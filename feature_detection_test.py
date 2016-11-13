import os

import numpy as np
import scipy.io
import dicom

from algorithm_test_runner.test_suite import Suite
from featured_detection import detect_features
from dicom_import import combine_slices


class TestFeatureDetection(Suite):
    alias = 'feature-detection'
    
    def collect(self):
        return {
            'mri-001-axial': {
                'images': './data/mri-001-axial',
                'golden': './data/points/mri-001-axial-golden.mat',
            }
        }

    def run(self, case_id, case_input):
        context = {}

        input_dicom_filenames = os.listdir(case_input['images'])
        dicom_datasets = [dicom.read_file(f) for f in input_dicom_filenames]
        voxels, ijk_to_patient_xyz_transform = combine_slices(dicom_datasets)

        points_in_patient_xyz = detect_features(voxels, ijk_to_patient_xyz_transform)
        context['points_in_patient_xyz'] = points_in_patient_xyz

        # TODO: find all points that are matched w/in a certain distance

        return metrics, context

    def verify(self, old, new):
        percent_change = abs(old - new)/old*100.0
        max_allowed_percent_change = 2.0
        passed = percent_change < max_allowed_percent_change
        if passed:
            return True, 'Passed with percent change {}'.format(percent_change)
        else:
            return False, 'Falied with percent change {}'.format(percent_change)
