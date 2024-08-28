# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-26 10:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0027_auto_20170628_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scan',
            name='dicom_series',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='common.DicomSeries'),
        ),
    ]
