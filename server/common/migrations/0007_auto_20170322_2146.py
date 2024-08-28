# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-22 21:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_phantommodel_cad_fiducials'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phantommodel',
            name='cad_fiducials',
            field=models.ForeignKey(help_text='The hard-coded gold standard points for the phantom model', on_delete=django.db.models.deletion.CASCADE, to='common.Fiducials'),
        ),
    ]
