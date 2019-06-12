from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
from hdat import Suite, MetricsChecker

from . import points_utils, phantoms, slicer, affine, file_io
from .utils import fov_center_xyz
from .visualization import scatter3
from .interpolation import interpolate_distortion
from .fp_rejector import remove_fps
from .feature_detection import FeatureDetector
from .registration import rigidly_register_and_categorize
from .dicom_import import combined_series_from_zip


def print_histogram(data, suffix):
    counts, bin_edges = np.histogram(data[np.isfinite(data)])
    total = np.sum(counts)
    for i, c in enumerate(counts):
        template = '{0:5.3f}{suffix} - {1:5.3f}{suffix}: {2:3.2f}%'
        print(template.format(bin_edges[i], bin_edges[i + 1], c/total*100, suffix=suffix))


class FullAlgorithmSuite(Suite):
    id = 'full-algorithm'
    PASS_THRESHOLD = 1.0

    def collect(self):
        return {
            '603A-CT-004': {
                'dicom': 'data/dicom/004_ct_603A_UVA_IYKOQG2M.zip',
                'notes': 'High quality; full FOV; slight rotation',
                'modality': 'ct',
                'phantom_model': '603A',
            },
            '603A-MR-006': {
                'dicom': 'data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip',
                'notes': 'Medium quality; full FOV; slight rotation',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '603A-MR-007': {
                'dicom': 'data/dicom/007_mri_603A_UVA_Sagittal_XUCWOCNR.zip',
                'notes': 'Medium quality saggitally sliced',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '603A-MR-026': {
                'dicom': 'data/dicom/026_mri_603A_t1_vibe_tra_FS_ND.zip',
                'notes': 'Higher quality with the phantom not centered within the axial slices',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '604-MR-010': {
                'dicom': 'data/dicom/010_mri_604_LFV-Phantom_E2632-1.zip',
                'modality': 'mri',
                'notes': 'old model of the 604 with a central gap; probably no need to support',
                'phantom_model': '604',
            },
            '604-MR-012': {
                'dicom': 'data/dicom/012_mri_604_ST150_in_Siemens_Vida_3T_at_ISO.zip',
                'modality': 'mri',
                'phantom_model': '604',
            },
            '603A-MR-013': {
                'dicom': 'data/dicom/013_mri_603A_patient_10182017.zip',
                'notes': 'Very high quality',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '603A-MR-014': {
                'dicom': 'data/dicom/014_mri_603A_T1_MPRAGE_TRA_P2_ISO_0_8_CORRECTED_DISTORTION_0005.zip',
                'notes': 'High quality; the grid has funny looking "ripples"',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '603A-MR-018': {
                'dicom': 'data/dicom/018_mri_603A_vibe_tra_FS.zip',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '604-MR-019': {
                'dicom': 'data/dicom/019_mri_604_Siemens_Vida_3T_3D_Flash_ND.zip',
                'modality': 'mri',
                'phantom_model': '604',
            },
            '603A-MR-020': {
                'dicom': 'data/dicom/020_mri_603A_Siemens_3T_Skyra.zip',
                'notes': 'Extremely high quality; almost looks like a CT',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '603A-CT-022': {
                'dicom': 'data/dicom/022_ct_603A_Niranjan_Original.zip',
                'modality': 'ct',
                'notes': 'This is a large high-quality CT',
                'phantom_model': '603A',
            },
            '604-CT-023': {
                'dicom': 'data/dicom/023_ct_604_Water_ST125_120kVp_175mAs.zip',
                'modality': 'ct',
                'phantom_model': '604',
            },
            '604-CT-024': {
                'dicom': 'data/dicom/024_ct_604_Canada_Original.zip',
                'modality': 'ct',
                'phantom_model': '604',
            },
            '603A-MR-025': {
                'dicom': 'data/dicom/025_mri_603A_spc_lukas.zip',
                'modality': 'mri',
                'phantom_model': '603A',
            },
            '604-CT-027': {
                'dicom': 'data/dicom/027_ct_604_st125_cheasapeake_imaging.zip',
                'modality': 'ct',
                'phantom_model': '604',
            },
            '604-MR-028': {
                'dicom': 'data/dicom/028_mri_604_st150_in_siemens_vida_3T.zip',
                'modality': 'mri',
                'phantom_model': '604',
            },
            # '603A-MR-029': {
                # 'dicom': 'data/dicom/029_mri_603A_t2_ci3d_tra_iso_0.8mm_ND.zip',
                # 'notes': 'The FOV does not cover the phantom; thus the algorithm currently fails',
                # 'modality': 'mri',
                # 'phantom_model': '603A',
            # },
            # '603A-MR-030': {
                # 'dicom': 'data/dicom/030_mri_603A_t1_vibe_sag_FS_MRisoMovedAwayFromHead.zip',
                # 'notes': 'Saggital view; low quality; the algorithm currently does not support rotated datasets',
                # 'modality': 'mri',
                # 'phantom_model': '603A',
            # },
            '604-CT-031': {
                'dicom': 'data/dicom/031_ct_604_water_st125_120kVp_175mAs.zip',
                'notes': 'Water is the phantom, so the contrast in the casing seems higher',
                'modality': 'ct',
                'phantom_model': '604',
            },
            '604-CT-032': {
                'dicom': 'data/dicom/032_ct_604_w_G_w_S_CIRS_05132019.zip',
                'modality': 'ct',
                'phantom_model': '604-new',
            },
            '604-MR-033': {
                'dicom': 'data/dicom/033_mri_604_w_G_w_S_Chesapeake_05102019.zip',
                'modality': 'mri',
                'phantom_model': '604-new',
            },
        }

    def run(self, case_input):
        metrics = OrderedDict()
        context = OrderedDict()

        phantom_paramaters = phantoms.paramaters[case_input['phantom_model']]
        golden_points_filename = phantom_paramaters['points_file']
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

        context['feature_image'] = feature_detector.feature_image
        context['preprocessed_image'] = feature_detector.preprocessed_image

        # 2. fp rejector
        points_ijk = feature_detector.points_ijk
        pruned_points_ijk = remove_fps(points_ijk, voxels, voxel_spacing, phantom_model)
        pruned_points_xyz = affine.apply_affine(ijk_to_xyz, pruned_points_ijk)

        points_ijk_set = set([tuple(x) for x in points_ijk.T])
        pruned_points_ijk_set = set([tuple(x) for x in pruned_points_ijk.T])
        rejected_points_ijk_set = points_ijk_set - pruned_points_ijk_set
        rejected_points_ijk = np.array(list(rejected_points_ijk_set)).T
        rejected_points_xyz = affine.apply_affine(ijk_to_xyz, rejected_points_ijk)
        context['FP_B_CNN'] = rejected_points_xyz

        isocenter_in_B = fov_center_xyz(voxels.shape, ijk_to_xyz)

        context['A_I'] = affine.apply_affine(affine.translation(*isocenter_in_B), context['A'])

        # 3. rigidly register
        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
            golden_points,
            pruned_points_xyz,
            phantom_paramaters['grid_spacing'],
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

        TPF, FPF, _ = points_utils.metrics(FN_A_S, TP_A_S, TP_B, FP_B)
        metrics['TPF'] = TPF
        metrics['FPF'] = FPF

        # 4. interpolate
        grid_density_mm = 4.0
        error_mags = np.linalg.norm(TP_A_S - TP_B, axis=0)
        overlay_ijk_to_xyz, distortion_grid = interpolate_distortion(TP_A_S, error_mags, grid_density_mm)
        context['distortion_grid'] = distortion_grid
        context['overlay_ijk_to_xyz'] = overlay_ijk_to_xyz

        # we fill in voxels outside the convex hull at 0, although technically, values
        # inside the convex hull could also be zero; thus, this is a "worst case"
        # metric and may underestimate the fraction of volume covered if there actually
        # is 0 distortion (unlikely)
        is_zero = distortion_grid == 0
        num_finite = np.sum(~is_zero)
        num_total = distortion_grid.size
        metrics['fraction_of_volume_covered'] = num_finite/float(num_total)

        metrics['max_distortion'] = np.nanmax(distortion_grid)
        metrics['99_distortion'] = np.nanpercentile(distortion_grid, 99)
        metrics['95_distortion'] = np.nanpercentile(distortion_grid, 95)
        metrics['90_distortion'] = np.nanpercentile(distortion_grid, 90)
        metrics['mean_distortion'] = np.nanmean(distortion_grid)
        metrics['median_distortion'] = np.nanmedian(distortion_grid)
        metrics['min_distortion'] = np.nanmin(distortion_grid)

        print('histogram mm')
        print_histogram(distortion_grid, 'mm')

        return metrics, context

    def check(self, old, new):
        checker = MetricsChecker(old, new)
        checker.can_increase('TPF', abs_tol=0.01)
        checker.close('fraction_of_volume_covered', abs_tol=0.01)
        checker.can_decrease('FPF', abs_tol=0.01)
        shift_tolerance = 0.1
        checker.close('max_distortion', abs_tol=shift_tolerance)
        checker.close('median_distortion', abs_tol=shift_tolerance)
        checker.close('min_distortion', abs_tol=shift_tolerance)
        return checker.result()

    def show(self, result):
        metrics = result['metrics']
        context = result['context']

        print('% volume: {:3.2f}%'.format(metrics['fraction_of_volume_covered']*100))
        print('number of true positives: ', context['TP_B'].shape[1])
        print('true positive fraction: {:5.3f}'.format(metrics['TPF']))
        print('false positive fraction: {:5.3f}'.format(metrics['FPF']))
        print('maximum distortion magnitude: {:5.3f}mm'.format(metrics['max_distortion']))
        print('99th percentile distortion magnitude: {:5.3f}mm'.format(metrics['99_distortion']))
        print('95th percentile distortion magnitude: {:5.3f}mm'.format(metrics['95_distortion']))
        print('90th percentile distortion magnitude: {:5.3f}mm'.format(metrics['90_distortion']))
        print('mean distortion magnitude: {:5.3f}mm'.format(metrics['mean_distortion']))
        print('median distortion magnitude: {:5.3f}mm'.format(metrics['median_distortion']))
        print('min distortion magnitude: {:5.3f}mm'.format(metrics['min_distortion']))

        error_mags = np.linalg.norm(context['TP_A_S'] - context['TP_B'], axis=0)

        tp_b_passed = error_mags <= FullAlgorithmSuite.PASS_THRESHOLD
        tp_b_failed = ~tp_b_passed

        descriptors = [
            {
               'points_xyz': context['FN_A_S'],
               'scatter_kwargs': {
                   'color': 'y',
                   'label': 'False Negatives',
                   'marker': 'o'
               }
            },
            {
                'points_xyz': context['TP_A_S'],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Gold Standard Registered',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': context['TP_B'][:, tp_b_passed],
                'scatter_kwargs': {
                    'color': 'g',
                    'label': f'True Positives (<= {FullAlgorithmSuite.PASS_THRESHOLD} mm distortion)',
                    'marker': 'x'
                }
            },
            {
                'points_xyz': context['TP_B'][:, tp_b_failed],
                'scatter_kwargs': {
                    'color': 'k',
                    'label': f'True Positives (> {FullAlgorithmSuite.PASS_THRESHOLD} mm distortion)',
                    'marker': 'x'
                }
            },
            {
                'points_xyz': context['FP_B'],
                'scatter_kwargs': {
                    'color': 'r',
                    'label': 'Rejected by Registration',
                    'marker': 'x'
                }
            },
            # {
            #     'points_xyz': context['FP_B_CNN'],
            #     'scatter_kwargs': {
            #         'color': 'm',
            #         'label': 'Rejected by CNN',
            #         'marker': 'x'
            #     }
            # },
        ]

        distortion_magnitude = context['distortion_grid']
        min_value = np.nanmin(distortion_magnitude)
        max_value = np.nanmax(distortion_magnitude)
        nan_value = min_value - 0.1*abs(max_value - min_value)
        distortion_magnitude[np.isnan(distortion_magnitude)] = nan_value
        overlay_ijk_to_xyz = context['overlay_ijk_to_xyz']

        s = slicer.PointsSlicer(context['preprocessed_image'], context['ijk_to_xyz'], descriptors)
        s.add_renderer(slicer.render_overlay(context['feature_image'], context['ijk_to_xyz']), hidden=True)
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_cursor)
        s.add_renderer(slicer.render_legend)
        s.add_renderer(slicer.render_overlay(distortion_magnitude, overlay_ijk_to_xyz, cmap='cool', alpha=0.8), hidden=True)
        s.draw()
        plt.show()

        scatter3({
            'Gold Standard': context['TP_A_S'],
            'Rejected by Registration': context['FP_B'],
            'True Positives': context['TP_B'],
            'False Negatives': context['FN_A_S'],
            # 'Rejected by CNN': context['FP_B_CNN'],
        })
        plt.show()
