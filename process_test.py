from unittest import mock
import math

import pytest
import numpy

from process import combine_dicom_slices


# direction cosines
x_cos = (1, 0, 0)
y_cos = (0, 1, 0)
z_cos = (0, 0, 1)
negative_x_cos = (-1, 0, 0)
negative_y_cos = (0, -1, 0)
negative_z_cos = (0, 0, -1)

arbitrary_shape = (10, 11)


def generate_mock_slice(pixel_array, slice_position, row_cosine, column_cosine):
    '''
    Build a minimal DICOM dataset representing a dataslice at a particular
    slice location.  The `slice_position` is the coordinate value along the
    remaining unused axis (i.e. the axis perpendicular to the direction
    cosines).
    '''
    na, nb = pixel_array.shape

    dataset = mock.Mock()
    dataset.pixel_array = pixel_array

    dataset.SeriesInstanceUID = 'arbitrary uid'
    dataset.SOPClassUID = 'arbitrary sopclass uid'
    dataset.PixelSpacing = [1.0, 1.0]
    dataset.Rows = na
    dataset.Columns = nb

    # assume that the images are centered on the remaining unused axis
    a_component = [-na/2.0*c for c in row_cosine]
    b_component = [-nb/2.0*c for c in column_cosine]
    c_component = [(slice_position if c == 0 and cc == 0 else 0) for c, cc in zip(row_cosine, column_cosine)]
    patient_position = [a + b + c for a, b, c in zip(a_component, b_component, c_component)]

    dataset.ImagePositionPatient = patient_position

    dataset.ImageOrientationPatient = list(row_cosine) + list(column_cosine)
    return dataset


@pytest.fixture
def axial_slices():
    return [
        generate_mock_slice(randi(*arbitrary_shape), 0, x_cos, y_cos),
        generate_mock_slice(randi(*arbitrary_shape), 1, x_cos, y_cos),
        generate_mock_slice(randi(*arbitrary_shape), 2, x_cos, y_cos),
        generate_mock_slice(randi(*arbitrary_shape), 3, x_cos, y_cos),
    ]


def test_combine_dicom_slices_axial(axial_slices):
    '''
    Axial slices cut perpendicular to the spinalchord.  Hence the row-cosine is
    in the x-direction in the patient coordinate system, and the column-cosine
    is in the y-direction in the patient coordinate system.
    '''
    combined = combine_dicom_slices(axial_slices[0:2])
    manually_combined = numpy.dstack((axial_slices[0].pixel_array, axial_slices[1].pixel_array))
    assert numpy.array_equal(combined, manually_combined)


def test_combine_dicom_slices_rows_and_cols_swapped():
    '''
    The direction cosines can be swapped.  In this case, these are still
    axial slices, however the slice-images have been transposed.
    '''
    slice_0_data = randi(*arbitrary_shape)
    slice_1_data = randi(*arbitrary_shape)
    slices = [
        generate_mock_slice(slice_0_data, 0, y_cos, x_cos),
        generate_mock_slice(slice_1_data, 1, y_cos, x_cos),
    ]

    combined = combine_dicom_slices(slices)
    manually_combined = numpy.dstack((slice_0_data.T, slice_1_data.T))
    assert numpy.array_equal(combined, manually_combined)


def test_combine_dicom_slices_row_direction_inverted():
    '''
    The direction cosines can also be negative.  In this case, these are still
    axial slices, however the slice-images have been reflected across one of
    the image axes.
    '''
    slice_0_data = randi(*arbitrary_shape)
    slice_1_data = randi(*arbitrary_shape)
    slices = [
        generate_mock_slice(slice_0_data, 0, negative_x_cos, y_cos),
        generate_mock_slice(slice_1_data, 1, negative_x_cos, y_cos),
    ]

    combined = combine_dicom_slices(slices)
    manually_combined = numpy.dstack((slice_0_data[::-1, :], slice_1_data[::-1, :]))
    assert numpy.array_equal(combined, manually_combined)


def test_combine_dicom_slices_sagital():
    '''
    Sagittal slices cut-sideways through the person.  E.g. a sagital slice will
    show the profile of a person.

    Typically, the person will be "looking" to the left-side of the image,
    hence the "row-cosine" points in the positive y-direction in the patient
    coordinate system, and the "column-cosine" points in the negative
    z-direction in the patient coordinate system.
    '''
    slice_0_data = randi(*arbitrary_shape)
    slice_1_data = randi(*arbitrary_shape)
    slices = [
        generate_mock_slice(slice_0_data, 0, y_cos, negative_z_cos),
        generate_mock_slice(slice_1_data, 1, y_cos, negative_z_cos),
    ]

    combined = combine_dicom_slices(slices)

    manually_combined = numpy.empty([2, arbitrary_shape[0], arbitrary_shape[1]])
    manually_combined[0, :, :] = slice_0_data[:, ::-1]
    manually_combined[1, :, :] = slice_1_data[:, ::-1]

    assert numpy.array_equal(combined, manually_combined)


