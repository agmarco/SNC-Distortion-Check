import io
import uuid

import six
from django.core.files.base import ContentFile
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile, FileDescriptor
from django.utils.translation import ugettext_lazy as _
import numpy as np


def bytes_to_ndarray(data):
    f = io.BytesIO(data)
    return np.load(f, allow_pickle=False)


def ndarray_to_bytes(ndarray):
    f = io.BytesIO()
    np.save(f, ndarray, allow_pickle=False)
    return f.getvalue()


class NumpyDescriptor:
    """
    The descriptor for the numpy array.
    
    A lot of this code was copied from:

        django/db/models/fields/files.py

    """
    def __init__(self, field, file_attname):
        self.field = field
        self.file_attname = file_attname

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        if self.field.name not in instance.__dict__:
            instance.refresh_from_db(fields=[self.field.name])

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        setattr(self.field, self.file_attname, ContentFile(ndarray_to_bytes(value), name=f'{uuid.uuid4()}.npy'))


class NumpyFileField(models.FileField):
    description = _("Numpy Array File")
    descriptor_class = NumpyDescriptor

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # TODO ?
        NumpyFileField.file = FileDescriptor(self)

    def contribute_to_class(self, cls, name, **kwargs):
        super(models.FileField, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.descriptor_class(self, 'file'))

    def get_prep_value(self, value):
        value = super(models.FileField, self).get_prep_value(self.file)
        if value is None:
            return None
        return six.text_type(value)

    def pre_save(self, model_instance, add):
        file = self.file
        if file and not file._committed:
            file.save(file.name, file.file, save=False)
        return file


class NumpyTextField(models.BinaryField):
    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        else:
            return bytes_to_ndarray(value.tobytes())

    def to_python(self, value):
        if isinstance(value, np.ndarray) or value is None:
            return value
        else:
            return bytes_to_ndarray(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        else:
            value_as_bytes = ndarray_to_bytes(value)
            return super().get_prep_value(value_as_bytes)
