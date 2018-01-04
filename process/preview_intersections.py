"""
This module is for previewing and selecting grid intersections that the
CNN should learn to reject due to nearby artifacts.
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button
from scipy import signal

from process import file_io, affine, slicer, kernels, phantoms
from process.feature_detection import modality_grid_radius_factors, FeatureDetector

cube_size = 45
window_shape = np.array((cube_size, cube_size, cube_size))
cube_size_half = window_shape // 2

datasets = {
    '604-1': {
        'model': '604',
        'modality': 'mri',
        'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
        'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
        'rejected': 'data/rejected_points/010_mri_604_LFV-Phantom_E2632-1-rejected.mat',
    },
    '604-2': {
        'model': '604',
        'modality': 'mri',
        'voxels': 'data/voxels/019_mri_604_Siemens_Vida_3T_3D_Flash_ND-voxels.mat',
        'points': 'data/points/019_mri_604_Siemens_Vida_3T_3D_Flash_ND-golden.mat',
        'rejected': 'data/rejected_points/019_mri_604_Siemens_Vida_3T_3D_Flash_ND-rejected.mat',
    },
}

new_rejected_points_xyz = np.array([[], [], []])

PREVIEW_ALL = False


def accept(point):
    print('accept')
    plt.close()


def reject(point):
    print('reject')
    global new_rejected_points_xyz
    new_rejected_points_xyz = np.append(new_rejected_points_xyz, np.array([point]).T, axis=1)
    plt.close()


class RejectPointsSlicer(slicer.PointsSlicer):
    def __init__(self, voxels, ijk_to_xyz, point_xyz, detected_point_xyz):
        points_descriptors = [
            {
                'points_xyz': np.array([point_xyz]).T,
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Gold Standard',
                    'marker': 'o',
                }
            },
            {
                'points_xyz': np.array([detected_point_xyz]).T,
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Detected',
                    'marker': 'x',
                }
            },
        ]
        super().__init__(voxels, ijk_to_xyz, points_descriptors)
        axaccept = plt.axes([0.7, 0.05, 0.1, 0.075])
        axreject = plt.axes([0.81, 0.05, 0.1, 0.075])
        self.baccept = Button(axaccept, 'Accept')
        self.breject = Button(axreject, 'Reject')


def get_feature_image(voxels, ijk_to_xyz, phantom_model, modality):
    voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
    actual_grid_radius = phantoms.paramaters[phantom_model]['grid_radius']
    modality_grid_radius_factor = modality_grid_radius_factors[modality]
    grid_radius = actual_grid_radius * modality_grid_radius_factor
    kernel = kernels.gaussian(voxel_spacing, grid_radius)
    return signal.fftconvolve(voxels, kernel, mode='same')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phantom')
    args = parser.parse_args()
    assert args.phantom in datasets
    dataset = datasets[args.phantom]
    voxel_data = file_io.load_voxels(dataset['voxels'])
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_xyz']
    xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
    voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
    golden_points_xyz = file_io.load_points(dataset['points'])['points']
    rejected_points_xyz = file_io.load_points(dataset['rejected'])['points']
    points_xyz = np.append(golden_points_xyz, rejected_points_xyz, axis=1)
    phantom_model = dataset['model']
    modality = dataset['modality']

    feature_detector = FeatureDetector(phantom_model, modality, voxels, ijk_to_xyz)
    detected_points_ijk = feature_detector.points_ijk

    if PREVIEW_ALL:
        descriptors = [
            {
                'points_xyz': points_xyz,
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Gold Standard',
                    'marker': 'o',
                }
            },
            {
                'points_xyz': affine.apply_affine(ijk_to_xyz, detected_points_ijk),
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Detected',
                    'marker': 'x',
                }
            },
        ]

        feature_image = get_feature_image(voxels, ijk_to_xyz, phantom_model, modality)
        s = slicer.PointsSlicer(voxels, ijk_to_xyz, descriptors)
        s.add_renderer(slicer.render_overlay(feature_image, ijk_to_xyz))
        s.add_renderer(slicer.render_points)
        s.add_renderer(slicer.render_cursor, hidden=True)
        s.add_renderer(slicer.render_legend)

        s.draw()
        plt.show()
    else:
        for point_xyz in points_xyz.T:
            point_ijk = affine.apply_affine_1(xyz_to_ijk, point_xyz)
            i, j, k = np.round(point_ijk).astype(int)
            window = (
                (i - cube_size_half[0], i + cube_size_half[0]),
                (j - cube_size_half[1], j + cube_size_half[1]),
                (k - cube_size_half[2], k + cube_size_half[2]),
            )

            window_adjusted = (
                (max(window[0][0], 0), min(window[0][1], voxels.shape[0])),
                (max(window[1][0], 0), min(window[1][1], voxels.shape[1])),
                (max(window[2][0], 0), min(window[2][1], voxels.shape[2])),
            )

            ijk_offset = np.array([-a for a, b in window_adjusted])
            translation = np.array([
                [1, 0, 0, ijk_offset[0]],
                [0, 1, 0, ijk_offset[1]],
                [0, 0, 1, ijk_offset[2]],
                [0, 0, 0, 1],
            ])

            original_point_xyz = point_xyz
            point_ijk = affine.apply_affine_1(translation, point_ijk)
            point_xyz = affine.apply_affine_1(ijk_to_xyz, point_ijk)

            detected_points_ijk_translated = affine.apply_affine(translation, detected_points_ijk)
            point_ijk_repeat = np.repeat(np.array([point_ijk]).T, detected_points_ijk_translated.shape[1], axis=1)
            displacements = detected_points_ijk_translated - point_ijk_repeat
            distances = np.linalg.norm(displacements, axis=0).squeeze()
            min_index = np.argmin(distances)
            closest_detected_point_ijk = detected_points_ijk_translated[:, min_index]
            closest_detected_point_xyz = affine.apply_affine_1(ijk_to_xyz, closest_detected_point_ijk)

            error = np.linalg.norm(closest_detected_point_xyz - point_xyz)
            error_threshold = 3
            if error > error_threshold:
                print(f'Error: {error}')
                window_slice_tup = tuple(slice(*bounds) for bounds in window_adjusted)
                voxel_window = voxels[window_slice_tup]

                cursor = np.array([(b - a) / 2 for a, b in window], dtype=int)
                cursor_offset = np.array([min(a, 0) for a, b in window])
                cursor = np.add(cursor, cursor_offset)

                feature_image = get_feature_image(voxel_window, ijk_to_xyz, phantom_model, modality)
                s = RejectPointsSlicer(voxel_window, ijk_to_xyz, point_xyz, closest_detected_point_xyz)
                s.cursor = cursor
                s.baccept.on_clicked(lambda e: accept(original_point_xyz))
                s.breject.on_clicked(lambda e: reject(original_point_xyz))
                s.add_renderer(slicer.render_overlay(feature_image, ijk_to_xyz))
                s.add_renderer(slicer.render_points)
                s.add_renderer(slicer.render_cursor, hidden=True)
                s.add_renderer(slicer.render_legend)

                s.draw()
                plt.show()

        golden_points_xyz_set = set([tuple(x) for x in golden_points_xyz.T])
        new_rejected_points_xyz_set = set([tuple(x) for x in new_rejected_points_xyz.T])
        new_golden_points_xyz_set = golden_points_xyz_set - new_rejected_points_xyz_set
        new_golden_points_xyz = np.array(list(new_golden_points_xyz_set)).T

        file_io.save_points(dataset['points'], {
            'points': new_golden_points_xyz,
        })
        file_io.save_points(dataset['rejected'], {
            'points': new_rejected_points_xyz,
        })
