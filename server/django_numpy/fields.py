import io
import uuid

import six
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import ugettext_lazy as _
import numpy as np


def bytes_to_ndarray(data):
    f = io.BytesIO(data)
    return np.load(f, allow_pickle=False)


def ndarray_to_bytes(ndarray):
    f = io.BytesIO()
    np.save(f, ndarray, allow_pickle=False)
    return f.getvalue()


class FileFieldArray(np.ndarray):
    def __new__(cls, input_array, instance=None, field=None, field_file=None):
        obj = np.asarray(input_array).view(cls)
        obj._instance = instance
        obj._field = field
        obj._field_file = None
        return obj

    @property
    def field_file(self):
        if self._field_file is None:
            filename = f'{uuid.uuid4()}.npy'
            content_file = ContentFile(ndarray_to_bytes(self), filename)
            self._field_file = self._field.attr_class(self._instance, self._field, content_file.name)
            self._field_file.file = content_file
            self._field_file._committed = False
        return self._field_file


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

        if self.field.name in instance.__dict__:
            value = instance.__dict__[self.field.name]
        else:
            instance.refresh_from_db(fields=[self.field.name])
            value = getattr(instance, self.field.name)

        if value is None:
            value = None
        elif isinstance(value, six.string_types):
            field_file = self.field.attr_class(instance, self.field, value)
            value = np.load(field_file.file, allow_pickle=False)
            value = FileFieldArray(value, instance, self.field, field_file)
        else:
            value = FileFieldArray(value, instance, self.field)

        instance.__dict__[self.field.name] = value
        return value

    def __set__(self, instance, value):
        if type(value) not in (np.ndarray, FileFieldArray) and not isinstance(value, six.string_types) and value is not None:
            if isinstance(value, np.ndarray):
                raise ValidationError("Subclasses of ndarray are not supported.")
            else:
                raise ValidationError("NumpyFileField's value must be an ndarray.")

        instance.__dict__[self.field.name] = value


class NumpyFileField(models.FileField):
    description = _("Numpy Array File")
    descriptor_class = NumpyDescriptor

    def get_prep_value(self, value):
        value = super(models.FileField, self).get_prep_value(value)
        # Need to convert File objects provided via a form to unicode for database insertion
        if value is None:
            return None
        else:
            return six.text_type(value.field_file)

    def pre_save(self, model_instance, add):
        value = super(models.FileField, self).pre_save(model_instance, add)
        if value is None:
            return None
        else:
            file = value.field_file
            if file and not file._committed:
                # Commit the file to storage prior to saving the model
                file.save(file.name, file.file, save=False)
            return value


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
