import io

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import numpy as np


def bytes_to_ndarray(data):
    f = io.BytesIO(data)
    return np.load(f, allow_pickle=False)


def ndarray_to_bytes(ndarray):
    f = io.BytesIO()
    np.save(f, ndarray, allow_pickle=False)
    return f.getvalue()


# TODO: finish working on this
class NumpyDescriptor(object):
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


class NumpyFileField(models.FileField):
    description = _("Numpy Array File")
    descriptor_class = NumpyDescriptor


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
