import logging
import zipfile
import uuid
import os
import tempfile

import io
import time
from datetime import datetime
from urllib.parse import urlparse

import dicom
from dicom.dataset import Dataset, FileDataset
from dicom.UID import generate_uid

import numpy as np
import scipy.io
import scipy.ndimage.filters
from celery import shared_task
from celery.signals import task_failure
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.conf import settings
from django.template import loader
from rest_framework.renderers import JSONRenderer
from naturalneighbor import griddata
from PIL import Image, ImageDraw, ImageFont

from process import dicom_import, affine, fp_rejector, phantoms
from process.affine import apply_affine
from process.feature_detection import FeatureDetector
from process.file_io import save_voxels
from process.registration import rigidly_register_and_categorize
from process.reports import generate_reports
from process.utils import fov_center_xyz
from process.points_utils import format_point_metrics, metrics
from . import serializers
from .import models
from .overlay_utilities import add_colorbar_to_slice
from process.exceptions import AlgorithmException

logger = logging.getLogger(__name__)


@shared_task
def process_scan(scan_pk, dicom_archive_url=None):
    scan = models.Scan.objects.get(pk=scan_pk)

    try:
        with transaction.atomic():
            modality = 'mri'
            phantom_model = scan.phantom.model.model_number
            phantom_paramaters = phantoms.paramaters[phantom_model]
            active_gold_standard = scan.phantom.active_gold_standard
            _, num_golden_fiducials = active_gold_standard.fiducials.fiducials.shape

            if dicom_archive_url:
                zipped_dicom_files = urlparse(dicom_archive_url).path
                dicom_series = models.DicomSeries(zipped_dicom_files=zipped_dicom_files)

                # TODO: save condensed DICOM tags onto `dicom_series` on upload so
                # we don't need to load all the zip files just to get at the
                # metadata; this should be a feature of dicom-numpy
                dicom_archive = dicom_series.zipped_dicom_files

                with zipfile.ZipFile(dicom_archive, 'r') as dicom_archive_zipfile:
                    datasets = dicom_import.dicom_datasets_from_zip(dicom_archive_zipfile)

                voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)
                ds = datasets[0]

                dicom_series.voxels = voxels
                dicom_series.ijk_to_xyz = ijk_to_xyz
                dicom_series.shape = voxels.shape
                dicom_series.series_uid = ds.SeriesInstanceUID
                dicom_series.study_uid = ds.StudyInstanceUID
                dicom_series.frame_of_reference_uid = ds.FrameOfReferenceUID
                dicom_series.patient_id = ds.PatientID
                dicom_series.acquisition_date = models.infer_acquisition_date(ds)

                dicom_series.save()
                scan.dicom_series = dicom_series
            else:
                with zipfile.ZipFile(scan.dicom_series.zipped_dicom_files, 'r') as zf:
                    datasets = dicom_import.dicom_datasets_from_zip(zf)

            voxels = scan.dicom_series.voxels
            ijk_to_xyz = scan.dicom_series.ijk_to_xyz
            voxel_spacing = affine.voxel_spacing(ijk_to_xyz)

            feature_detector = FeatureDetector(
                phantom_model,
                modality,
                voxels,
                ijk_to_xyz,
            )

            pruned_points_ijk = fp_rejector.remove_fps(
                feature_detector.points_ijk,
                voxels,
                voxel_spacing,
                phantom_model,
            )
            pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

            scan.detected_fiducials = models.Fiducials.objects.create(fiducials=pruned_points_xyz)

            _, num_fiducials = pruned_points_xyz.shape
            error_cutoff = 0.5
            if abs(num_fiducials - num_golden_fiducials)/num_golden_fiducials > error_cutoff:
                raise AlgorithmException(
                    f"Detected {num_fiducials} grid intersections, but expected to find "
                    f"{num_golden_fiducials}, according to {active_gold_standard.source_summary}. "
                    f"Aborting analysis since the fractional error is larger than {error_cutoff*100:.1f}%."
                )

            isocenter_in_B = fov_center_xyz(voxels.shape, ijk_to_xyz)

            xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                scan.golden_fiducials.fiducials.fiducials,
                scan.detected_fiducials.fiducials,
                isocenter_in_B,
                phantom_paramaters['brute_search_slices'],
            )

            TPF, FPF, FLE_percentiles = metrics(FN_A_S, TP_A_S, TP_B, FP_B)
            logger.info(format_point_metrics(TPF, FPF, FLE_percentiles))

            TPF_minimum = 0.85

            if TPF < TPF_minimum:
                raise AlgorithmException(
                    f"Only {TPF*100:.1f}% of the {num_golden_fiducials} gold standard points could "
                    f"be matched to one of the {num_fiducials} detected grid intersection locations.  This "
                    f"is less than our minimum allowable {TPF_minimum*100:.1f}%, thus we aborted processing "
                    f"the scan.  Please be sure to (1) orient the phantom correctly with 4° along each axis, "
                    f"(2) position the phantom's center within 5mm of the isocenter, (3) position the "
                    f"scanner's isocenter in the exact center of the field of view, (4) ensure the pixel "
                    f"size and slice spacing is sufficient to resolve the grid intersections.  If you believe"
                    f"none of these scenarios can explain the failure, please let CIRS support know about "
                    f"the issue."
                )

            scan.TP_A_S = models.Fiducials.objects.create(fiducials=TP_A_S)
            scan.TP_B = models.Fiducials.objects.create(fiducials=TP_B)

            full_report_filename = 'full_report.pdf'
            executive_report_filename = 'executive_report.pdf'
            full_report_path = os.path.join(settings.BASE_DIR, 'tmp', full_report_filename)
            executive_report_path = os.path.join(settings.BASE_DIR, 'tmp', executive_report_filename)

            generate_reports(
                TP_A_S,
                TP_B,
                datasets,
                scan.dicom_series.voxels,
                scan.dicom_series.ijk_to_xyz,
                scan.golden_fiducials.phantom.model.model_number,
                scan.tolerance,
                scan.institution,
                scan.machine_sequence_pair.machine.name,
                scan.machine_sequence_pair.sequence.name,
                scan.golden_fiducials.phantom.name,
                scan.dicom_series.acquisition_date,
                full_report_path,
                executive_report_path,
            )

            with open(full_report_path, 'rb') as report_file:
                scan.full_report.save(full_report_filename, File(report_file))

            with open(executive_report_path, 'rb') as report_file:
                scan.executive_report.save(executive_report_filename, File(report_file))

            raw_data_filename = 'raw_data.zip'
            raw_data = dump_raw_data(scan)
            scan.raw_data.save(raw_data_filename, File(raw_data))

    except AlgorithmException as e:
        scan = models.Scan.objects.get(pk=scan.pk)  # fresh instance
        logger.exception('Algorithm error')
        scan.errors = str(e)

    except Exception as e:
        scan = models.Scan.objects.get(pk=scan.pk)  # fresh instance

        creator_email = scan.creator.email
        logger.exception(f'Unhandled scan exception occurred while processing scan for "{creator_email}"')
        scan.errors = 'A server error occurred while processing the scan.'
    finally:
        scan.processing = False
        scan.save()
        logger.info('finished processing scan')


