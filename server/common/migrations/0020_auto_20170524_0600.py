# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-24 06:00
from __future__ import unicode_literals

from django.db import migrations, models
import server.common.models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0019_merge_20170518_1913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phantom',
            name='serial_number',
            field=models.CharField(help_text="The Phantom's serial number", max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='scan',
            name='executive_report',
            field=models.FileField(null=True, upload_to=server.common.models.scan_upload_path),
        ),
        migrations.AlterField(
            model_name='scan',
            name='full_report',
            field=models.FileField(null=True, upload_to=server.common.models.scan_upload_path),
        ),
        migrations.AlterField(
            model_name='scan',
            name='raw_data',
            field=models.FileField(null=True, upload_to=server.common.models.scan_upload_path),
        ),
    ]