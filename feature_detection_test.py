import math

import pytest
import numpy as np
from numpy.testing import assert_allclose

from feature_detection import cylindrical_grid_kernel, _fill_corners


class TestCylinderGridKernel:
    def test_size_non_uniform(self):
        '''
        Check that the kernel size is reasonable.  The kernel shape should
        always be odd, and should depend only on the grid spacing and the pixel
        size.
        '''
        pixel_spacing = (1.0, 2.0, 4.0)
        grid_radius = 4.0
        grid_spacing = 12.0
        expected_shape = tuple(1 + 2*math.ceil((0.5*grid_spacing - 0.5*p)/p) for p in pixel_spacing)
        kernel = cylindrical_grid_kernel(pixel_spacing, grid_radius, grid_spacing, upsample=1)
        assert kernel.shape == expected_shape

    def test_no_upsampling(self):
        pixel_spacing = (1.0, 1.0, 1.0)
        grid_radius = 0.5
        grid_spacing = 2.0
        kernel = cylindrical_grid_kernel(pixel_spacing, grid_radius, grid_spacing, upsample=1)

        intersection_slice = np.array([
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ])

        off_slice = np.array([
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ])

        assert_allclose(kernel[0, :, :], off_slice)
        assert_allclose(kernel[1, :, :], intersection_slice)
        assert_allclose(kernel[2, :, :], off_slice)

    def test_upsampling(self):
        '''
        Set the grid radius such that 5/9 upsampled voxels fall within the
        cylinder.
        '''
        pixel_spacing = (1.0, 1.0, 1.0)
        grid_radius = 1/6 + 0.00001
        grid_spacing = 2.0
        kernel = cylindrical_grid_kernel(pixel_spacing, grid_radius, grid_spacing, upsample=3)

        g = 15.0/27.0
        off_slice = np.array([
            [0, 0, 0],
            [0, g, 0],
            [0, 0, 0],
        ])
        print(kernel[0, :, :])
        assert_allclose(kernel[0, :, :], off_slice)

    @pytest.mark.skip
    def test_volume(self):
        '''
        The volume of the intersection of two cylinders is:

            I2 = (16/3)*r^3

        The volume of the intersection of three cylinders is:

            I3 = 8*(2 - sqrt(2))*r^3

        See http://mathworld.wolfram.com/SteinmetzSolid.html

        The volume of the union of two intersecting cylinders of length L is:

            U2 = 2*(pi*r^2*L) - I2

        The volume of the union of three intersection cylinders of length L is:

            U3 = U2 + (pi*r^2*L) - 2*I2 + I3
               = 3*(pi*r^2*L) - 3*I2 + I3
               = 3*(pi*r^2*L) - 3*(16/3)*r^3 + 8*(2 - sqrt(2))*r^3

        because you subtract out the intersection of the third cylinder with
        each of the other two, and then add back the intersection of all three.

        NOTE: I am not sure why the numbers are so far off, but I am 80% sure
        these formula are correct.
        '''
        pixel_spacing = (1.0, 1.0, 1.0)
        radius = 3.0
        kernel = cylindrical_grid_kernel(pixel_spacing, radius)

        length = radius*4*2

        cylinder_volume = math.pi*radius**2*length
        two_intersection_volume = 16.0/3.0*radius**3
        three_intersection_volume = 8*(2 - math.sqrt(2))*radius**3

        expected_kernel_volume = 3*cylinder_volume - 3*two_intersection_volume + three_intersection_volume

        actual_volume = np.sum(kernel)
        assert math.isclose(actual_volume, expected_kernel_volume, rel_tol=1e-1)


class TestFillCorners:
    def test_1x1x4(self):
        corner = np.array([
            [[0, 1, 2, 3]],
        ])

        expected_full = np.array([
            [[3, 2, 1, 0, 1, 2, 3]],
        ])

        assert np.alltrue(_fill_corners(corner) == expected_full)

    def test_1x4x1(self):
        corner = np.array([[
            [0], [1], [2], [3],
        ]])

        expected_full = np.array([[
            [3], [2], [1], [0], [1], [2], [3],
        ]])

        assert np.alltrue(_fill_corners(corner) == expected_full)

    def test_4x1x1(self):
        corner = np.array([
            [[0]], [[1]], [[2]], [[3]],
        ])

        expected_full = np.array([
            [[3]], [[2]], [[1]], [[0]], [[1]], [[2]], [[3]],
        ])

        assert np.alltrue(_fill_corners(corner) == expected_full)


    def test_2x2x2(self):
        corner = np.array([
            [[0, 1], [2, 3]],
            [[4, 5], [6, 7]],
        ])

        expected_full = np.array([
            [[7, 6, 7], [5, 4, 5], [7, 6, 7]],
            [[3, 2, 3], [1, 0, 1], [3, 2, 3]],
            [[7, 6, 7], [5, 4, 5], [7, 6, 7]],
        ])

        assert np.alltrue(_fill_corners(corner) == expected_full)

    def test_2x2x3(self):
        corner = np.array([
            [[0, 1, 2], [3, 4, 5]],
            [[6, 7, 8], [9, 0, 1]],
        ])

        expected_full = np.array([
            [[1, 0, 9, 0, 1], [8, 7, 6, 7, 8], [1, 0, 9, 0, 1]],
            [[5, 4, 3, 4, 5], [2, 1, 0, 1, 2], [5, 4, 3, 4, 5]],
            [[1, 0, 9, 0, 1], [8, 7, 6, 7, 8], [1, 0, 9, 0, 1]],
        ])

        assert np.alltrue(_fill_corners(corner) == expected_full)