@shared_task
def process_ct_upload(gold_standard_pk, dicom_archive_url):
    try:
        with transaction.atomic():
            modality = 'ct'

            gold_standard = models.GoldenFiducials.objects.get(pk=gold_standard_pk)

            dicom_series = models.DicomSeries(zipped_dicom_files=urlparse(dicom_archive_url).path)

            with zipfile.ZipFile(dicom_series.zipped_dicom_files, 'r') as zip_file:
                datasets = dicom_import.dicom_datasets_from_zip(zip_file)

            voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)
            ds = datasets[0]

            dicom_series.voxels = voxels
            dicom_series.ijk_to_xyz = ijk_to_xyz
            dicom_series.shape = voxels.shape
            dicom_series.series_uid = ds.SeriesInstanceUID
            dicom_series.study_uid = ds.StudyInstanceUID
            dicom_series.patient_id = ds.PatientID
            dicom_series.acquisition_date = models.infer_acquisition_date(ds)
            dicom_series.frame_of_reference_uid = getattr(ds, 'FrameOfReferenceUID', None)

            dicom_series.save()
            gold_standard.dicom_series = dicom_series

            feature_detector = FeatureDetector(
                gold_standard.phantom.model.model_number,
                modality,
                dicom_series.voxels,
                dicom_series.ijk_to_xyz
            )

            # TODO: apply the FP rejector to this stage

            fiducials = models.Fiducials.objects.create(fiducials=feature_detector.points_xyz)
            gold_standard.fiducials = fiducials
            gold_standard.processing = False
            gold_standard.save()
    except Exception as e:
        raise e


@task_failure.connect
def task_failure_handler(task_id=None, exception=None, args=None, **kwargs):
    logging.info("{} {} {}".format(task_id, str(exception), str(args)))