def test_combine_dicom_slices_coronal():
    '''
    Coronal (or frontal) slices, in humans, cuts through both ears, hands and feet.  In this case, we
    have the row direction-cosine pointing in the positive x-direction, and the
    column direction-cosine pointing in the negative z-direction.
    '''
    slice_0_data = randi(*arbitrary_shape)
    slice_1_data = randi(*arbitrary_shape)
    slices = [
        generate_mock_slice(slice_0_data, 0, x_cos, negative_z_cos),
        generate_mock_slice(slice_1_data, 1, x_cos, negative_z_cos),
    ]

    combined = combine_dicom_slices(slices)

    manually_combined = numpy.empty([arbitrary_shape[0], 2, arbitrary_shape[1]])
    manually_combined[:, 0, :] = slice_0_data[:, ::-1]
    manually_combined[:, 1, :] = slice_1_data[:, ::-1]

    assert numpy.array_equal(combined, manually_combined)


def test_combine_dicom_slices_non_orthogonal_direction_cosines(axial_slices):
    '''
    We assume that the direction cosines are perpendicular to each other.
    '''
    one_degree = 1*math.pi/180
    non_orthogonal_orientation = [1, 0, 0, math.sin(one_degree), math.cos(one_degree), 0]
    for dataset in axial_slices:
        dataset.ImageOrientationPatient = non_orthogonal_orientation

    with pytest.raises(ValueError):
        combine_dicom_slices(axial_slices)


def test_combine_dicom_slices_non_standard_direction_cosines(axial_slices):
    '''
    Currently was assume that the direction cosines are oriented perpendicular
    to the axes of the patient coordinate system.
    '''
    one_degree = 1*math.pi/180
    non_standard_orientation = [-math.cos(one_degree), math.sin(one_degree), 0, \
                                   math.sin(one_degree), math.cos(one_degree), 0]
    for dataset in axial_slices:
        dataset.ImageOrientationPatient = non_standard_orientation

    with pytest.raises(ValueError):
        combine_dicom_slices(axial_slices)


def test_combine_dicom_slices_casts_to_float(axial_slices):
    '''
    The typically integer DICOM pixel data should be cast to a float.
    '''
    assert combine_dicom_slices(axial_slices).dtype == numpy.dtype('float64')


def test_combine_dicom_slices_is_robust_to_ordering(axial_slices):
    '''
    The DICOM slices should be able to be passed in in any order, and they
    should be recombined appropriately.
    '''
    assert numpy.array_equal(
        combine_dicom_slices([axial_slices[0], axial_slices[1], axial_slices[2]]),
        combine_dicom_slices([axial_slices[1], axial_slices[0], axial_slices[2]])
    )

    assert numpy.array_equal(
        combine_dicom_slices([axial_slices[0], axial_slices[1], axial_slices[2]]),
        combine_dicom_slices([axial_slices[2], axial_slices[0], axial_slices[1]])
    )


def test_combine_dicom_slices_missing_middle_slice(axial_slices):
    '''
    All slices must be present.  Slice position is determined using the
    ImagePositionPatient (0020,0032) tag.
    '''
    with pytest.raises(ValueError):
        combine_dicom_slices([axial_slices[0], axial_slices[2], axial_slices[3]])


def test_combine_dicom_slices_slice_from_different_series(axial_slices):
    '''
    As a sanity check, slices that don't come from the same DICOM series should
    be rejected.
    '''
    axial_slices[2].SeriesInstanceUID += 'Ooops'
    with pytest.raises(ValueError):
        combine_dicom_slices(axial_slices)


@pytest.mark.xfail(reason='Not sure how to detect this in DICOM')
def test_combine_dicom_slices_missing_end_slice(axial_slices):
    '''
    Ideally, we would detect missing edge slices, however given that we don't
    know any way to determine the number of slices are in a DICOM series, this
    seems impossible.
    '''
    with pytest.raises(ValueError):
        combine_dicom_slices([axial_slices[0], axial_slices[1], axial_slices[2]])


def randi(*shape):
    return numpy.random.randint(1000, size=shape, dtype='uint16')
