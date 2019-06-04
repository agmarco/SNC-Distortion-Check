import sys
from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt
from hdat import Suite, MetricsChecker

from . import file_io
from . import points_utils
from . import slicer
from .slicer_fp_rejector import render_intersection_square
from . import affine
from .fp_rejector import remove_fps
from .feature_detection import FeatureDetector


class FeatureDetectionSuite(Suite):
    id = 'feature-detection'

    def collect(self):
        sys.setrecursionlimit(10000)  # 603A-1 fails without this
        cases = {
            '603A-1': {
                'voxels': 'tmp/001_ct_603A_E3148_ST1.25-voxels.mat',
                'points': 'data/points/001_ct_603A_E3148_ST1.25-golden.mat',
            },
            '603A-2': {
                'voxels': 'tmp/006_mri_603A_UVA_Axial_2ME2SRS5-voxels.mat',
                'points': 'data/points/006_mri_603A_UVA_Axial_2ME2SRS5-golden.mat',
            },
            '603A-3': {
                'voxels': 'tmp/011_mri_603A_arterial_TOF_3d_motsa_ND-voxels.mat',
                'points': 'data/points/011_mri_630A_arterial_TOF_3d_motsa_ND-golden.mat',
            },
            # '604-1': {
            #     'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
            #     'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
            #     'notes': 'This scan currently fails because the ROI radius used for the center '
            #              'of mass calculations is only 1 px on the z-axis. Since this is the '
            #              'old model, we are disregarding for now.',
            # },
            '604-2': {
                'voxels': 'data/voxels/019_mri_604_Siemens_Vida_3T_3D_Flash_ND-voxels.mat',
                'points': 'data/points/019_mri_604_Siemens_Vida_3T_3D_Flash_ND-golden.mat',
            },
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
        context['voxel_spacing'] = voxel_spacing
        context['ijk_to_xyz'] = ijk_to_xyz

        rho = lambda bmag: 2.5
        context['raw'] = self._process_points(golden_points, feature_detector.points_xyz, rho)

        points_ijk = feature_detector.points_ijk
        pruned_points_ijk = remove_fps(points_ijk, voxels, voxel_spacing, phantom_model)
        pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)
        context['pruned'] = self._process_points(golden_points, pruned_points_xyz, rho)

        metrics['TPF'] = context['pruned']['TPF']
        metrics['FPF'] = context['pruned']['FPF']
        metrics['FLE_100'] = context['pruned']['FLE_100']['r']
        metrics['FLE_50'] = context['pruned']['FLE_50']['r']

        return metrics, context

    def _process_points(self, golden_points, points, rho):
        context = OrderedDict()

        FN_A, TP_A, TP_B, FP_B = points_utils.categorize(golden_points, points, rho)

        context['FN_A'] = FN_A
        context['TP_A'] = TP_A
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        TPF, FPF, FLE_percentiles = points_utils.metrics(FN_A, TP_A, TP_B, FP_B)
        context['TPF'] = TPF
        context['FPF'] = FPF

        for p in [0, 25, 50, 75, 95, 99, 100]:
            context['FLE_{}'.format(p)] = FLE_percentiles[p]

        return context

    def _print_points_metrics(self, point_cloud_comparison_metrics):
        for k, v in point_cloud_comparison_metrics.items():
            if k.startswith('FLE_'):
                print(points_utils.format_FLE_percentile(v))
            elif type(v) == float:
                print("{} = {:06.4f}".format(k, v))

    def check(self, old, new):
        checker = MetricsChecker(old, new)
        checker.can_increase('TPF', abs_tol=0.01)
        checker.can_decrease('FPF', abs_tol=0.01)
        checker.close('FLE_100', abs_tol=0.1)
        checker.close('FLE_50', abs_tol=0.1)
        return checker.result()

    def show(self, result):
        context = result['context']

        print('BEFORE FP-REJECTOR DETECTION')
        self._print_points_metrics(context['raw'])
        print('AFTER FP-REJECTOR DETECTION')
        self._print_points_metrics(context['pruned'])

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
                'points_xyz': context['pruned']['TP_A'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Gold Standard',
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

        s = slicer.PointsSlicer(context['preprocessed_image'], ijk_to_xyz, descriptors)
        s.add_renderer(slicer.render_overlay(context['feature_image'], context['ijk_to_xyz']), hidden=True)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_translucent_overlay(
            context['label_image'] > 0,
            [0, 1, 0],
            context['ijk_to_xyz'],
        ))
        s.add_renderer(partial(render_intersection_square, voxels, voxel_spacing, phantom_model))
        s.add_renderer(slicer.render_cursor)
        s.draw()
        plt.show()