def dump_raw_data(scan):
    voxels_path = os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}.mat')
    voxels_data = {
        'phantom_model': scan.phantom.model.model_number,
        'modality': 'mri',
        'voxels': scan.dicom_series.voxels,
    }
    save_voxels(voxels_path, voxels_data)

    raw_points_path = os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}.mat')
    raw_points_data = {
        'all': scan.detected_fiducials.fiducials,
        'TP': scan.TP_B.fiducials,
    }
    scipy.io.savemat(raw_points_path, raw_points_data)

    renderer = JSONRenderer()

    phantom = serializers.PhantomSerializer(scan.phantom)
    phantom_s = io.BytesIO()
    phantom_s.write(renderer.render(phantom.data))

    machine = serializers.MachineSerializer(scan.machine_sequence_pair.machine)
    machine_s = io.BytesIO()
    machine_s.write(renderer.render(machine.data))

    sequence = serializers.SequenceSerializer(scan.machine_sequence_pair.sequence)
    sequence_s = io.BytesIO()
    sequence_s.write(renderer.render(sequence.data))

    institution = serializers.InstitutionSerializer(scan.institution)
    institution_s = io.BytesIO()
    institution_s.write(renderer.render(institution.data))

    files = {
        'voxels.mat': voxels_path,
        'raw_points.mat': raw_points_path,
    }

    streams = {
        'phantom.json': phantom_s,
        'machine.json': machine_s,
        'sequence.json': sequence_s,
        'institution.json': institution_s,
    }

    s = io.BytesIO()
    with zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED) as zf:
        zipped_dicom_files = scan.dicom_series.zipped_dicom_files
        zipped_dicom_files.seek(0)  # rewind the file, as it may have been read earlier
        zf.writestr('dicom.zip', zipped_dicom_files.read())

        for zip_path, path in files.items():
            zf.write(path, zip_path)

        for zip_path, stream in streams.items():
            zf.writestr(zip_path, stream.getvalue())

    return s


@shared_task
def process_dicom_overlay(scan_pk, study_instance_uid, frame_of_reference_uid, patient_id, user_email,
            domain, site_name, use_https):
    try:
        with transaction.atomic():
            # TODO: Consolidate and split out these constants in the process module.
            GRID_DENSITY_mm = 2.0

            scan = models.Scan.objects.get(pk=scan_pk)
            ds = scan.dicom_series
            ijk_to_xyz = ds.ijk_to_xyz
            coord_min_xyz, coord_max_xyz = apply_affine(ijk_to_xyz, np.array([(0.0, 0.0, 0.0), ds.shape]).T).T
            TP_A = scan.TP_A_S.fiducials
            error_mags = scan.error_mags
            interp_grid_ranges = [
                [coord_min_xyz[0], coord_max_xyz[0], GRID_DENSITY_mm],
                [coord_min_xyz[1], coord_max_xyz[1], GRID_DENSITY_mm],
                [coord_min_xyz[2], coord_max_xyz[2], GRID_DENSITY_mm],
            ]
            logger.info("Gridding data for overlay generation.")

            gridded = griddata(TP_A.T, error_mags.T, interp_grid_ranges)
            gridded[np.isnan(gridded)] = 0
            output_dir = tempfile.mkdtemp()
            logger.info("Exporting overlay to dicoms.")
            export_overlay(
                voxel_array=gridded,
                voxelSpacing_tup=(GRID_DENSITY_mm, GRID_DENSITY_mm, GRID_DENSITY_mm),
                voxelPosition_tup=coord_min_xyz,
                studyInstanceUID=study_instance_uid or ds.study_uid,
                seriesInstanceUID=generate_uid(),
                frameOfReferenceUID=frame_of_reference_uid or ds.frame_of_reference_uid,
                patientID=patient_id or ds.patient_id,
                output_directory=output_dir
            )
            zip_bytes = io.BytesIO()
            with zipfile.ZipFile(zip_bytes, 'w', zipfile.ZIP_DEFLATED) as zf:
                for dirname, subdirs, files in os.walk(output_dir):
                    zf.write(dirname)
                    for filename in files:
                        zf.write(os.path.join(dirname, filename), arcname=filename)
            logger.info("done zipping generated dicoms.")

            zip_filename = f'overlay/{uuid.uuid4()}/overlay.zip'
            default_storage.save(zip_filename, zip_bytes)

            subject_template_name = 'common/email/dicom_overlay_subject.txt'
            email_template_name = 'common/email/dicom_overlay_email.txt'
            html_email_template_name = 'common/email/dicom_overlay_email.html'
            from_email = None
            to_email = user_email
            protocol = 'https' if use_https else 'http'
            expires_in_days = 30
            expires_in_seconds = 60*60*24*expires_in_days
            zip_url = default_storage.url(zip_filename, expire=expires_in_seconds)
            context = {
                'zip_url': f'{protocol}://{domain}{zip_url}' if zip_url[0] == '/' else zip_url,
                'site_name': site_name,
                'expires_in_days': expires_in_days,
            }
            send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                to_email,
                html_email_template_name
            )
    except Exception as e:
        raise e


