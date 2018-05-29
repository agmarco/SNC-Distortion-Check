import logging
import zipfile
import uuid
import os
import tempfile
import dateutil.parser

import io
import time
from datetime import datetime
from urllib.parse import urlparse

import dicom
from dicom.dataset import Dataset, FileDataset
from dicom.UID import generate_uid

import numpy as np
from celery import shared_task
from celery.signals import task_failure
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.conf import settings
from django.db.models import F
from django.template import loader

from process import dicom_import, affine, fp_rejector, phantoms
from process.affine import apply_affine_1
from process.feature_detection import FeatureDetector
from process.registration import rigidly_register_and_categorize
from process.reports import generate_reports
from process.utils import fov_center_xyz
from process.interpolation import interpolate_distortion
import process.points_utils
from .dump_raw_scan_data import dump_raw_scan_data
from . import models
from .overlay_utilities import add_colorbar_to_slice
from process.exceptions import AlgorithmException

logger = logging.getLogger(__name__)


@shared_task(name='common.tasks.process_scan')
def process_scan(scan_pk, dicom_archive_url=None):
    '''
    Analyze an MRI or CT of a phantom (stored in a zip archive containing a set of DICOM
    files) and compare the location of the phantom's grid intersections to that
    of the currently set gold standard intersection locations, then generate a
    report.

    If `dicom_archive_url` is set, then this is a newly uploaded set of DICOM
    files, and the DICOM files need to be parsed and some metadata stored in
    the database.  If `dicom_archive_url` is `None`, then the scan is being
    "re-run"; in this case, we may be able to use some of the data that is
    already saved in the database.

    This task saves details periodically, so that in the event of a failure, we
    have as much data as possible available for debugging purposes.
    '''
    logger.info("Beginning processing of scan (pk={})".format(scan_pk))
    scan = models.Scan.objects.get(pk=scan_pk)

    try:
        if dicom_archive_url:
            _save_dicom_series(scan, dicom_archive_url)
        elif scan.dicom_series is None:
            raise AlgorithmException(
                f"Unable to run this scan because there are no DICOM files available; this may "
                f"mean that there was an issue uploading the DICOM files on the initial upload."
            )
        logger.info("Processing files stored at {}".format(scan.dicom_series.zipped_dicom_files.url))

        try:
            datasets = scan.dicom_series.unzip_datasets()
            dicom_meatadata_saved = scan.dicom_series.patient_id is None
            if not dicom_meatadata_saved:
                _save_dicom_series_metadata(scan.dicom_series, datasets)
            voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)
        except Exception as e:
            logger.exception(f'Exception occurred while extracting voxel data from the DICOM files')
            raise AlgorithmException(
                f"We were unable to extract the voxels from the uploaded zip-file. "
                f"Please be sure it is a zip-archive containing DICOM files for a single image series."
            )

        # delete the datasets to save memory; pydicom lazily loads the pixel
        # data from each slice, so after reading the voxel files from the
        # datasets, the datasets are much much larger; thus, although we need
        # them again later, we delete them and then reload to trade
        # processing time for peak memory usage
        # TODO: find a better way; perhaps dicom_import should handle this
        del datasets

        _save_detected_fiducials(scan, voxels, ijk_to_xyz)

        active_gold_standard = scan.golden_fiducials
        _, num_golden_fiducials = active_gold_standard.fiducials.fiducials.shape
        _, num_detected_fiducials = scan.detected_fiducials.fiducials.shape

        error_cutoff = 0.5
        if abs(num_detected_fiducials - num_golden_fiducials)/num_golden_fiducials > error_cutoff:
            raise AlgorithmException(
                f"Detected {num_detected_fiducials} grid intersections, but expected to find "
                f"{num_golden_fiducials}, according to {active_gold_standard.source_summary}. "
                f"Aborting analysis since the fractional error is larger than {error_cutoff*100:.1f}%. "
                f"Please be sure that it corresponds to the selected phantom."
            )

        isocenter_in_B = fov_center_xyz(voxels.shape, ijk_to_xyz)
        TPF = _save_registration_results(scan, isocenter_in_B)

        TPF_minimum = 0.80

        if TPF < TPF_minimum:
            phantom_model = scan.phantom.model.model_number
            grid_spacing = phantoms.paramaters[phantom_model]['grid_spacing']
            raise AlgorithmException(
                f"Only {TPF*100:.1f}% of the {num_golden_fiducials} gold standard points could "
                f"be matched to one of the {num_detected_fiducials} detected grid intersection locations.  This "
                f"is less than our minimum allowable {TPF_minimum*100:.1f}%, thus we aborted processing "
                f"the scan.  Please be sure to (1) orient the phantom within 5° of the expected orientation, "
                f"(2) the phantom's center is at most {3*grid_spacing:.1f} mm from the isocenter, (3) the "
                f"scanner's isocenter in the center of the field of view, (4) the pixel "
                f"size and slice spacing is sufficient to resolve the phantom grid intersections."
            )

        datasets = scan.dicom_series.unzip_datasets()
        _save_reports(scan, datasets, voxels, ijk_to_xyz)

    except AlgorithmException as e:
        scan = models.Scan.objects.get(pk=scan.pk)  # fresh instance
        logger.exception('Algorithm error')
        scan.errors = str(e)

    except Exception as e:
        scan = models.Scan.objects.get(pk=scan.pk)  # fresh instance
        creator_email = scan.creator.email
        logger.exception(f'Unhandled scan exception occurred while processing scan for "{creator_email}"')
        scan.errors = 'A server error occurred while processing the scan.'
    else:
        if scan.institution.scans_remaining is not None:
            scan.institution.scans_remaining = F('scans_remaining') - 1
            scan.institution.save()
    finally:
        raw_data_filename = 'raw_data.zip'
        raw_data = dump_raw_scan_data(scan)
        scan.raw_data.save(raw_data_filename, File(raw_data))

        scan.processing = False
        scan.save()
        logger.info('finished processing scan')


