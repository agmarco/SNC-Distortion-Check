# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-22 03:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0032_remove_institution_number_of_licenses'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dicomseries',
            name='ijk_to_xyz',
        ),
        migrations.RemoveField(
            model_name='dicomseries',
            name='shape',
        ),
        migrations.RemoveField(
            model_name='dicomseries',
            name='voxels',
        ),
    ]