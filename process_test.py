import pytest
import numpy
import dicom

from process import combine_dicom_slices


def generate_test_slice(z, nx=10, ny=11):
    slice_data_set = dicom.dataset.Dataset()
    slice_data_set.pixel_array = numpy.random.rand(nx, ny)
    slice_data_set.ImagePositionPatient = [-nx/2.0, -ny/2.0, z]
    return slice_data_set


@pytest.fixture
def slices():
    return [
        generate_test_slice(0),
        generate_test_slice(1),
        generate_test_slice(2),
        generate_test_slice(3),
    ]


def test_combine_dicom_slices_simple_case(slices):
    combined = combine_dicom_slices(slices[0:2])
    manually_combined = numpy.dstack((slices[0].pixel_array, slices[1].pixel_array))
    assert numpy.array_equal(combined, manually_combined)


def test_combine_dicom_slices_is_robust_to_ordering(slices):
    assert numpy.array_equal(
        combine_dicom_slices([slices[0], slices[1], slices[2]]),
        combine_dicom_slices([slices[1], slices[0], slices[2]])
    )

    assert numpy.array_equal(
        combine_dicom_slices([slices[0], slices[1], slices[2]]),
        combine_dicom_slices([slices[2], slices[0], slices[1]])
    )


def test_combine_dicom_slices_missing_middle_slice(slices):
    with pytest.raises(ValueError):
        combine_dicom_slices([slices[0], slices[2], slices[3]])


@pytest.mark.xfail(reason='Not sure how to detect this in DICOM')
def test_combine_dicom_slices_missing_end_slice(slices):
    with pytest.raises(ValueError):
        combine_dicom_slices([slices[0], slices[1], slices[2]])