def _save_dicom_series(scan, dicom_archive_url):
    zipped_dicom_files = urlparse(dicom_archive_url).path
    dicom_series = models.DicomSeries(zipped_dicom_files=zipped_dicom_files)
    dicom_series.save()
    scan.dicom_series = dicom_series
    scan.save()


def _save_dicom_series_metadata(dicom_series, datasets):
    first_dataset = datasets[0]
    dicom_series.series_uid = first_dataset.SeriesInstanceUID
    dicom_series.study_uid = first_dataset.StudyInstanceUID
    dicom_series.frame_of_reference_uid = getattr(first_dataset, 'FrameOfReferenceUID', None)
    dicom_series.patient_id = getattr(first_dataset, 'PatientID', None)
    dicom_series.patient_name = getattr(first_dataset, 'PatientName', None)
    if getattr(first_dataset, 'PatientBirthDate', None):
        dicom_series.patient_birth_date = dateutil.parser.parse(
            first_dataset.PatientBirthDate).date()
    dicom_series.patient_sex = getattr(first_dataset, 'PatientSex', None)
    dicom_series.modality = getattr(first_dataset, 'Modality', None)
    dicom_series.acquisition_date = models.infer_acquisition_date(first_dataset)
    dicom_series.rows = getattr(first_dataset, 'Rows', None)
    dicom_series.columns = getattr(first_dataset, 'Columns', None)
    dicom_series.number_of_slices = getattr(first_dataset, 'NumberOfSlices', len(datasets))
    dicom_series.save()


def _save_detected_fiducials(scan, voxels, ijk_to_xyz):
    modality = scan.dicom_series.modality
    if modality == 'MR':
        modality_key = 'mri'
    elif modality in ['CT', 'SC']:
        modality_key = 'ct'
    else:
        raise ValueError('Modality must be either "MR", "CT", or "SC".')
    phantom_model = scan.phantom.model.model_number
    feature_detector = FeatureDetector(phantom_model, modality_key, voxels, ijk_to_xyz, limit_memory_usage=True)
    voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
    points_ijk = feature_detector.points_ijk
    pruned_points_ijk = fp_rejector.remove_fps(points_ijk, voxels, voxel_spacing, phantom_model)
    pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)
    scan.detected_fiducials = models.Fiducials.objects.create(fiducials=pruned_points_xyz)
    scan.save()