def send_mail(subject_template_name, email_template_name,
              context, from_email, to_email, html_email_template_name=None):
    """
    Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')

    email_message.send()

# TODO: convert to class for easier unit testing
def export_overlay(voxel_array, voxelSpacing_tup, voxelPosition_tup, studyInstanceUID, seriesInstanceUID,
            frameOfReferenceUID, patientID, output_directory):
    '''
    Exports a voxel array to a series of dicom files.

    :param voxel_array: voxels array in x,y,z axis order. Units should be in mm.
    :param voxelSpacing_tup: spacing in mm
    :param voxelPosition_tup: position of first voxel in mm in patient coordinate system
    :param studyInstanceUID:
    :param seriesInstanceUID:
    :param frameOfReferenceUID:
    :param patientID:
    :param output_directory: directory to dump the dicoms in
    :return:
    '''

    def _rescale_to_stored_values(pixel_array):
        '''
        Rescales the provided pixel array values from output units to storage
        units such that the dynamic range for 16 bit image is maximized.
        '''
        rescaleIntercept, max_val = np.min(pixel_array), np.max(pixel_array)
        rescaleSlope = (max_val - rescaleIntercept) / np.iinfo(np.uint16).max
        scaled_pixel_array = (pixel_array - rescaleIntercept) / (rescaleSlope or 1)
        stored_value_array = scaled_pixel_array.astype(np.uint16)
        return rescaleSlope, rescaleIntercept, stored_value_array

    def _encode_multival(values):
        '''
        Encodes a collection of multivalued elements in backslash separated
        syntax known by dicom spec.
        '''
        return '\\'.join(str(val) for val in values)

    def _base_ds():
        sopinst = generate_uid()
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'  # Implicit VR Little Endian
        file_meta.MediaStorageSOPInstanceUID = sopinst
        file_meta.ImplementationClassUID = '1.1.1'
        ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0"*128)
        ds.SOPInstanceUID = sopinst
        ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image SOP Class
        return ds

    def _unstack(voxel_array):
        '''converts array of x,y,z into one of z,x,y to make it easier to slice.'''
        return voxel_array.transpose(2, 0, 1)

    if len(voxel_array.shape) != 3:
        msg = 'Only 3d arrays are supported for dicom export, got shape {}'
        raise Exception(msg.format(voxel_array.shape))
    rescaleSlope, rescaleIntercept, rescaled_voxel_array = _rescale_to_stored_values(voxel_array)
    slices_array = _unstack(rescaled_voxel_array)
    for slice_num, slice_arr in enumerate(slices_array):
        slice_arr = add_colorbar_to_slice(slice_arr, np.max(voxel_array[slice_num]))

        sliceVoxelPosition = (voxelPosition_tup[0],
                              voxelPosition_tup[1],
                              voxelPosition_tup[2] + voxelSpacing_tup[2]*slice_num)
        ds = _base_ds()
        # Patient Module
        ds.PatientName = ''
        ds.PatientID = patientID

        # general study module
        ds.ContentDate = str(datetime.today()).replace('-','')
        ds.ContentTime = str(time.time())
        ds.StudyInstanceUID = studyInstanceUID
        ds.StudyDescription = 'Distortion Overlay'

        # general series module
        ds.SeriesInstanceUID = seriesInstanceUID
        ds.Modality = 'PT'

        # Frame of reference module
        ds.FrameOfReferenceUID = frameOfReferenceUID

        # Image plane module
        xSpacing_mm, ySpacing_mm, zSpacing_mm = voxelSpacing_tup
        ds.ImageOrientationPatient = _encode_multival([1, 0, 0, 0, 1, 0])  # direction cosines
        ds.ImagePositionPatient = _encode_multival(sliceVoxelPosition)
        ds.PixelSpacing = _encode_multival([xSpacing_mm, ySpacing_mm])
        ds.SliceThickness = str(zSpacing_mm)
        ds.InstanceNumber = slice_num

        # image pixel module
        rows, columns = slice_arr.shape
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation = 0  # unsigned int
        ds.HighBit = 15
        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.Columns = columns
        ds.Rows = rows
        ds.NumberOfFrames = 1
        ds.RescaleIntercept = rescaleIntercept
        ds.RescaleSlope = rescaleSlope
        ds.PixelData = slice_arr.astype(np.uint16).tobytes()
        ds.Units = 'mm'
        dicom.write_file(os.path.join(output_directory, '{}.dcm'.format(ds.SOPInstanceUID)), ds)
