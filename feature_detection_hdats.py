from collections import OrderedDict

import scipy.io
import matplotlib.pyplot as plt
import glob
import numpy as np

from hdatt.suite import Suite
from feature_detection import FeatureDetector
from test_utils import populate_base_context, get_test_data_generators, load_voxels
import slicer
import affine


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        # data_generators = get_test_data_generators()
        # cases = {
            # '.'.join(data_generator.description): {
                # 'voxels': data_generator.output_data_prefix+'-voxels.mat',
                # 'points': data_generator.output_data_prefix+'-points.mat',
            # }
            # for data_generator in data_generators
        # }

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
        }
        return cases

    def run(self, case_input):
        voxels, ijk_to_xyz_transform = load_voxels(case_input['voxels'])

        feature_detector = FeatureDetector(voxels, ijk_to_xyz_transform)

        points = feature_detector.run()
        golden_points = scipy.io.loadmat(case_input['points'])['points']

        metrics = OrderedDict()
        context = OrderedDict()

        FN_A, TP_A, TP_B, FP_B = points_utils.categorize(golden_points, points, lambda bmag: 1)
        context['case_input'] = case_input
        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B
        context['label_image'] = feature_detector.label_image
        context['preprocessed_image'] = feature_detector.preprocessed_image
        context['feature_image'] = feature_detector.feature_image
        context['kernel'] = feature_detector.kernel

        total_error, average_error, random_error_average, TPF, FNF, FPF = points_utils.metrics(FN_A, TP_A, TP_B, FP_B)
        metrics['total_error'] = total_error
        metrics['average_error'] = average_error
        metrics['random_error_average'] = random_error_average
        metrics['true_positive_fraction'] = true_positive_fraction
        metrics['false_negative_fraction'] = false_negative_fraction
        metrics['false_positive_fraction'] = false_negative_fraction

        print("FNF {:06.5f}, TPF {:06.5f}, RAE {:06.3f}".format(
            metrics['false_negative_fraction'],
            metrics['false_positive_fraction'],
            metrics['true_positive_fraction'],
            metrics['random_error_average'],
        ))

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        comments = []

        max_allowed_percent_change = 2.0

        passing = True
        for metric_name, new_value in new_metrics.items():
            try:
                old_value = old_metrics[metric_name]
            except KeyError:
                comments.append('Missing key in old metric: "{}"'.format(metric_name))
                passing = False
            percent_change = abs(old_value - new_value)/old_value*100.0
            if percent_change < max_allowed_percent_change:
                msg = 'Metric "{}" valid: {} -> {}'
                comments.append(msg.format(metric_name, old_value, new_value))
            else:
                passing = False
                msg = 'Metric "{}" invalid: {} -> {} ({:.2f}% change)'
                comments.append(msg.format(metric_name, old_value, new_value, percent_change))

        return passing, '\n' + '\n'.join(comments)

    def show(self, result):
        context = result['context']
        descriptors = [
            {'points_xyz': context['FN_A'], 'scatter_kwargs': {'color': 'y', 'label': 'FN_A', 'marker': 'o'}},
            {'points_xyz': context['TP_A'], 'scatter_kwargs': {'color': 'g', 'label': 'TP_A', 'marker': 'o'}},
            {'points_xyz': context['TP_B'], 'scatter_kwargs': {'color': 'g', 'label': 'TP_B', 'marker': 'x'}},
            {'points_xyz': context['FP_B'], 'scatter_kwargs': {'color': 'r', 'label': 'FP_B', 'marker': 'x'}},
        ]
        raw_voxels, ijk_to_xyz = load_voxels(context['case_input']['voxels'])

        kernel_big = np.zeros_like(raw_voxels)
        kernel_small = context['kernel']
        kernel_shape = kernel_small.shape

        slices = []
        for n_image, n_kernel in zip(raw_voxels.shape, kernel_small.shape):
            assert n_image > n_kernel, 'Image should be bigger than the kernel'
            start = round(n_image/2 - n_kernel/2)
            stop = start + n_kernel
            slices.append(slice(start, stop))

        kernel_big[slices] = kernel_small*np.max(context['feature_image'])

        s = slicer.PointsSlicer(context['feature_image'], ijk_to_xyz, descriptors)
        s.add_renderer(slicer.render_slices)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.build_render_overlay(context['label_image'] > 0, [0, 1, 0]))
        s.add_renderer(slicer.build_render_overlay(kernel_big, [1, 0, 0]))
        s.add_renderer(slicer.render_cursor)
        s.draw()
        plt.show()