def _save_registration_results(scan, isocenter_in_B):
    phantom_model = scan.phantom.model.model_number
    grid_spacing = phantoms.paramaters[phantom_model]['grid_spacing']

    golden_fiducials = scan.golden_fiducials.fiducials.fiducials
    detected_fiducials = scan.detected_fiducials.fiducials

    _, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(golden_fiducials, detected_fiducials, grid_spacing, isocenter_in_B)
    scan.TP_A_S = models.Fiducials.objects.create(fiducials=TP_A_S)
    scan.TP_B = models.Fiducials.objects.create(fiducials=TP_B)

    TPF, FPF, FLE_percentiles = process.points_utils.metrics(FN_A_S, TP_A_S, TP_B, FP_B)
    logger.info(process.points_utils.format_point_metrics(TPF, FPF, FLE_percentiles))

    scan.save()

    return TPF


def _save_reports(scan, datasets, voxels, ijk_to_xyz):
    full_report_filename = 'full_report.pdf'
    executive_report_filename = 'executive_report.pdf'
    full_report_path = os.path.join(settings.BASE_DIR, 'tmp', full_report_filename)
    executive_report_path = os.path.join(settings.BASE_DIR, 'tmp', executive_report_filename)

    generate_reports(
        scan.TP_A_S.fiducials,
        scan.TP_B.fiducials,
        datasets,
        voxels,
        ijk_to_xyz,
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

    scan.save()


CT_WARNING_THRESHOLD = 0.05

@shared_task(name='common.tasks.process_ct_upload')
def process_ct_upload(gold_standard_pk, dicom_archive_url=None):
    logger.info("Beginning processing of CT for golden standard (pk={})".format(gold_standard_pk))
    gold_standard = models.GoldenFiducials.objects.get(pk=gold_standard_pk)

    try:
        if dicom_archive_url:
            dicom_series = models.DicomSeries(zipped_dicom_files=urlparse(dicom_archive_url).path)
            dicom_series.save()
            gold_standard.dicom_series = dicom_series
            gold_standard.save()

            with zipfile.ZipFile(dicom_series.zipped_dicom_files, 'r') as zip_file:
                datasets = dicom_import.dicom_datasets_from_zip(zip_file)
            _save_dicom_series_metadata(dicom_series, datasets)
        else:
            dicom_series = gold_standard.dicom_series
            with zipfile.ZipFile(dicom_series.zipped_dicom_files, 'r') as zip_file:
                datasets = dicom_import.dicom_datasets_from_zip(zip_file)
        logger.info("Processing files stored at {}".format(dicom_series.zipped_dicom_files.url))

        voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)
        del datasets

        modality = 'ct'
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
        phantom_model = gold_standard.phantom.model.model_number
        feature_detector = FeatureDetector(phantom_model, modality, voxels, ijk_to_xyz, limit_memory_usage=True)
        points_ijk = feature_detector.points_ijk
        pruned_points_ijk = fp_rejector.remove_fps(points_ijk, voxels, voxel_spacing, phantom_model)
        pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

        cad_fiducials = gold_standard.phantom.model.cad_fiducials.fiducials

        grid_spacing = phantoms.paramaters[phantom_model]['grid_spacing']

        isocenter_in_B = fov_center_xyz(voxels.shape, ijk_to_xyz)
        xyztpx_a_to_b, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                cad_fiducials, pruned_points_xyz, grid_spacing, isocenter_in_B)

        TPF, FPF, FLE_percentiles = process.points_utils.metrics(FN_A_S, TP_A_S, TP_B, FP_B)
        logger.info(process.points_utils.format_point_metrics(TPF, FPF, FLE_percentiles))

        ct_fiducials = TP_B

        # We want to keep the gold standard points aligned with the original
        # CAD model (where-in the center of the model is at (0, 0, 0)).  Since
        # our registration function returns the translation and rotation
        # necessary to shift the CAD to the CT, we must invert the shift and
        # apply it to move the CT points back to the CAD's coordinate system.
        a_to_b = affine.rotation_translation(*xyztpx_a_to_b)
        b_to_a = np.linalg.inv(a_to_b)
        ct_fiducials_aligned_with_cad = affine.apply_affine(b_to_a, ct_fiducials)

        gold_standard.fiducials = models.Fiducials.objects.create(fiducials=ct_fiducials_aligned_with_cad)

        _raise_if_fiducials_too_different_from_cad(ct_fiducials_aligned_with_cad, cad_fiducials)

    except AlgorithmException as e:
        gold_standard = models.GoldenFiducials.objects.get(pk=gold_standard_pk)  # fresh instance
        logger.exception('Algorithm error')
        gold_standard.errors = str(e)

    except Exception as e:
        gold_standard = models.GoldenFiducials.objects.get(pk=gold_standard_pk)  # fresh instance
        logger.exception(f'Unhandled scan exception occurred while processing gold standard.')
        gold_standard.errors = 'A server error occurred while processing the gold standard.'

    finally:
        gold_standard.processing = False
        gold_standard.save()
        logger.info('finished processing gold standard')


