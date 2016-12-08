from collections import OrderedDict

import scipy.io
import matplotlib.pyplot as plt
import glob
import numpy as np

from hdatt.suite import Suite
from feature_detection import FeatureDetector
from test_utils import populate_base_context, get_test_data_generators, load_voxels
import slicer


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        data_generators = get_test_data_generators()
        cases = {
            '.'.join(data_generator.description): {
                'voxels': data_generator.output_data_prefix+'-voxels.mat',
                'points': data_generator.output_data_prefix+'-points.mat',
            }
            for data_generator in data_generators
        }
        return cases

    def run(self, case_input):
        voxels, ijk_to_xyz_transform = load_voxels(case_input['voxels'])
        feature_detector = FeatureDetector(voxels, ijk_to_xyz_transform)
        points = feature_detector.run()

        golden_points = scipy.io.loadmat(case_input['points'])['points']
        metrics, context = populate_base_context(case_input, golden_points, points)
        context['label_image'] = feature_detector.label_image
        context['preprocessed_image'] = feature_detector.preprocessed_image
        context['feature_image'] = feature_detector.feature_image
        context['kernel'] = feature_detector.kernel

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
        kernel_big[:kernel_shape[0], :kernel_shape[1], :kernel_shape[2]] = kernel_small*np.max(context['feature_image'])

        s = slicer.PointsSlicer(context['feature_image'], ijk_to_xyz, descriptors)
        s.add_renderer(slicer.render_slices)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.build_render_overlay(context['label_image'] > 0, [0, 1, 0]))
        s.add_renderer(slicer.build_render_overlay(kernel_big, [1, 0, 0]))
        s.add_renderer(slicer.render_cursor)
        s.draw()
        plt.show()
