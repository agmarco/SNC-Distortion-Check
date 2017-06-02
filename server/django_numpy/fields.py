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


class FileFieldArray(np.ndarray):

    def __new__(cls, input_array, instance=None):
        obj = np.asarray(input_array).view(cls)
        obj.instance = instance
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        else:
            self.instance = getattr(obj, 'instance', None)


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

        if isinstance(value, six.string_types):
            field_file = self.field.get_file(instance)
            value = np.load(field_file.file, allow_pickle=False)

        if type(value) is FileFieldArray:
            value.instance = instance
        elif isinstance(value, np.ndarray):
            value = FileFieldArray(value, instance)

        instance.__dict__[self.field.name] = value
        return value

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        self.field.set_file(instance, value)


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
        # Only close the file if it's already open, which we know by the presence of self._file
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
        self._files = {}

    def set_file(self, instance, value):
        self._files[instance.pk] = value

    def get_file(self, instance):
        value = self._files[instance.pk]

        if isinstance(value, six.string_types):
            field_file = self.attr_class(instance, self, value)
            self._files[instance.pk] = field_file

        elif isinstance(value, np.ndarray):
            filename = f'{uuid.uuid4()}.npy'
            content_file = ContentFile(ndarray_to_bytes(value), filename)
            field_file = self.attr_class(instance, self, content_file.name)
            field_file.file = content_file
            field_file._committed = False
            self._files[instance.pk] = field_file

        return self._files[instance.pk]

    def get_prep_value(self, value):
        value = super(models.FileField, self).get_prep_value(value)
        # Need to convert File objects provided via a form to unicode for database insertion
        if value is None:
            return None
        else:
            return six.text_type(self.get_file(value.instance))

    def pre_save(self, model_instance, add):
        value = super(models.FileField, self).pre_save(model_instance, add)
        file = self.get_file(model_instance)
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