def _raise_if_fiducials_too_different_from_cad(ct_fiducials, cad_fiducials):
    _, num_cad_fiducials = cad_fiducials.shape
    _, num_ct_fiducials = ct_fiducials.shape

    error_threshold = 0.5
    fractional_difference = abs(num_ct_fiducials - num_cad_fiducials) / num_cad_fiducials
    if fractional_difference > CT_WARNING_THRESHOLD:
        msg = 'There was an error processing the CT upload, and too many or too few points were detected ' + \
              f'({num_ct_fiducials} in the upload, vs {num_cad_fiducials} in the CAD model).' + \
              'Thus, the points can not be used.'
        logger.error(msg)
        if fractional_difference > error_threshold:
            raise AlgorithmException(msg)


@task_failure.connect
def task_failure_handler(task_id=None, exception=None, args=None, **kwargs):
    logging.info("{} {} {}".format(task_id, str(exception), str(args)))


# TODO: figure out how to avoid passing in domain, site_name, and use_https
@shared_task(name='common.tasks.process_dicom_overlay')
def process_dicom_overlay(scan_pk, study_instance_uid, frame_of_reference_uid, patient_id, user_email,
            domain, site_name, use_https):
    try:
        with transaction.atomic():
            GRID_DENSITY_mm = 1.5

            scan = models.Scan.objects.get(pk=scan_pk)
            dicom_series = scan.dicom_series
            TP_A_S = scan.TP_A_S.fiducials
            error_mags = scan.error_mags

            overlay_ijk_to_xyz, interpolated_error_mags = interpolate_distortion(TP_A_S, error_mags, GRID_DENSITY_mm)

            output_dir = tempfile.mkdtemp()
            logger.info("Exporting overlay to dicoms")
            export_overlay(
                voxel_array=interpolated_error_mags,
                voxelSpacing_tup=(GRID_DENSITY_mm, GRID_DENSITY_mm, GRID_DENSITY_mm),
                voxelPosition_tup=apply_affine_1(overlay_ijk_to_xyz, np.zeros((3,))),
                studyInstanceUID=study_instance_uid or dicom_series.study_uid,
                seriesInstanceUID=generate_uid(),
                frameOfReferenceUID=frame_of_reference_uid or dicom_series.frame_of_reference_uid,
                patientID=patient_id or dicom_series.patient_id,
                output_directory=output_dir,
                imageOrientationPatient=np.array([1, 0, 0, 0, 1, 0]),
            )
            logger.info("Done exporting overlay")
            zip_bytes = io.BytesIO()
            num_files = 0
            with zipfile.ZipFile(zip_bytes, 'w', zipfile.ZIP_DEFLATED) as zf:
                for dirname, subdirs, files in os.walk(output_dir):
                    zf.write(dirname)
                    for filename in files:
                        num_files += 1
                        zf.write(os.path.join(dirname, filename), arcname=filename)
            logger.info("Done zipping %d generated dicom files to temp folder", num_files)

            zip_filename = f'overlay/{uuid.uuid4()}/overlay.zip'
            default_storage.save(zip_filename, zip_bytes)
            logger.info("Done saving temporary file to online storage")

            subject_template_name = 'common/email/dicom_overlay_subject.txt'
            email_template_name = 'common/email/dicom_overlay_email.txt'
            html_email_template_name = 'common/email/dicom_overlay_email.html'
            from_email = None
            to_email = user_email
            protocol = 'https' if use_https else 'http'
            expires_in_days = 30
            zip_url_or_path = default_storage.url(zip_filename)
            zip_url = f'{protocol}://{domain}{zip_url_or_path}' if zip_url_or_path[0] == '/' else zip_url_or_path
            context = {
                'zip_url': zip_url,
                'site_name': site_name,
                'expires_in_days': expires_in_days,
            }
            logger.info("Emailing overlay (%s) to %s", zip_url, to_email)
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
            frameOfReferenceUID, patientID, output_directory, imageOrientationPatient):
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

    def _base_dataset():
        sopinst = generate_uid()
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'  # Implicit VR Little Endian
        file_meta.MediaStorageSOPInstanceUID = sopinst
        file_meta.ImplementationClassUID = '1.1.1'
        dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0"*128)
        dataset.SOPInstanceUID = sopinst
        dataset.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image SOP Class
        return dataset

    def _unstack(voxel_array):
        '''converts array of x,y,z into one of z,x,y to make it easier to slice.'''
        return voxel_array.transpose(2, 0, 1)

    if len(voxel_array.shape) != 3:
        msg = 'Only 3d arrays are supported for dicom export, got shape {}'
        raise Exception(msg.format(voxel_array.shape))

    rescaleSlope, rescaleIntercept, rescaled_voxel_array = _rescale_to_stored_values(voxel_array)
    slices_array = _unstack(rescaled_voxel_array)
    for slice_num, slice_arr in enumerate(slices_array):
        add_colorbar_to_slice(slice_arr, np.max(slice_arr))

        sliceVoxelPosition = (voxelPosition_tup[0],
                              voxelPosition_tup[1],
                              voxelPosition_tup[2] + voxelSpacing_tup[2]*slice_num)
        dataset = _base_dataset()
        # Patient Module
        dataset.PatientName = ''
        dataset.PatientID = patientID

        # general study module
        dataset.ContentDate = str(datetime.today()).replace('-', '')
        dataset.ContentTime = str(time.time())
        dataset.StudyInstanceUID = studyInstanceUID
        dataset.StudyDescription = 'Distortion Overlay'

        # general series module
        dataset.SeriesInstanceUID = seriesInstanceUID
        dataset.Modality = 'PT'

        # Frame of reference module
        dataset.FrameOfReferenceUID = frameOfReferenceUID

        # Image plane module
        xSpacing_mm, ySpacing_mm, zSpacing_mm = voxelSpacing_tup
        dataset.ImageOrientationPatient = _encode_multival(imageOrientationPatient)  # direction cosines
        dataset.ImagePositionPatient = _encode_multival(sliceVoxelPosition)
        dataset.PixelSpacing = _encode_multival([xSpacing_mm, ySpacing_mm])
        dataset.SliceThickness = str(zSpacing_mm)
        dataset.InstanceNumber = slice_num

        # image pixel module
        columns, rows = slice_arr.shape
        dataset.SamplesPerPixel = 1
        dataset.PhotometricInterpretation = "MONOCHROME2"
        dataset.PixelRepresentation = 0  # unsigned int
        dataset.HighBit = 15
        dataset.BitsStored = 16
        dataset.BitsAllocated = 16
        dataset.Columns = columns
        dataset.Rows = rows
        dataset.NumberOfFrames = 1
        dataset.RescaleIntercept = rescaleIntercept
        dataset.RescaleSlope = rescaleSlope

        # TODO: Fix incorrect transpositions upstream; also swap back rows and columns
        dataset.PixelData = slice_arr.astype(np.uint16).T.tobytes()
        dataset.Units = 'mm'
        dicom.write_file(os.path.join(output_directory, '{}.dcm'.format(dataset.SOPInstanceUID)), dataset)
