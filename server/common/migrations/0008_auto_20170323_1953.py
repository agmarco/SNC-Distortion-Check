# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-23 19:53
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import server.common.models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_auto_20170322_2146'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', server.common.models.CommonFieldsUserManager()),
            ],
        ),
        migrations.AddField(
            model_name='dicomseries',
            name='acquisition_date',
            field=models.DateField(default=datetime.datetime(2017, 3, 23, 19, 53, 24, 400328), help_text='The DICOM Series Instance Acquisition Date'),
            preserve_default=False,
        ),
    ]
