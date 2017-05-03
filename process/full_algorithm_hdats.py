from collections import OrderedDict

import numpy as np
from scipy.interpolate.interpnd import LinearNDInterpolator
import matplotlib.pyplot as plt

from . import points_utils
from hdatt.suite import Suite
from . import slicer
from . import affine, file_io
from .fp_rejector import remove_fps
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
        metrics = OrderedDict()
        context = OrderedDict()

        golden_points = file_io.load_points(case_input['golden_points'])['points']
        context['A'] = golden_points

        # 0. generate voxel data from zip file
        voxels, ijk_to_xyz = combined_series_from_zip(case_input['dicom'])
        phantom_name = case_input['phantom_name']
        modality = case_input['modality']
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)

        context['ijk_to_xyz'] = ijk_to_xyz

        # 1. feature detector
        feature_detector = FeatureDetector(phantom_name, modality, voxels, ijk_to_xyz)
        feature_detector.run()

        context['preprocessed_image'] = feature_detector.preprocessed_image

        # 2. fp rejector
        pruned_points_ijk = remove_fps(feature_detector.points_ijk, voxels, voxel_spacing)
        pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

        # 3. rigidly register
        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
            golden_points,
            pruned_points_xyz
        )

        x, y, z, theta, phi, xi = xyztpx

        context['x'] = x
        context['y'] = y
        context['z'] = z
        context['theta'] = theta
        context['phi'] = phi
        context['xi'] = xi

        metrics['registration_shift'] = np.sqrt(x*x + y*y + z*z)
        # TODO: add a metric for the angle change

        context['FN_A_S'] = FN_A_S
        context['TP_A_S'] = TP_A_S
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        # 4. interpolate
        # 5. make assertions about the interpolated values

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        pass

    def show(self, result):
        metrics = result['metrics']
        context = result['context']

        print(metrics)

        descriptors = [
            {
                'points_xyz': context['A'],
                'scatter_kwargs': {
                    'color': 'b',
                    'label': 'A',
                    'marker': 's'
                }
            },
            {
                'points_xyz': context['FN_A_S'],
                'scatter_kwargs': {
                    'color': 'y',
                    'label': 'FN_A_S',
                    'marker': 'x'
                }
            },
            {
                'points_xyz': context['TP_A_S'],
                'scatter_kwargs': {
                    'color': 'y',
                    'label': 'TP_A_s',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['TP_B'],
                'scatter_kwargs': {
                    'color': 'm',
                    'label': 'TP_B',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['FP_B'],
                'scatter_kwargs': {
                    'color': 'm',
                    'label': 'FP_B',
                    'marker': 'o'
                }
            },
        ]

        s = slicer.PointsSlicer(context['preprocessed_image'], context['ijk_to_xyz'], descriptors)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_cursor)
        s.draw()
        plt.show()
