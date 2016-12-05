from collections import OrderedDict
from math import pi
import unittest

import pytest
import numpy as np
from numpy.testing import assert_allclose

import affine
from registration import build_f, register
from affine import apply_xyztpx


@pytest.fixture
def grid5x5x5():
    A = []
    Delta = 20
    for x in range(-2*Delta, 2*Delta + 1, Delta):
        for y in range(-2*Delta, 2*Delta + 1, Delta):
            for z in range(-2*Delta, 2*Delta + 1, Delta):
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


class TestRegistrationPerfectMatch:
    def assert_5x5x5_match(self, xyztpx):
        A = grid5x5x5()
        B = apply_xyztpx(xyztpx, A)

        g = lambda bmag: 1.0
        rho = lambda bmag: 10.0

        tolerance = 1e-5
        xyztpx_actual = register(A, B, g, rho, tolerance)

        assert_allclose(xyztpx_actual, xyztpx, atol=tolerance*10)

    def test_small_translation(self):
        self.assert_5x5x5_match([0.4, -0.3, 0.3, 0, 0, 0])

    def test_big_translation(self):
        self.assert_5x5x5_match([4.4, -6.3, 5.3, 0, 0, 0])

    def test_rotation(self):
        self.assert_5x5x5_match([0, 0, 0, pi/180*2, -pi/180*5, pi/180*3])


class RegistrationTestSuite(Suite):
    id = 'registration'

    def collect(self):
        data_generators = get_test_data_generators()
        rotation_generators = [data_generator for data_generator in data_generators if type(data_generator) == Rotation]
        cases = {
            '.'.join(data_generator.description): {
                'rotation_deg': data_generator.rotation_deg,
                'voxels': data_generator.output_data_prefix+'_voxels.mat',
                'points': data_generator.output_data_prefix+'_points.mat',
                'source_points': data_generator.source.output_data_prefix+'_points.mat'
            }
            for data_generator in rotation_generators
        }
        return cases

    def run(self, case_input):
        golden_points = scipy.io.loadmat(case_input['source_points'])['points']
        rotated_points = scipy.io.loadmat(case_input['points'])['points']
        rotation_deg = float(case_input['rotation_deg'])
        rotation_rad = np.deg2rad(rotation_deg)
        expected_xyz_tpx = np.array((0, 0, 0, rotation_rad, rotation_rad, rotation_rad))

        # TODO: determine rho and g based on our knowledge of the phantom
        g = lambda bmag: 1.0
        rho = lambda bmag: 15.0
        measured_xyz_tpx = np.array(register(golden_points, rotated_points, rho, g, 1e-6))

        a_to_b_registration_matrix = affine.translation_rotation(*measured_xyz_tpx)
        registered_points = affine.apply_affine(a_to_b_registration_matrix, golden_points)
        diff_xyz_tpx = np.abs(measured_xyz_tpx - expected_xyz_tpx)
        _, context = populate_base_context(case_input, rotated_points, registered_points)
        metrics = OrderedDict()
        metrics['d_x'], metrics['d_y'], metrics['d_z'], metrics['d_theta'], metrics['d_pi'], metrics['d_xi'] = diff_xyz_tpx
        return metrics, context

    def verify(self, old_metrics, new_metrics):
        # TODO Implement this.
        pass

    def show(self, result):
        show_base_result(result)

    def diff(self, golden_result, result):
        assert golden_result['case_input']['images'] == result['case_input']['images']
