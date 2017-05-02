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
from .dicom_import import combined_series_from_zip


class FullAlgorithmSuite(Suite):
    id = 'full-algorithm'

    def collect(self):
        return {
            'demo': {
                'dicom': 'data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip',
                'golden_points': 'data/points/603A.mat',
                'modality': 'mri',
                'phantom_name': '603A',
            }
        }

    def run(self, case_input):
        golden_points = file_io.load_points(case_input['golden_points'])['points']

        # 0. generate voxel data from zip file
        voxels, ijk_to_xyz = combined_series_from_zip(case_input['dicom'])
        phantom_name = case_input['phantom_name']
        modality = case_input['modality']

        # 1. feature detector
        # 2. fp rejector
        detected_points = FeatureDetector(phantom_name, modality, voxels, ijk_to_xyz).run()

        # 3. rigidly register
        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
            golden_points,
            rotated_distorted_golden_points
        )

        # 4. interpolate
        # 5. make assertions about the interpolated values

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        pass

    def show(self, result):
        pass

    def diff(self, golden_result, result):
        pass
