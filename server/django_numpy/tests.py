import pytest
import numpy as np
from django.core.exceptions import ValidationError

from .fields import ndarray_to_bytes, bytes_to_ndarray
from .models import NumpyFileFieldModel, NumpyFileFieldNullModel, NumpyTextFieldModel


class CustomArray(np.ndarray):
    def __new__(cls, input_array):
        obj = np.asarray(input_array).view(cls)
        return obj


def test_numpy_file_field_save_and_reload(db):
    instance = NumpyFileFieldModel()
    array = np.random.rand(5, 10, 3)
    instance.array = array
    instance.save()
    reretrieved_instance = NumpyFileFieldModel.objects.get(pk=instance.pk)
    np.testing.assert_allclose(reretrieved_instance.array, array)


def test_numpy_file_field_custom_ndarray(db):
    instance = NumpyFileFieldModel()
    array = CustomArray(np.random.rand(5, 10, 3))
    with pytest.raises(ValidationError):
        instance.array = array
        instance.save()


def test_numpy_file_field_bad_type(db):
    instance = NumpyFileFieldModel()
    with pytest.raises(ValidationError):
        instance.array = 1
        instance.save()


# TODO test failure to load file
def test_numpy_file_field_load_failure(db):
    instance = NumpyFileFieldModel()
    array = np.random.rand(5, 10, 3)
    instance.array = array
    instance.save()


def test_numpy_file_field_save_failure(db):
    instance = NumpyFileFieldModel()
    with pytest.raises(FileNotFoundError):
        instance.array = 'bad.npy'
        instance.save()


def test_numpy_file_field_none(db):
    instance = NumpyFileFieldNullModel()
    array = np.random.rand(5, 10, 3)
    instance.array = array
    instance.save()
    assert instance is not None
    instance.array = None
    instance.save()
    reretrieved_instance = NumpyFileFieldNullModel.objects.get(pk=instance.pk)
    assert reretrieved_instance.array is None


def test_numpy_file_field_dtype(db):
    instance = NumpyFileFieldModel()
    array = np.random.randint(0, 100, (5, 10, 3))
    instance.array = array
    instance.save()
    reretrieved_instance = NumpyFileFieldModel.objects.get(pk=instance.pk)
    np.testing.assert_equal(reretrieved_instance.array, array)


def test_numpy_file_field_copy(db):
    a = NumpyFileFieldModel()
    b = NumpyFileFieldModel()
    array = np.random.rand(5, 10, 3)
    a.array = array
    b.array = a.array
    a.save()
    b.save()
    assert a.array.field_file != b.array.field_file
    # TODO: edit one array, save the instance, then assert the array values are indeed different.


def test_numpy_text_field_save_and_reload(db):
    instance = NumpyTextFieldModel()
    array = np.random.rand(5, 10, 3)
    instance.array = array
    instance.save()

    reretrieved_instance = NumpyTextFieldModel.objects.get(pk=instance.pk)

    np.testing.assert_allclose(reretrieved_instance.array, array)


def test_bytes_to_ndarray_preserves_data():
    original = np.random.rand(60, 160).astype(np.float64)

    primitive = ndarray_to_bytes(original)
    assert type(primitive) == bytes
    there_and_back = bytes_to_ndarray(primitive)

    np.testing.assert_allclose(original, there_and_back)
