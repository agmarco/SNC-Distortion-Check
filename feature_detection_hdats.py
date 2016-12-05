from collections import OrderedDict

import scipy.io
import matplotlib.pyplot as plt
import glob

from hdatt.suite import Suite
from feature_detection import FeatureDetector
from test_utils import populate_base_context, get_test_data_generators, show_base_result, load_voxels


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        data_generators = get_test_data_generators()
        cases = {
            '.'.join(data_generator.description): {
                'voxels': data_generator.output_data_prefix+'_voxels.mat',
                'points': data_generator.output_data_prefix+'_points.mat',
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
        show_base_result(result)

    def diff(self, golden_result, result):
        assert golden_result['case_input']['images'] == result['case_input']['images']

        # TODO: finish this
        # case_input = result['case_input']

        # context = result['context']
        # golden_context = golden_result['context']
        # descriptors = [
            # {'points_xyz': context['FN_A'], 'scatter': {'color': 'y', 'label': 'FN_A', 'marker': 'o'}},
            # {'points_xyz': context['TP_A'], 'scatter': {'color': 'g', 'label': 'TP_A', 'marker': 'o'}},
            # {'points_xyz': context['TP_B'], 'scatter': {'color': 'g', 'label': 'TP_B', 'marker': 'x'}},
            # {'points_xyz': context['FP_B'], 'scatter': {'color': 'r', 'label': 'FP_B', 'marker': 'x'}},
        # ]

        # voxels, ijk_to_xyz_transform = self._load_images(case_input)
        # overlay_points(voxels, ijk_to_xyz_transform, descriptors)
