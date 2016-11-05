from unittest import mock
import math

import pytest
import numpy

from dicom_import import combine_slices, validate_slices_form_uniform_grid, merge_slice_pixel_arrays


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


class TestMergeSlices:
    def test_simple_axial_set(self, axial_slices):
        combined, _ = combine_slices(axial_slices[0:2])

        manually_combined = numpy.dstack((axial_slices[0].pixel_array, axial_slices[1].pixel_array))
        assert numpy.array_equal(combined, manually_combined)


class TestMergeSlicePixelArrays:
    def test_casts_to_float(self, axial_slices):
        '''
        The typically integer DICOM pixel data should be cast to a float.
        '''
        assert merge_slice_pixel_arrays(axial_slices).dtype == numpy.dtype('float64')


    def test_robust_to_ordering(self, axial_slices):
        '''
        The DICOM slices should be able to be passed in in any order, and they
        should be recombined appropriately.
        '''
        assert numpy.array_equal(
            merge_slice_pixel_arrays([axial_slices[0], axial_slices[1], axial_slices[2]]),
            merge_slice_pixel_arrays([axial_slices[1], axial_slices[0], axial_slices[2]])
        )

        assert numpy.array_equal(
            merge_slice_pixel_arrays([axial_slices[0], axial_slices[1], axial_slices[2]]),
            merge_slice_pixel_arrays([axial_slices[2], axial_slices[0], axial_slices[1]])
        )


class TestValidateSlicesFormUniformGrid:
    def test_missing_middle_slice(self, axial_slices):
        '''
        All slices must be present.  Slice position is determined using the
        ImagePositionPatient (0020,0032) tag.
        '''
        with pytest.raises(ValueError):
            validate_slices_form_uniform_grid([axial_slices[0], axial_slices[2], axial_slices[3]])

    def test_slices_from_different_series(self, axial_slices):
        '''
        As a sanity check, slices that don't come from the same DICOM series should
        be rejected.
        '''
        axial_slices[2].SeriesInstanceUID += 'Ooops'
        with pytest.raises(ValueError):
            validate_slices_form_uniform_grid(axial_slices)

    @pytest.mark.xfail(reason='Not sure how to detect this in DICOM')
    def test_missing_end_slice(self, axial_slices):
        '''
        Ideally, we would detect missing edge slices, however given that we don't
        know any way to determine the number of slices are in a DICOM series, this
        seems impossible.
        '''
        with pytest.raises(ValueError):
            validate_slices_form_uniform_grid([axial_slices[0], axial_slices[1], axial_slices[2]])


def randi(*shape):
    return numpy.random.randint(1000, size=shape, dtype='uint16')
