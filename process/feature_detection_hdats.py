from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt
import numpy as np

from process import affine
from . import file_io
from . import points_utils
from . import slicer
from .slicer_fp_rejector import render_intersection_square
from . import affine
from .fp_rejector import remove_fps
from hdatt.suite import Suite
from .feature_detection import FeatureDetector
from .visualization import scatter3


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        cases = {
            '001': {
                'voxels': 'tmp/001_ct_603A_E3148_ST1.25-voxels.mat',
                'points': 'data/points/001_ct_603A_E3148_ST1.25-golden.mat',
            },
            '006': {
                'voxels': 'tmp/006_mri_603A_UVA_Axial_2ME2SRS5-voxels.mat',
                'points': 'data/points/006_mri_603A_UVA_Axial_2ME2SRS5-golden.mat',
            },
            '010': {
                'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
                'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
            },
            '011': {
                'voxels': 'tmp/011_mri_603A_arterial_TOF_3d_motsa_ND-voxels.mat',
                'points': 'data/points/011_mri_630A_arterial_TOF_3d_motsa_ND-golden.mat',
            },
            # TODO: determine if we care about the 1540 data sets
            # '1540-075': {
                # 'voxels': 'tmp/xxx_ct_1540_ST075-120kVp-100mA-voxels.mat',
                # 'points': 'data/points/1540-gaussian.mat',
            # },
            # '1540-125': {
                # 'voxels': 'tmp/xxx_ct_1540_ST125-120kVp-100mA-voxels.mat',
                # 'points': 'data/points/1540-gaussian.mat',
            # },
            # '1540-250': {
                # 'voxels': 'tmp/xxx_ct_1540_ST250-120kVp-100mA-voxels.mat',
                # 'points': 'data/points/1540-gaussian.mat',
            # },
        }
        return cases

    def run(self, case_input):
        golden_points = file_io.load_points(case_input['points'])['points']

        metrics = OrderedDict()
        context = OrderedDict()

        context['case_input'] = case_input

        voxel_data = file_io.load_voxels(case_input['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_xyz']
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
        phantom_model = voxel_data['phantom_model']
        modality = voxel_data['modality']

        feature_detector = FeatureDetector(phantom_model, modality, voxels, ijk_to_xyz)

        context['phantom_model'] = phantom_model
        context['label_image'] = feature_detector.label_image
        context['preprocessed_image'] = feature_detector.preprocessed_image
        context['feature_image'] = feature_detector.feature_image
        context['kernel'] = feature_detector.kernel
        context['voxel_spacing'] = voxel_spacing

        rho = lambda bmag: 2.5
        metrics['raw'], context['raw'] = self._process_points(
                golden_points, feature_detector.points_xyz, rho)

        points_ijk = feature_detector.points_ijk

        pruned_points_ijk = remove_fps(points_ijk, voxels, voxel_spacing, phantom_model)

        pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)
        metrics['pruned'], context['pruned'] = self._process_points(
                golden_points, pruned_points_xyz, rho)

        return metrics, context

    def _process_points(self, golden_points, points, rho):
        metrics = OrderedDict()
        context = OrderedDict()

        FN_A, TP_A, TP_B, FP_B = points_utils.categorize(golden_points, points, rho)

        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        TPF, FPF, FLE_percentiles = points_utils.metrics(FN_A, TP_A, TP_B, FP_B)
        metrics['TPF'] = TPF
        metrics['FPF'] = FPF

        for p in [0, 25, 50, 75, 95, 99, 100]:
            metrics['FLE_{}'.format(p)] = FLE_percentiles[p]

        return metrics, context

    def _print_metrics(self, metrics):
        print('BEFORE FP-REJECTOR DETECTION')
        self._print_points_metrics(metrics['raw'])
        print('AFTER FP-REJECTOR DETECTION')
        self._print_points_metrics(metrics['pruned'])

    def _print_points_metrics(self, point_cloud_comparison_metrics):
        for k, v in point_cloud_comparison_metrics.items():
            if k.startswith('FLE_'):
                print(points_utils.format_FLE_percentile(v))
            else:
                print("{} = {:06.4f}".format(k, v))

    def verify(self, old_metrics, new_metrics):
        new_TPF = new_metrics['pruned']['TPF']
        old_TPF = old_metrics['pruned']['TPF']
        if new_TPF < old_TPF:
            return False, f'The TPF has decreased from {old_TPF} to {new_TPF}'

        new_FPF = new_metrics['pruned']['FPF']
        old_FPF = old_metrics['pruned']['FPF']
        if new_FPF > old_FPF:
            return False, f"The FPF has increased from {old_FPF} to {new_FPF}"

        new_FLE_100 = new_metrics['pruned']['FLE_100']['r']
        old_FLE_100 = old_metrics['pruned']['FLE_100']['r']
        old_FPF = old_metrics['pruned']['FPF']
        if new_FLE_100 > old_FLE_100:
            return False, f"The maximum FLE increased from {old_FLE_100} to {new_FLE_100}."

        return True, 'The results seem as good or better than the existing results'

    def show(self, result):
        self._print_metrics(result['metrics'])

        context = result['context']

        descriptors = [
            {
                'points_xyz': context['pruned']['FN_A'],
                'scatter_kwargs': {
                    'color': 'y',
                    'label': 'False Negatives',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['pruned']['TP_B'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'True Positives',
                    'marker': 'x'
                }
            },
            {
                'points_xyz': context['pruned']['FP_B'],
                'scatter_kwargs': {
                    'color': 'r',
                    'label': 'False Positives',
                    'marker': 'x'
                }
            },
        ]

        voxel_data = file_io.load_voxels(context['case_input']['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_xyz']
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
        phantom_model = voxel_data['phantom_model']

        kernel_big = np.zeros_like(voxels)
        kernel_small = context['kernel']
        kernel_shape = kernel_small.shape

        slices = []
        for n_image, n_kernel in zip(voxels.shape, kernel_small.shape):
            assert n_image > n_kernel, 'Image should be bigger than the kernel'
            start = round(n_image/2 - n_kernel/2)
            stop = start + n_kernel
            slices.append(slice(start, stop))

        kernel_big[slices] = kernel_small*np.max(context['feature_image'])

        s = slicer.PointsSlicer(context['preprocessed_image'], ijk_to_xyz, descriptors)
        s.add_renderer(slicer.render_overlay(context['feature_image']), hidden=True)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_translucent_overlay(
            context['label_image'] > 0,
            [0, 1, 0]
        ))
        s.add_renderer(slicer.render_translucent_overlay(kernel_big, [1, 0, 0]))
        s.add_renderer(partial(render_intersection_square, voxels, voxel_spacing, phantom_model))
        s.add_renderer(slicer.render_cursor)
        s.draw()
        plt.show()
