import unittest
from math import pi

import numpy as np
import pytest
from numpy.testing import assert_allclose

from process.affine import apply_xyztpx
from process.registration import build_f, rigidly_register, rigidly_register_and_categorize
from process.file_io import load_points


@pytest.fixture
def grid3x3x3():
    A = []
    Delta = 20
    for x in range(-Delta, Delta + 1, Delta):
        for y in range(-Delta, Delta + 1, Delta):
            for z in range(-Delta, Delta + 1, Delta):
                A.append((x, y, z))

    A = np.array(A, dtype=float).T
    m, mm = A.shape
    assert m == 3
    return A


class TestSimpleObjectiveFunction(unittest.TestCase):
    def setUp(self):
        B = np.array([[0, 0, 0], [0, 0, 1]], dtype=float).T
        A = np.array([[0, 0, 0]], dtype=float).T
        self.g = lambda bmag: 1.0 - bmag/100.0
        self.rho = lambda bmag: 2.0
        self.f = build_f(A, B, self.g, self.rho)

    def test_overlapping_points_no_shift(self):
        '''
        The first point in a overlaps with b.
        '''
        assert self.f([0, 0, 0, 0, 0, 0]) == -self.g(0.0)

    def test_overlapping_points_with_shift(self):
        '''
        With a shift of [0, 0, 1] the second point will overlap.
        '''
        assert self.f([0, 0, 1, 0, 0, 0]) == -self.g(1.0)

    def test_grabs_closest_point_at_rho(self):
        '''
        A shift in the -z direction will move the second point further away,
        and the first point right on the edge of rho.
        '''
        assert self.f([0, 0, -2, 0, 0, 0]) == 0

    def test_grabs_closest_point_at_half_rho(self):
        '''
        Moving the first point by 0.5 in any direction should result in a
        value that is "halfway out" of the cone.
        '''
        expected_value = self.g(0)*(0.5/self.rho(0) - 1)
        assert self.f([0, 0, -0.5, 0, 0, 0]) == expected_value
        assert self.f([0, 0.5, 0, 0, 0, 0]) == expected_value
        assert self.f([0, -0.5, 0, 0, 0, 0]) == expected_value
        assert self.f([0.5, 0, 0, 0, 0, 0]) == expected_value
        assert self.f([-0.5, 0, 0, 0, 0, 0]) == expected_value

    def test_rejects_multiple_points(self):
        '''
        This test ensures that each point in a is only matched with a single
        other point in B, and that the objective function properly determines
        which point should be matched even at the boundary conditions.

        If two points are equidistant, it should match the one with the higher g
        value, which in this case is g(0)
        '''
        assert self.f([0, 0, 0.5, 0, 0, 0]) == self.g(0)*(0.5/self.rho(0) - 1.0)
        assert_allclose(self.f([0, 0, 0.5001, 0, 0, 0]), self.g(1.0)*((1 - 0.5001)/self.rho(1.0) - 1.0))


@pytest.mark.slow
class TestRegistrationPerfectMatch:
    def assert_3x3x3_match(self, xyztpx):
        A = grid3x3x3()
        B = apply_xyztpx(xyztpx, A)

        g = lambda bmag: 1.0
        rho = lambda bmag: 10.0

        tolerance = 1e-5
        xyztpx_actual = rigidly_register(A, B, g, rho, tolerance)

        assert_allclose(xyztpx_actual, xyztpx, atol=tolerance*10)

    def test_small_translation(self):
        self.assert_3x3x3_match([0.4, -0.3, 0.3, 0, 0, 0])

    def test_big_translation(self):
        self.assert_3x3x3_match([4.4, -2.3, 1.3, 0, 0, 0])

    def test_rotation(self):
        self.assert_3x3x3_match([0, 0, 0, pi/180*2, -pi/180*1, pi/180*2])


class TestRegisterAndCategorize:
    def assert_3x3x3_match(self, xyztpx, isocenter):
        A = grid3x3x3()
        B = apply_xyztpx(xyztpx, A)
        A_S = B  # since this is an idealized case

        isocenter = np.array(isocenter)

        tolerance = 1e-5
        xyztpx_actual, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(A, B, isocenter_in_B=isocenter)

        # see TODO in affine next to
        #assert_allclose(xyztpx_actual, xyztpx, atol=tolerance*10)
        assert_allclose(TP_A_S, A_S, atol=tolerance*100)
        assert_allclose(TP_B, B, atol=tolerance*100)
        assert FN_A_S.size == 0
        assert FP_B.size == 0

    def test_small_translation_isocenter_at_origin(self):
        self.assert_3x3x3_match([0.4, -0.3, 0.3, 0, 0, -pi/180*5], [0, 0, 0])

    def test_small_translation_isocenter_shifted(self):
        self.assert_3x3x3_match([0.4, -0.3, 0.3, 0, 0, 0], [150, -50, 250])

    def test_small_rotation_isocenter_shifted(self):
        # NOTE: this test is very sensitive to the brute force search space
        self.assert_3x3x3_match([0, 0, 0, 0, 0, -pi/180*3], [150, -50, 250])
