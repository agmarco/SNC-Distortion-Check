import numpy as np

from .fields import ndarray_to_bytes, bytes_to_ndarray
from .models import NumpyFileFieldModel, NumpyTextFieldModel


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
    instance.array = array
    instance.save()
    reretrieved_instance = NumpyFileFieldModel.objects.get(pk=instance.pk)
    np.testing.assert_allclose(reretrieved_instance.array, array)


def test_numpy_text_field_save_and_reload(db):
    instance = NumpyTextFieldModel()
    array = np.random.rand(5, 10, 3)
    instance.array = array
    instance.save()

    reretrieved_instance = NumpyTextFieldModel.objects.get(pk=instance.pk)

    np.testing.assert_allclose(reretrieved_instance.array, array)


def test_bytes_to_ndarray_preserves_data():
    original = np.random.rand(60, 160).astype(np.float64)

    primative = ndarray_to_bytes(original)
    assert type(primative) == bytes
    there_and_back = bytes_to_ndarray(primative)

    np.testing.assert_allclose(original, there_and_back)
