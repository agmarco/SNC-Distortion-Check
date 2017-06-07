import numpy as np
import pytest

from process.utils import decimate, fov_center_xyz


class TestDecimate:
    def test_simple_three_dimensions(self):
        a = np.zeros((10, 20, 10))
        a[:5, :16, :5] = 1
        a_decimated = decimate(a, 5)
        assert np.allclose(a_decimated, np.array([
            [[1, 0], [1, 0], [1, 0], [0.2, 0]],
            [[0, 0], [0, 0], [0, 0], [0, 0]],
        ]))

    def test_size_mismatch(self):
        a = np.zeros((10, 20))
        with pytest.raises(AssertionError):
            decimate(a, 6)


class TestFovCenterXyz:
    def test_even_shape_no_transform(self):
        voxel_shape = (3, 3, 3)
        ijk_to_xyz = np.identity(4)
        actual = fov_center_xyz(voxel_shape, ijk_to_xyz)
        expected = np.array([1, 1, 1])
        np.testing.assert_allclose(actual, expected)

    def test_odd_shape_no_transform(self):
        voxel_shape = (4, 4, 4)
        ijk_to_xyz = np.identity(4)
        actual = fov_center_xyz(voxel_shape, ijk_to_xyz)
        expected = np.array([1.5, 1.5, 1.5])
        np.testing.assert_allclose(actual, expected)

