# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-14 21:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0033_auto_20180121_2252'),
    ]

    operations = [
        migrations.AddField(
            model_name='goldenfiducials',
            name='errors',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='institution',
            name='license_expiration_date',
            field=models.DateField(blank=True, help_text="The date when the institution's license expires; they are warned 30 days before it expires.  If left blank, the license won't expire at a particular date.", null=True),
        ),
        migrations.AlterField(
            model_name='institution',
            name='scans_remaining',
            field=models.PositiveIntegerField(blank=True, help_text='The number of scans the institution is allowed to complete before needing to purchase more scans.  They are warned when there are 20 scans remaining.  Only successfully completed scans will decrement the count.  If left blank the license will never expire due to the scan count.', null=True),
        ),
    ]
