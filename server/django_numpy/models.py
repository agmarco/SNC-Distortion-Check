from django.db import models

from .fields import NdarrayFileField, NdarrayTextField


class NumpyFileFieldModel(models.Model):
    array = NdarrayFileField(upload_to='test_numpy_file_field/array')


class NumpyFileFieldNullModel(models.Model):
    array = NdarrayFileField(upload_to='test_numpy_file_field_null/array', null=True)


class NumpyTextFieldModel(models.Model):
    array = NdarrayTextField()


class NumpyTextFieldNullModel(models.Model):
    array = NdarrayTextField(null=True)
