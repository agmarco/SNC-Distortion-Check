# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-28 18:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0009_auto_20170324_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='goldenfiducials',
            name='processing',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='goldenfiducials',
            name='fiducials',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='common.Fiducials'),
        ),
    ]
