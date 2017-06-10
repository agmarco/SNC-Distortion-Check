import logging
import zipfile
import uuid
import os
import tempfile
import io
import time
from datetime import datetime
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
from scipy.interpolate.ndgriddata import griddata

from process import dicom_import, affine, fp_rejector
from process.affine import apply_affine
from process.feature_detection import FeatureDetector
from process.file_io import save_voxels
from process.registration import rigidly_register_and_categorize
from process.reports import generate_reports
from process.utils import fov_center_xyz
from . import serializers
from .models import Scan, Fiducials, GoldenFiducials, DicomSeries

logger = logging.getLogger(__name__)


class AlgorithmException(Exception):
    '''
    The algorithm's results failed in a way that indicates it can not handle
    the data set.
    '''
    pass


@shared_task
def process_scan(scan_pk):
    scan = Scan.objects.get(pk=scan_pk)

    try:
        with transaction.atomic():
            modality = 'mri'
            phantom_model = scan.phantom.model.model_number

            # TODO: save condensed DICOM tags onto `dicom_series` on upload so
            # we don't need to load all the zip files just to get at the
            # metadata; this should be a feature of dicom-numpy
            dicom_archive = scan.dicom_series.zipped_dicom_files

            with zipfile.ZipFile(dicom_archive, 'r') as zip_file:
                datasets = dicom_import.dicom_datasets_from_zip(zip_file)

            voxels = scan.dicom_series.voxels
            ijk_to_xyz = scan.dicom_series.ijk_to_xyz
            voxel_spacing = affine.voxel_spacing(ijk_to_xyz)

            feature_detector = FeatureDetector(
                phantom_model,
                modality,
                voxels,
                ijk_to_xyz,
            )

            pruned_points_ijk = fp_rejector.remove_fps(feature_detector.points_ijk, voxels, voxel_spacing, phantom_model)
            pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

            scan.detected_fiducials = Fiducials.objects.create(fiducials=pruned_points_xyz)

            isocenter_in_B = fov_center_xyz(voxels.shape, ijk_to_xyz)

            xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                scan.golden_fiducials.fiducials.fiducials,
                scan.detected_fiducials.fiducials,
                isocenter_in_B,
            )

            if TP_B.size == 0:
                # TODO: add more satisfying error message
                raise AlgorithmException("No fiducials could be matched with the gold standard.")

            scan.TP_A_S = Fiducials.objects.create(fiducials=TP_A_S)
            scan.TP_B = Fiducials.objects.create(fiducials=TP_B)

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
        scan = Scan.objects.get(pk=scan_pk)  # fresh instance

        logger.exception('Algorithm error')
        scan.errors = str(e)

    except Exception as e:
        scan = Scan.objects.get(pk=scan_pk)  # fresh instance

        creator_email = scan.creator.email
        logger.exception(f'Unhandled scan exception occurred while processing scan for "{creator_email}"')
        scan.errors = f'''
            A server error occurred while processing the scan.  CIRS has been
            notified of the issue and is taking steps to resolve the issue.  We
            will notify you at "{creator_email}" when the exception has been
            resolved.
        '''
    finally:
        scan.processing = False
        scan.save()
        logger.info('finished processing scan')


@shared_task
def process_ct_upload(dicom_series_pk, gold_standard_pk):
    try:
        with transaction.atomic():
            modality = 'ct'
            dicom_series = DicomSeries.objects.get(pk=dicom_series_pk)
            gold_standard = GoldenFiducials.objects.get(pk=gold_standard_pk)

            feature_detector = FeatureDetector(
                gold_standard.phantom.model.model_number,
                modality,
                dicom_series.voxels,
                dicom_series.ijk_to_xyz
            )

            fiducials = Fiducials.objects.create(fiducials=feature_detector.points_xyz)
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
        zf.writestr('dicom.zip', scan.dicom_series.zipped_dicom_files.read())

        for zip_path, path in files.items():
            zf.write(path, zip_path)

        for zip_path, stream in streams.items():
            zf.writestr(zip_path, stream.getvalue())

    return s


@shared_task
def process_dicom_overlay(scan_pk, study_instance_uid, frame_of_reference_uid, patient_id, user_email, domain, use_https):
    try:
        with transaction.atomic():
            # TODO: Consolidate and split out these constants in the process module.
            GRID_DENSITY_mm = 1
            DISTORTION_SCALE = 1000
            BLUR_SIGMA = 2

            scan = Scan.objects.get(pk=scan_pk)
            ds = scan.dicom_series
            ijk_to_xyz = ds.ijk_to_xyz
            coord_min_xyz, coord_max_xyz = apply_affine(ijk_to_xyz, np.array([(0.0, 0.0, 0.0), ds.shape]).T).T
            TP_A = scan.TP_A_S.fiducials
            error_mags = scan.error_mags
            grid_x, grid_y, grid_z = np.meshgrid(np.arange(coord_min_xyz[0], coord_max_xyz[0], GRID_DENSITY_mm),
                                                 np.arange(coord_min_xyz[1], coord_max_xyz[1], GRID_DENSITY_mm),
                                                 np.arange(coord_min_xyz[2], coord_max_xyz[2], GRID_DENSITY_mm))
            logger.info("Gridding data for overlay generation.")
            gridded = griddata(TP_A.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
            gridded *= DISTORTION_SCALE  # rescale so it looks a bit better
            gridded = scipy.ndimage.filters.gaussian_filter(gridded, BLUR_SIGMA,
                                                            truncate=2)  # TODO: remove this once we fix interpolation
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
            context = {
                'zip': os.path.join(settings.MEDIA_URL, zip_filename),
                'protocol': 'https' if use_https else 'http',
                'domain': domain,
            }
            send_mail(subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name)
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


def export_overlay(voxel_array, voxelSpacing_tup, voxelPosition_tup, studyInstanceUID, seriesInstanceUID, frameOfReferenceUID, patientID, output_directory):
    '''
    Exports a voxel array to a series of dicom files.

    :param voxel_array: voxels array in x,y,z axis order.
    :param voxelSpacing_tup: spacing in mm
    :param voxelPosition_tup: position of first voxel in mm in patient coordinate system
    :param studyInstanceUID:
    :param seriesInstanceUID:
    :param frameOfReferenceUID:
    :param patientID:
    :param output_directory: directory to dump the dicoms in
    :return:
    '''
    def _encode_multival(values):
        '''
        Encodes a collection of multivalued elements in backslash separated syntax known by dicom spec.
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
        raise Exception('Only 3d arrays are supported for dicom export, got shape {}'.format(voxel_array.shape))

    slices_array = _unstack(voxel_array)
    for slice_num, slice_arr in enumerate(slices_array):
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
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 0.01
        ds.PixelData = slice_arr.astype(np.uint16).tobytes()
        dicom.write_file(os.path.join(output_directory, '{}.dcm'.format(ds.SOPInstanceUID)), ds)
