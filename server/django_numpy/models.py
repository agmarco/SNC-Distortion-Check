from django.db import models

from .fields import NumpyFileField, NumpyTextField


class NumpyFileFieldModel(models.Model):
    array = NumpyFileField(upload_to='test_numpy_file_field/array')


class NumpyFileFieldNullModel(models.Model):
    array = NumpyFileField(upload_to='test_numpy_file_field_null/array', null=True)


class NumpyTextFieldModel(models.Model):
    array = NumpyTextField()


class NumpyTextFieldNullModel(models.Model):
    array = NumpyTextField(null=True)
