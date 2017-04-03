import logging
import zipfile

from celery import shared_task
from celery.signals import task_failure
from django.db import transaction

from process.dicom_import import combine_slices, dicom_datasets_from_zip
from process.feature_detection import FeatureDetector

from .models import Scan, Fiducials, GoldenFiducials, DicomSeries

logger = logging.getLogger(__name__)


@shared_task
def process_scan(scan_pk):
    scan = Scan.objects.get(pk=scan_pk)

    try:
        with transaction.atomic():
            points_in_patient_xyz = FeatureDetector(
                scan.golden_fiducials.phantom.model.model_number,
                'mri',
                scan.dicom_series.voxels,
                scan.dicom_series.ijk_to_xyz
            ).run()

            scan.result = f"Success, found {points_in_patient_xyz.shape[1]} points"
            scan.processing = False
            scan.save()
    except Exception as e:
        scan.errors = str(e)
        scan.processing = False
        scan.save()
        raise e


@shared_task
def process_ct_upload(dicom_series_pk, gold_standard_pk):
    try:
        with transaction.atomic():
            dicom_series = DicomSeries.objects.get(pk=dicom_series_pk)
            gold_standard = GoldenFiducials.objects.get(pk=gold_standard_pk)

            points_in_patient_xyz = FeatureDetector(
                gold_standard.phantom.model.model_number,
                'ct',
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
