import os
from collections import OrderedDict

import numpy as np
import scipy.io
import dicom

from hdatt.suite import Suite
from feature_detection import detect_features
from dicom_import import combine_slices
from points import categorize
from overlaypoints import overlay_points


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        return {
            'mri-001-axial': {
                'images': './data/dicom/mri-001-axial',
                'golden': './data/points/mri-001-axial-golden.mat',
            }
        }

    def _load_images(self, images):
        image_dir = os.path.abspath(images)
        input_dicom_filenames = [os.path.join(image_dir, p) for p in os.listdir(image_dir)]
        dicom_datasets = [dicom.read_file(f) for f in input_dicom_filenames]
        return combine_slices(dicom_datasets)

    def run(self, case_input):
        metrics = OrderedDict()
        context = {}

        voxels, ijk_to_xyz_transform = self._load_images(case_input['images'])
        points = detect_features(voxels, ijk_to_xyz_transform)

        golden_points = scipy.io.loadmat(case_input['golden'])['points']
        FN_A, TP_A, TP_B, FP_B = categorize(golden_points, points, lambda bmag: 7.5)

        context['case_input'] = case_input
        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        total_error, average_error, random_error_average, TPF, FNF = points.metrics(FN_A, TP_A, TP_B, FP_B)
        metrics['total_error'] = total_error
        metrics['average_error'] = average_error
        metrics['random_error_average'] = random_error_average
        metrics['true_positive_fraction'] = true_positive_fraction
        metrics['false_negative_fraction'] = false_negative_fraction

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
            {'points_xyz': context['FN_A'], 'scatter': {'color': 'y', 'label': 'FN_A', 'marker': 'o'}},
            {'points_xyz': context['TP_A'], 'scatter': {'color': 'g', 'label': 'TP_A', 'marker': 'o'}},
            {'points_xyz': context['TP_B'], 'scatter': {'color': 'g', 'label': 'TP_B', 'marker': 'x'}},
            {'points_xyz': context['FP_B'], 'scatter': {'color': 'r', 'label': 'FP_B', 'marker': 'x'}},
        ]

        voxels, ijk_to_xyz_transform = self._load_images(context['case_input']['images'])
        overlay_points(voxels, ijk_to_xyz_transform, descriptors)

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
