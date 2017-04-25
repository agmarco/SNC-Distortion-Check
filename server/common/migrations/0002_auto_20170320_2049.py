# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-20 20:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Global',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': (('configuration', 'Configuration'),),
                'managed': False,
            },
        ),
        migrations.AlterModelOptions(
            name='machinesequencepair',
            options={'verbose_name': 'Machine-Sequence Combination'},
        ),
        migrations.AlterField(
            model_name='machinesequencepair',
            name='tolerance',
            field=models.FloatField(help_text='The maximum allowable geometric error_mags (mm) for this machine-scanner pair'),
        ),
        migrations.AlterField(
            model_name='user',
            name='institution',
            field=models.ForeignKey(blank=True, help_text='The institution this user is a member of; will be blank for admin users', null=True, on_delete=django.db.models.deletion.CASCADE, to='common.Institution'),
        ),
    ]
