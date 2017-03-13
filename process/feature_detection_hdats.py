from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np

from . import file_io
from . import points_utils
from . import slicer
from hdatt.suite import Suite
from .feature_detection import FeatureDetector


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
            # '001': {
                # 'voxels': 'tmp/001_ct_603A_E3148_ST1.25-voxels.mat',
                # 'points': 'data/points/001_ct_603A_E3148_ST1.25-golden.mat',
            # },
            # '006': {
                # 'voxels': 'tmp/006_mri_603A_UVA_Axial_2ME2SRS5-voxels.mat',
                # 'points': 'data/points/006_mri_603A_UVA_Axial_2ME2SRS5-golden.mat',
            # },
            # '010': {
                # 'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
                # 'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
            # },
            # '011': {
                # 'voxels': 'tmp/011_mri_603A_arterial_TOF_3d_motsa_ND-voxels.mat',
                # 'points': 'data/points/011_mri_630A_arterial_TOF_3d_motsa_ND-golden.mat',
            # },
            '1540-075': {
                'voxels': 'tmp/xxx_ct_1540_ST075-120kVp-100mA-voxels.mat',
                'points': 'data/points/1540-gaussian.mat',
            },
            '1540-125': {
                'voxels': 'tmp/xxx_ct_1540_ST125-120kVp-100mA-voxels.mat',
                'points': 'data/points/1540-gaussian.mat',
            },
            '1540-150': {
                'voxels': 'tmp/xxx_ct_1540_ST150-120kVp-100mA-voxels.mat',
                'points': 'data/points/1540-gaussian.mat',
            },
            '1540-250': {
                'voxels': 'tmp/xxx_ct_1540_ST250-120kVp-100mA-voxels.mat',
                'points': 'data/points/1540-gaussian.mat',
            },
        }
        return cases

    def run(self, case_input):
        metrics = OrderedDict()
        context = OrderedDict()

        context['case_input'] = case_input

        voxel_data = file_io.load_voxels(case_input['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
        phantom_name = voxel_data['phantom_name']
        modality = voxel_data['modality']

        feature_detector = FeatureDetector(phantom_name, modality, voxels, ijk_to_xyz)
        points = feature_detector.run()

        context['phantom_name'] = phantom_name
        context['label_image'] = feature_detector.label_image
        context['preprocessed_image'] = feature_detector.preprocessed_image
        context['feature_image'] = feature_detector.feature_image
        context['kernel'] = feature_detector.kernel

        golden_points = file_io.load_points(case_input['points'])['points']

        rho = lambda bmag: 3
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

        self.print_metrics(metrics)

        return metrics, context

    def print_metrics(self, metrics):
        for k, v in metrics.items():
            if k.startswith('FLE_'):
                msg = "{} = {:06.4f}mm ({:06.4f}mm, {:06.4f}mm, {:06.4f}mm)"
                print(msg.format(k, v['r'], v['x'], v['y'], v['z']))
            else:
                print("{} = {:06.4f}".format(k, v))

    def verify(self, old_metrics, new_metrics):
        return new_metrics['TPF'] == 1.0 and \
               new_metrics['FPF'] < 0.2 and \
               new_metrics['FLE_100']['r'] < 0.375, ''

    def show(self, result):
        self.print_metrics(result['metrics'])

        context = result['context']
        descriptors = [
            {
                'points_xyz': context['FN_A'],
                'scatter_kwargs': {
                    'color': 'y',
                    'label': 'FN_A',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['TP_A'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'TP_A',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['TP_B'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'TP_B',
                    'marker': 'x'
                }
            },
            {
                'points_xyz': context['FP_B'],
                'scatter_kwargs': {
                    'color': 'r',
                    'label': 'FP_B',
                    'marker': 'x'
                }
            },
        ]

        voxel_data = file_io.load_voxels(context['case_input']['voxels'])
        raw_voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
        phantom_name = voxel_data['phantom_name']

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

        s = slicer.PointsSlicer(context['preprocessed_image'], ijk_to_xyz, descriptors)
        s.add_renderer(slicer.render_overlay(context['feature_image']), hidden=True)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_translucent_overlay(
            context['label_image'] > 0,
            [0, 1, 0]
        ))
        s.add_renderer(slicer.render_translucent_overlay(kernel_big, [1, 0, 0]))
        s.add_renderer(slicer.render_cursor)
        s.draw()
        plt.show()