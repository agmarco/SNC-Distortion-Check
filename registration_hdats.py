from collections import OrderedDict

import numpy as np
import scipy
import scipy.io

from hdatt.suite import Suite
from registration import rigidly_register
from test_utils import get_test_data_generators, Rotation, show_base_result
import affine


class RegistrationSuite(Suite):
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
        measured_xyz_tpx = np.array(rigidly_register(golden_points, rotated_points, rho, g, 1e-6))

        a_to_b_registration_matrix = affine.translation_rotation(*measured_xyz_tpx)
        registered_points = affine.apply_affine(a_to_b_registration_matrix, golden_points)
        diff_xyz_tpx = np.abs(measured_xyz_tpx - expected_xyz_tpx)

        context = OrderedDict()
        context['case_input'] = case_input

        FN_A, TP_A, TP_B, FP_B = points_utils.categorize(rotated_points, registered_points, rho)
        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

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
