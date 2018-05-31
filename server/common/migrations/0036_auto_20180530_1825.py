# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-30 22:25
from __future__ import unicode_literals

import zipfile

import botocore.exceptions
from django.db import migrations

from process import dicom_import


def populate_dicom_fields(apps, schema_editor):
    DicomSeries = apps.get_model('common', 'DicomSeries')
    for dicom_series in DicomSeries.objects.all():
        try:
            with zipfile.ZipFile(dicom_series.zipped_dicom_files, 'r') as f:
                datasets = dicom_import.dicom_datasets_from_zip(f)
            first_dataset = datasets[0]
            dicom_series.patient_name = getattr(first_dataset, 'PatientName', None)
            dicom_series.patient_birth_date = getattr(first_dataset, 'PatientBirthDate', None)
            dicom_series.patient_sex = getattr(first_dataset, 'PatientSex', None)
            dicom_series.modality = getattr(first_dataset, 'Modality', None)
            dicom_series.rows = getattr(first_dataset, 'Rows', None)
            dicom_series.columns = getattr(first_dataset, 'Columns', None)
            dicom_series.number_of_slices = getattr(first_dataset, 'NumberOfSlices', None)
            dicom_series.save()
        except (ValueError, zipfile.BadZipFile, botocore.exceptions.ClientError):
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0035_auto_20180530_1824'),
    ]

    operations = [
        migrations.RunPython(populate_dicom_fields),
    ]
