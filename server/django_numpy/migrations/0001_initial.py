# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-13 21:38
from __future__ import unicode_literals

from django.db import migrations, models
import server.django_numpy.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NumpyFileFieldModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('array', server.django_numpy.fields.NdarrayFileField(upload_to='test_numpy_file_field/array')),
            ],
        ),
        migrations.CreateModel(
            name='NumpyFileFieldNullModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('array', server.django_numpy.fields.NdarrayFileField(null=True, upload_to='test_numpy_file_field_null/array')),
            ],
        ),
        migrations.CreateModel(
            name='NumpyTextFieldModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('array', server.django_numpy.fields.NdarrayTextField()),
            ],
        ),
        migrations.CreateModel(
            name='NumpyTextFieldNullModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('array', server.django_numpy.fields.NdarrayTextField(null=True)),
            ],
        ),
    ]
