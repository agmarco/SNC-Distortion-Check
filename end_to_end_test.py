from collections import OrderedDict

import numpy as np
import scipy
import scipy.io
from scipy.interpolate.interpnd import LinearNDInterpolator

import affine
from affine import translation_rotation
from feature_detection import detect_features
from hdatt.suite import Suite
from registration import register
from reports import compute_matches
from test_utils import get_test_data_generators, Rotation, show_base_result, populate_base_context, Distortion, \
    load_voxels, load_points

class EndToEndTestSuite(Suite):
    id = 'EndToEnd'

    def collect(self):
        data_generators = get_test_data_generators()
        rotation_and_distortion_generators = [data_generator for data_generator in data_generators if type(data_generator) == Rotation and type(data_generator.input_test_data) == Distortion]
        cases = {
            '.'.join(data_generator.description): {
                'rotation_deg': float(data_generator.rotation_deg),
                'distorted_and_rotated_voxels': data_generator.output_data_prefix+'_voxels.mat',
                'distorted_and_rotated_points': data_generator.output_data_prefix+'_points.mat',
                'source_voxels': data_generator.source.output_data_prefix+'_voxels.mat',
                'source_points': data_generator.source.output_data_prefix+'_points.mat',
            }
            for data_generator in rotation_and_distortion_generators
        }
        return cases

    def run(self, case_input):
        voxels, ijk_to_xyz_transform = load_voxels(case_input['distorted_and_rotated_voxels'])
        golden_points = load_points(case_input['source_points'])
        rotation_rad = np.deg2rad(case_input['rotation_deg'])
        rotation_mat = translation_rotation(0, 0, 0, rotation_rad, rotation_rad, rotation_rad)
        rotated_golden_points = affine.apply_affine(rotation_mat, golden_points)
        rotated_distorted_golden_points = scipy.io.loadmat(case_input['distorted_and_rotated_points'])['points']

        detected_points = detect_features(voxels, ijk_to_xyz_transform)

        # TODO: determine rho and g based on our knowledge of the phantom
        g = lambda bmag: 1.0
        rho = lambda bmag: 15.0
        measured_xyz_tpx = np.array(register(golden_points, rotated_distorted_golden_points, rho, g, 1e-6))
        a_to_b_registration_matrix = affine.translation_rotation(*measured_xyz_tpx)
        registered_golden_points = affine.apply_affine(a_to_b_registration_matrix, golden_points)
        TP_A, TP_B = compute_matches(registered_golden_points, detected_points, min_mm=10)
        detected_error_vecs = (TP_A - TP_B)

        interpolator = LinearNDInterpolator(TP_A, detected_error_vecs)
        golden_error_vecs = (rotated_golden_points - rotated_distorted_golden_points).T
        deviation_magnitude_from_golden = np.linalg.norm(interpolator(rotated_golden_points.T) - golden_error_vecs, axis=1)
        nan_index = np.isnan(deviation_magnitude_from_golden)
        deviation_magnitude_from_golden_99 = np.percentile(deviation_magnitude_from_golden[~nan_index], 99)
        num_nans = np.sum(np.isnan(deviation_magnitude_from_golden))
        deviation_magnitude_from_golden[nan_index] = deviation_magnitude_from_golden_99

        _, context = populate_base_context(case_input, rotated_golden_points, registered_golden_points)
        metrics = OrderedDict()
        metrics['mean_normalized_error'] = np.mean(deviation_magnitude_from_golden)
        metrics['nan_fraction'] = num_nans/len(deviation_magnitude_from_golden)
        return metrics, context

    def verify(self, old_metrics, new_metrics):
        # TODO Implement this.
        pass

    def show(self, result):
        show_base_result(result, voxels_key='distorted_and_rotated_voxels')

    def diff(self, golden_result, result):
        assert golden_result['case_input']['images'] == result['case_input']['images']
