# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-13 21:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0036_auto_20180530_1825'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.BooleanField(default=False, help_text='Deleted items are hidden from non-admins')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_modified_on', models.DateTimeField(auto_now=True)),
                ('number', models.PositiveSmallIntegerField(unique=True)),
                ('phantom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.Phantom')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
