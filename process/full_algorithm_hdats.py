from collections import OrderedDict

import numpy as np
from scipy.interpolate.interpnd import LinearNDInterpolator
import matplotlib.pyplot as plt

from . import points_utils, phantoms, slicer, affine, file_io
from .utils import fov_center_xyz
from .visualization import scatter3
from .interpolate import interpolate_distortion
from hdatt.suite import Suite
from .fp_rejector import remove_fps
from .affine import rotation_translation
from .feature_detection import FeatureDetector
from .registration import rigidly_register_and_categorize
from .test_utils import get_test_data_generators, Rotation, show_base_result, Distortion
from .dicom_import import combined_series_from_zip


def print_histogram(data, suffix):
    counts, bin_edges = np.histogram(data[np.isfinite(data)])
    total = np.sum(counts)
    for i, c in enumerate(counts):
        template = '{0:5.3f}{suffix} - {1:5.3f}{suffix}: {2:3.2f}%'
        print(template.format(bin_edges[i], bin_edges[i + 1], c/total*100, suffix=suffix))


class FullAlgorithmSuite(Suite):
    id = 'full-algorithm'

    def collect(self):
        return {
            '603A-2': {
                'dicom': 'data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '603A-4': {
                'dicom': 'data/dicom/yyy_mri_603A_t1_vibe_tra_FS_ND.zip',
                'modality': 'mri',
                'phantom_model': '603A',
            }
        }

    def run(self, case_input):
        metrics = OrderedDict()
        context = OrderedDict()

        golden_points_filename = phantoms.paramaters[case_input['phantom_model']]['points_file']
        golden_points = file_io.load_points(golden_points_filename)['points']
        context['A'] = golden_points

        # 0. generate voxel data from zip file
        voxels, ijk_to_xyz = combined_series_from_zip(case_input['dicom'])
        phantom_model = case_input['phantom_model']
        modality = case_input['modality']
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)

        context['ijk_to_xyz'] = ijk_to_xyz

        # 1. feature detector
        feature_detector = FeatureDetector(phantom_model, modality, voxels, ijk_to_xyz)

        context['preprocessed_image'] = feature_detector.preprocessed_image

        # 2. fp rejector
        points_ijk = feature_detector.points_ijk
        pruned_points_ijk = remove_fps(points_ijk, voxels, voxel_spacing, phantom_model)
        pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

        isocenter_in_B = fov_center_xyz(voxels.shape, ijk_to_xyz)

        # 3. rigidly register
        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
            golden_points,
            pruned_points_xyz,
            isocenter_in_B,
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
        distortion_grid = interpolate_distortion(TP_A_S, TP_B, ijk_to_xyz, voxels.shape)
        context['distortion_grid'] = distortion_grid

        # calculate metrics
        magnitude_mm = np.linalg.norm(distortion_grid, axis=3)
        is_nan = np.isnan(magnitude_mm)
        num_finite = np.sum(~is_nan)
        num_total = magnitude_mm.size

        metrics['fraction_of_volume_covered'] = num_finite/num_total
        metrics['max_distortion'] = np.nanmax(magnitude_mm)
        metrics['median_distortion'] = np.nanmedian(magnitude_mm)
        metrics['min_distortion'] = np.nanmin(magnitude_mm)

        print('histogram mm')
        print_histogram(magnitude_mm, 'mm')

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        pass

    def show(self, result):
        metrics = result['metrics']
        context = result['context']

        print('% volume: {:3.2f}%'.format(metrics['fraction_of_volume_covered']))
        print('max distortion magnitude: {:5.3f}mm'.format(metrics['max_distortion']))
        print('median distortion magnitude: {:5.3f}mm'.format(metrics['median_distortion']))
        print('min distortion magnitude: {:5.3f}mm'.format(metrics['min_distortion']))

        descriptors = [
            {
                'points_xyz': context['TP_B'],
                'scatter_kwargs': {
                    'color': 'm',
                    'label': 'Detected Points',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['FP_B'],
                'scatter_kwargs': {
                    'color': 'm',
                    'label': 'False Positives',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['FN_A_S'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'False Negatives',
                    'marker': 'x'
                }
            },
            {
                'points_xyz': context['TP_A_S'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Registered Golden Standard Points',
                    'marker': 's'
                }
            },
        ]

        distortion_magnitude = np.linalg.norm(context['distortion_grid'], axis=3)
        min_value = np.nanmin(distortion_magnitude)
        max_value = np.nanmax(distortion_magnitude)
        nan_value = min_value - 0.1*abs(max_value - min_value)
        distortion_magnitude[np.isnan(distortion_magnitude)] = nan_value

        s = slicer.PointsSlicer(context['preprocessed_image'], context['ijk_to_xyz'], descriptors)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_cursor)
        s.add_renderer(slicer.render_legend)
        s.add_renderer(slicer.render_overlay(distortion_magnitude, cmap='cool', alpha=0.8))
        s.draw()
        plt.show()

        scatter3({
            'FN_A_S': context['FN_A_S'],
            'TP_A_S': context['TP_A_S'],
            'TP_B': context['TP_B'],
            'FP_B': context['FP_B'],
        })
        plt.show()
