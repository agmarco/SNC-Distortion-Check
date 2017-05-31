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
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        if self.field.name not in instance.__dict__:
            instance.refresh_from_db(fields=[self.field.name])

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        #  TODO committed


class NumpyFileField(models.FileField):
    description = _("Numpy Array File")
    descriptor_class = NumpyDescriptor

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.field_file = None
        self._committed = False

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        else:
            #  TODO None = instance
            self.field_file = self.attr_class(None, self, value)
            return np.load(self.field_file.file, allow_pickle=False)

    def to_python(self, value):
        if isinstance(value, np.ndarray) or value is None:
            return value
        else:
            #  TODO None = instance
            self.field_file = self.attr_class(None, self, value)
            return np.load(self.field_file.file, allow_pickle=False)

    def get_prep_value(self, value):
        # TODO
        value = super(models.FileField, self).get_prep_value(value)
        if value is None:
            return None
        return six.text_type(value)

    def pre_save(self, model_instance, add):
        ndarray = super(models.FileField, self).pre_save(model_instance, add)
        if ndarray is not None and not self._committed:
            filename = self.generate_filename(model_instance, f'{uuid.uuid4()}.npy')
            file = ContentFile(ndarray_to_bytes(ndarray), filename)
            self.field_file = self.attr_class(model_instance, self, file.name)
            self.field_file.file = file
            self.field_file._committed = self._committed
            self.field_file.save(file.name, file.file, save=False)
            return self.field_file.name
        else:
            return None


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
