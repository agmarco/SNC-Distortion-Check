# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-04 18:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0013_auto_20170403_2009'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scan',
            name='result',
        ),
    ]
