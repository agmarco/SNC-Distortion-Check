import logging
import zipfile
import uuid
import os

import numpy as np
from celery import shared_task
from celery.signals import task_failure
from django.core.files import File
from django.db import transaction
from django.conf import settings

from process import dicom_import, affine, phantoms, fp_rejector
from process.feature_detection import FeatureDetector
from process.registration import rigidly_register_and_categorize
from process.reports import generate_report, generate_cube

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
                scan.phantom.model.model_number,
                modality,
                voxels,
                ijk_to_xyz,
            )

            pruned_points_ijk = fp_rejector.remove_fps(feature_detector.points_ijk, voxels, voxel_spacing)
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
            report_filename = f'{uuid.uuid4()}.pdf'
            report_path = os.path.join(settings.BASE_DIR, 'tmp', report_filename)

            generate_report(
                TP_A_S,
                TP_B,
                datasets,
                scan.dicom_series.voxels,
                scan.dicom_series.ijk_to_xyz,
                scan.golden_fiducials.phantom.model.model_number,
                scan.tolerance,
                scan.institution,
                report_path,
            )

            with open(report_path) as report:
                scan.full_report.save(report_filename, File(report))
                # TODO: save executive report too

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

            points_in_patient_xyz = FeatureDetector(
                gold_standard.phantom.model.model_number,
                modality,
                dicom_series.voxels,
                dicom_series.ijk_to_xyz
            ).run()

            fiducials = Fiducials.objects.create(fiducials=points_in_patient_xyz)
            gold_standard.fiducials = fiducials
            gold_standard.processing = False
            gold_standard.save()
    except Exception as e:
        raise e


@task_failure.connect
def task_failure_handler(task_id=None, exception=None, args=None, **kwargs):
    logging.info("{} {} {}".format(task_id, str(exception), str(args)))
