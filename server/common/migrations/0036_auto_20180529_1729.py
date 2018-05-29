# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-29 21:29
from __future__ import unicode_literals

import dateutil.parser
import zipfile

from django.db import migrations

from process import dicom_import


def populate_dicom_fields(apps, schema_editor):
    DicomSeries = apps.get_model('common', 'DicomSeries')
    for dicom_series in DicomSeries.objects.all():
        with zipfile.ZipFile(dicom_series.zipped_dicom_files, 'r') as f:
            datasets = dicom_import.dicom_datasets_from_zip(f)
        first_dataset = datasets[0]
        dicom_series.patient_name = getattr(first_dataset, 'PatientName', None)
        if getattr(first_dataset, 'PatientBirthDate', None):
            dicom_series.patient_birth_date = dateutil.parser.parse(
                first_dataset.PatientBirthDate).date()
        dicom_series.patient_sex = getattr(first_dataset, 'PatientSex', None)
        dicom_series.modality = getattr(first_dataset, 'Modality', None)
        dicom_series.rows = getattr(first_dataset, 'Rows', None)
        dicom_series.columns = getattr(first_dataset, 'Columns', None)
        dicom_series.number_of_slices = getattr(first_dataset, 'NumberOfSlices', len(datasets))
        dicom_series.save()


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0035_auto_20180529_1727'),
    ]

    operations = [
        migrations.RunPython(populate_dicom_fields),
    ]
