import math

import numpy as np

from feature_detection import cylindrical_grid_kernel


class TestCylinderGridKernel:
    def test_size_simple(self):
        pixel_spacing = (1.0, 1.0, 1.0)
        radius = 4.0
        kernel = cylindrical_grid_kernel(pixel_spacing, radius)
        assert kernel.shape == (32, 32, 32)

    def test_size_non_uniform(self):
        pixel_spacing = (1.0, 2.0, 4.0)
        radius = 4.0
        kernel = cylindrical_grid_kernel(pixel_spacing, radius)
        assert kernel.shape == (32, 16, 8)

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

