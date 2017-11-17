import unittest
import math
from math import cos, sin, radians, sqrt
from itertools import product

import numpy as np
import pytest
from numpy.testing import assert_allclose

from process.affine import apply_xyztpx
from process.registration import build_objective_function, rigidly_register, \
        rigidly_register_and_categorize, registeration_tolerance, grid_search
from process.file_io import load_points


def grid3x3x3(delta):
    unit_grid_list = [
        [x, y, z]
        for x, y, z
        in product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1])
    ]
    return np.array(unit_grid_list, dtype=np.double).T*delta

def grid5x5x5(delta):
    unit_grid_list = [
        [x, y, z]
        for x, y, z
        in product([-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2])
    ]
    return np.array(unit_grid_list, dtype=np.double).T*delta


class TestSimpleObjectiveFunction(unittest.TestCase):
    def setUp(self):
        B = np.array([[0, 0, 0], [0, 0, 1]], dtype=float).T
        A = np.array([[0, 0, 0]], dtype=float).T
        self.g = lambda bmag: 1.0 - bmag/100.0
        self.rho = lambda bmag: 2.0
        self.f = build_objective_function(A, B, self.g, self.rho)

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
        expected_value = self.g(0)*((0.5)/self.rho(0) - 1)
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
        assert self.f([0, 0, 0.5, 0, 0, 0]) == self.g(0)*((0.5)/self.rho(0) - 1.0)
        actual = self.f([0, 0, 0.5001, 0, 0, 0])
        expected = self.g(1.0)*((1 - 0.5001)/self.rho(1.0) - 1.0)
        assert_allclose(actual, expected)


@pytest.mark.slow
class TestRegistrationPerfectMatch:
    def assert_5x5x5_match(self, xyztpx):
        grid_spacing = 20
        A = grid5x5x5(grid_spacing)
        B = apply_xyztpx(xyztpx, A)

        tolerance = 1e-5
        xyztpx_actual = rigidly_register(A, B, grid_spacing, tolerance)

        assert_allclose(xyztpx_actual, xyztpx, atol=tolerance*10)

    def test_small_translation(self):
        self.assert_5x5x5_match([0.4, -0.3, 0.3, 0, 0, 0])

    def test_big_translation(self):
        self.assert_5x5x5_match([24.4, -2.3, 1.3, 0, 0, 0])

    def test_big_translation_and_rotation(self):
        self.assert_5x5x5_match([4.4, -32.3, 1.3, radians(5), -radians(5), radians(3)])

    def test_rotation(self):
        self.assert_5x5x5_match([0, 0, 0, radians(2), -radians(1), radians(2)])


class TestRegisterAndCategorize:
    def assert_3x3x3_match(self, xyztpx, isocenter):
        grid_spacing = 20
        A = grid3x3x3(grid_spacing)
        B = apply_xyztpx(xyztpx, A)
        A_S = B  # since this is an idealized case

        isocenter = np.array(isocenter)

        tolerance = 1e-6
        xyztpx_actual, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                A, B, grid_spacing, isocenter)

        assert_allclose(xyztpx_actual, xyztpx, atol=tolerance*10)
        assert_allclose(TP_A_S, A_S, atol=tolerance*10)
        assert_allclose(TP_B, B, atol=tolerance*10)
        assert FN_A_S.size == 0
        assert FP_B.size == 0

    def test_small_translation_isocenter_at_origin(self):
        self.assert_3x3x3_match([0.4, -0.3, 0.3, 0, 0, -radians(5)], [0, 0, 0])

    def test_small_translation_isocenter_shifted(self):
        self.assert_3x3x3_match([32 + 0.4, -10 + -0.3, 22 + 0.3, 0, 0, 0], [32, -10, 22])

    def test_shifts_multiple_times_no_rotation(self):
        self.assert_3x3x3_match([2, 1, -1, 0, 0, 0], [0, 0, 0])

    def test_points_beyond_g_cutoff_are_ignored(self):
        '''
        This test is a sanity check, to make sure our `g` function is working
        properly.

        All of the points close to the isocenter (within g_cutoff) have a shift
        of (0, 0, 0.1), while the points outside the cutoff don't have a shift.
        '''
        grid_spacing = 1.0

        A = np.array([
            [0, 0, 2.0],
            [0, 0, 3.0],
            [0, 0, 10*grid_spacing + 11.0],
            [0, 0, 10*grid_spacing + 12.0],
            [0, 0, 10*grid_spacing + 13.0]
        ]).T

        B = np.array([
            [0, 0, 2.1],
            [0, 0, 3.1],
            [0, 0, 10*grid_spacing + 11.0],
            [0, 0, 10*grid_spacing + 12.0],
            [0, 0, 10*grid_spacing + 13.0]
        ]).T

        isocenter = np.array([0, 0, 0])

        tolerance = 1e-5
        xyztpx_actual, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                A, B, grid_spacing, isocenter)
        x, y, z, _, _, _ = xyztpx_actual
        assert math.isclose(x, 0, abs_tol=registeration_tolerance)
        assert math.isclose(y, 0, abs_tol=registeration_tolerance)
        assert math.isclose(z, 0.1, abs_tol=registeration_tolerance)

    def test_points_near_isocenter_weighted_more(self):
        '''
        This test is a sanity check, to make sure our `g` function is working
        properly.

        All of the points close to the isocenter have a shift
        of (0, 0, -1), while the points outside the cutoff don't have a shift.
        '''
        A = np.array([[0, 0, -1], [0, 0, 0.0], [0, 0, 1.0]]).T
        B = np.array([[0, 0, -1.1 + 2], [0, 0, 0.0 + 2], [0, 0, 1.1 + 2]]).T
        isocenter = np.array([0, 0, 0])
        grid_spacing = 1.0

        tolerance = 1e-5
        xyztpx_actual, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                A, B, grid_spacing, isocenter)
        x, y, z, _, _, _ = xyztpx_actual
        assert math.isclose(x, 0, abs_tol=registeration_tolerance)
        assert math.isclose(y, 0, abs_tol=registeration_tolerance)
        assert math.isclose(z, +2, abs_tol=registeration_tolerance)


@pytest.mark.parametrize("initial_xyztpx,expected_xyz", [
    ([1.0, 1.0, 1.0, 0.0, 0, 0], [0.0, 0, 0]),
    ([4, -3.0, 4.0, 0, 0, 0], [0.0, 0, 0]),
    ([0.1, -3, 4, 0, 0, 0], [0.1, 0, 0]),
    ([0, 0, 0, radians(12), 0, 0], [0, 0, 0]),
    ([1.0, 1.0, 0, 0, 0, radians(12)], [1 - cos(radians(12)) + sin(radians(12)), 1 - cos(radians(12)) - sin(radians(12)), 0]),
    ([sqrt(2)/2, sqrt(2)/2, 0, 0, 0, radians(45)], [0, 0, 0]),
    ([sqrt(2)/2, 0, sqrt(2)/2, 0, -radians(45), 0], [0, 0, 0]),
    ([0, sqrt(2)/2, sqrt(2)/2, radians(45), 0, 0], [0, 0, 0]),
])
def test_grid_search(initial_xyztpx, expected_xyz):
    def f(xyztpx):
        x, y, z, theta, phi, xi = xyztpx
        return (1 + x*x)*(1 + y*y)*(1 + z*z)
    grid_spacing = 1.0
    final_xyztpx = grid_search(f, grid_spacing, np.array(initial_xyztpx))
    assert_allclose(final_xyztpx, np.array(expected_xyz + initial_xyztpx[3:]), atol=1e-5)
