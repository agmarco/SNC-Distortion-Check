import os

import numpy as np
import scipy.io
import dicom

from hdatt.suite import Suite
from feature_detection import detect_features
from dicom_import import combine_slices
from points import categorize


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        return {
            'mri-001-axial': {
                'images': './data/dicom/mri-001-axial',
                'golden': './data/points/mri-001-axial-golden.mat',
            }
        }

    def run(self, case_input):
        metrics = {}
        context = {}

        image_dir = os.path.abspath(case_input['images'])
        input_dicom_filenames = [os.path.join(image_dir, p) for p in os.listdir(image_dir)]
        dicom_datasets = [dicom.read_file(f) for f in input_dicom_filenames]
        voxels, ijk_to_patient_xyz_transform = combine_slices(dicom_datasets)
        points = detect_features(voxels, ijk_to_patient_xyz_transform)

        golden_points = scipy.io.loadmat(case_input['golden'])['points']
        FN_A, TP_A, TP_B, FP_B = categorize(golden_points, points, lambda bmag: 7.5)

        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        metrics['percent_false_negative'] = FN_A.shape[1]/(FN_A.shape[1] + TP_A.shape[1])*100
        metrics['percent_false_positive'] = FP_B.shape[1]/(FP_B.shape[1] + TP_B.shape[1])*100

        mean_matched_displacement = np.average(TP_A - TP_B, axis=1)
        metrics['mean_matched_distance'] = np.linalg.norm(mean_matched_displacement)

        random_errors = TP_A - TP_B - mean_matched_displacement.reshape(3, 1)
        metrics['mean_matched_random_distance'] = np.average(np.linalg.norm(random_errors))

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        percent_change = abs(old - new)/old*100.0
        max_allowed_percent_change = 2.0
        passed = percent_change < max_allowed_percent_change
        if passed:
            return True, 'Passed with percent change {}'.format(percent_change)
        else:
            return False, 'Falied with percent change {}'.format(percent_change)
