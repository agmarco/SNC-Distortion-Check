from collections import OrderedDict

import numpy as np
from scipy.interpolate.interpnd import LinearNDInterpolator

from . import points_utils
from hdatt.suite import Suite
from . import affine, file_io
from .affine import translation_rotation
from .feature_detection import FeatureDetector
from .registration import rigidly_register_and_categorize
from .test_utils import get_test_data_generators, Rotation, show_base_result, Distortion


class FullAlgorithmSuite(Suite):
    id = 'full-algorithm'

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
        voxel_data = file_io.load_voxels(case_input['distorted_and_rotated_voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
        phantom_name = voxel_data['phantom_name']
        modality = voxel_data['modality']

        golden_points = file_io.load_points(case_input['source_points'])['points']
        rotation_rad = np.deg2rad(case_input['rotation_deg'])
        rotation_mat = translation_rotation(0, 0, 0, rotation_rad, rotation_rad, rotation_rad)
        rotated_golden_points = affine.apply_affine(rotation_mat, golden_points)
        rotated_distorted_golden_points = file_io.load_points(case_input['distorted_and_rotated_points'])['points']

        detected_points = FeatureDetector(phantom_name, modality, voxels, ijk_to_xyz).run()

        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
            golden_points,
            rotated_distorted_golden_points
        )
        detected_error_vecs = TP_A_S - TP_B
        # TODO: fix + replace following code w general purpose function in the
        # util file

        interpolator = LinearNDInterpolator(TP_A, detected_error_vecs)
        golden_error_vecs = (rotated_golden_points - rotated_distorted_golden_points).T
        deviation_magnitude_from_golden = np.linalg.norm(interpolator(rotated_golden_points.T) - golden_error_vecs, axis=1)
        nan_index = np.isnan(deviation_magnitude_from_golden)
        deviation_magnitude_from_golden_99 = np.percentile(deviation_magnitude_from_golden[~nan_index], 99)
        num_nans = np.sum(np.isnan(deviation_magnitude_from_golden))
        deviation_magnitude_from_golden[nan_index] = deviation_magnitude_from_golden_99

        context = OrderedDict()

        FN_A, TP_A, TP_B, FP_B = points_utils.categorize(rotated_golden_points, registered_golden_points, rho)
        context['case_input'] = case_input
        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        metrics = OrderedDict()
        metrics['mean_target_registration_error'] = np.mean(deviation_magnitude_from_golden)
        metrics['nan_fraction'] = num_nans/len(deviation_magnitude_from_golden)

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        # TODO Implement this.
        pass

    def show(self, result):
        show_base_result(result, voxels_key='distorted_and_rotated_voxels')

    def diff(self, golden_result, result):
        assert golden_result['case_input']['images'] == result['case_input']['images']