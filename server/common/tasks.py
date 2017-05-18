import logging
import zipfile
import uuid
import os
import io

import scipy.io
from celery import shared_task
from celery.signals import task_failure
from django.core.files import File
from django.db import transaction
from django.conf import settings
from rest_framework.renderers import JSONRenderer

from process import dicom_import, affine, fp_rejector
from process.feature_detection import FeatureDetector
from process.file_io import save_voxels
from process.registration import rigidly_register_and_categorize
from process.reports import generate_reports
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

            xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                scan.golden_fiducials.fiducials.fiducials,
                scan.detected_fiducials.fiducials,
            )

            if TP_B.size == 0:
                # TODO: add more satisfying error message
                raise AlgorithmException("No fiducials could be matched with the gold standard.")

            scan.TP_A_S = Fiducials.objects.create(fiducials=TP_A_S)
            scan.TP_B = Fiducials.objects.create(fiducials=TP_B)

            # TODO: come up with better filename
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
        'dicom.zip': scan.dicom_series.zipped_dicom_files.path,
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
        for zip_path, path in files.items():
            zf.write(path, zip_path)

        for zip_path, stream in streams.items():
            zf.writestr(zip_path, stream.getvalue())

    return s
