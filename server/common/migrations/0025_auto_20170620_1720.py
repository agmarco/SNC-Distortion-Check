# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-20 21:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0024_auto_20170610_1709'),
    ]

    operations = [
        migrations.AddField(
            model_name='sequence',
            name='tolerance',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='phantom',
            name='institution',
            field=models.ForeignKey(blank=True, help_text='The institution that owns this phantom.  If blank, new users can register an account to the phantom if they know the serial number.', null=True, on_delete=django.db.models.deletion.CASCADE, to='common.Institution'),
        ),
    ]
