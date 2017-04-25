# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-04 19:17
from __future__ import unicode_literals
import numpy as np

from django.db import migrations, models
import server.django_numpy.fields


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0014_remove_scan_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='error_mags',
            field=server.django_numpy.fields.NumpyTextField(null=True),
        ),
        migrations.AlterField(
            model_name='scan',
            name='tolerance',
            field=models.FloatField(default=np.array([0])),
            preserve_default=False,
        ),
    ]
