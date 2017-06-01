import io
import uuid

import six
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

        # self.field.field_file is updated whenever __get__ is invoked.

        if isinstance(value, six.string_types):
            self.field.field_file = self.field.attr_class(instance, self.field, value)
            instance.__dict__[self.field.name] = np.load(self.field.field_file.file, allow_pickle=False)

        elif isinstance(value, np.ndarray) and self.field.field_file is None:
            filename = f'{uuid.uuid4()}.npy'
            file = ContentFile(ndarray_to_bytes(value), filename)
            self.field.field_file = self.field.attr_class(instance, self.field, file.name)
            self.field.field_file.file = file
            self.field.field_file._committed = False

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        self.field.field_file = None


class NumpyFieldFile(FieldFile):
    def save(self, name, content, save=True):
        name = self.field.generate_filename(self.instance, name)
        self.name = self.storage.save(name, content, max_length=self.field.max_length)
        self._committed = True

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()

    def delete(self, save=True):
        if not self:
            return
        # Only close the file if it's already open, which we know by the
        # presence of self._file
        if hasattr(self, '_file'):
            self.close()
            del self.file

        self.storage.delete(self.name)

        self.name = None
        self._committed = False

        if save:
            self.instance.save()


class NumpyFileField(models.FileField):
    description = _("Numpy Array File")
    descriptor_class = NumpyDescriptor
    attr_class = NumpyFieldFile

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.field_file = None

    def get_prep_value(self, value):
        if self.field_file is None:
            return None
        else:
            return six.text_type(self.field_file)

    def pre_save(self, model_instance, add):
        ndarray = super(models.FileField, self).pre_save(model_instance, add)
        if self.field_file and not self.field_file._committed:
            self.field_file.save(self.field_file.name, self.field_file.file, save=False)
        return ndarray


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
