import zipfile

from celery import shared_task
from django.db import transaction

from .models import Scan
from process.dicom_import import combine_slices, dicom_datasets_from_zip
from process.feature_detection import FeatureDetector


@shared_task
def process_scan(scan_id):
    scan = Scan.objects.get(pk=scan_id)

    try:
        with transaction.atomic():
            scan.errors = None
            phantom_name = '603A'
            modality = 'mri'

            with zipfile.ZipFile(scan.dicom_archive, 'r') as zip_file:
                datasets = dicom_datasets_from_zip(zip_file)
            voxels, ijk_to_xyz = combine_slices(datasets)

            points_in_patient_xyz = FeatureDetector(phantom_name, modality, voxels, ijk_to_xyz).run()
            scan.result = "Success, found {} points".format(points_in_patient_xyz.shape[1])
            scan.processing = False
            scan.save()
    except Exception as e:
        scan.errors = str(e)
        scan.processing = False
        scan.save()
        raise e
