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

from process import dicom_import, affine, phantoms
from process.affine import apply_affine
from process.feature_detection import FeatureDetector
from process.registration import rigidly_register_and_categorize
from process.reports import generate_report, generate_cube

from .models import Scan, Fiducials, GoldenFiducials, DicomSeries

logger = logging.getLogger(__name__)


@shared_task
def process_scan(scan_pk):
    scan = Scan.objects.get(pk=scan_pk)

    try:
        with transaction.atomic():
            modality = 'mri'

            voxels = scan.dicom_series.voxels,
            ijk_to_xyz = scan.dicom_series.ijk_to_xyz
            voxel_spacing = affine.voxel_spacing(ijk_to_xyz)

            feature_detector = FeatureDetector(
                scan.phantom.model.model_number,
                modality,
                voxels,
                ijk_to_xyz,
            )

            pruned_points_ijk = remove_fps(feature_detector.points_ijk, voxels, voxel_spacing)
            pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

            scan.detected_fiducials = Fiducials.objects.create(fiducials=pruned_points_xyz)

            xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                scan.golden_fiducials.fiducials.fiducials,
                scan.detected_fiducials.fiducials,
            )

            if TP_B.size == 0:
                raise Exception("No fiducials could be matched with the gold standard.")

            scan.TP_A_S = Fiducials.objects.create(fiducials=TP_A_S)
            scan.TP_B = Fiducials.objects.create(fiducials=TP_B)

            with zipfile.ZipFile(scan.dicom_series.zipped_dicom_files, 'r') as zip_file:
                datasets = dicom_import.dicom_datasets_from_zip(zip_file)

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
