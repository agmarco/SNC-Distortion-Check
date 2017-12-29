"""
This module is for previewing and selecting grid intersections that the
CNN should learn to reject due to nearby artifacts.
"""

import argparse
import os

import scipy.io
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
    },
}

rejected_points = np.array([[], [], []])


def accept(point):
    plt.close()


def reject(point):
    global rejected_points
    rejected_points = np.append(rejected_points, np.array([point]).T, axis=1)
    plt.close()


def show(phantom_model, modality, voxels, ijk_to_xyz, point_xyz, detected_point_xyz, original_point_xyz, cursor):
    descriptors = [
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

    voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
    actual_grid_radius = phantoms.paramaters[phantom_model]['grid_radius']
    modality_grid_radius_factor = modality_grid_radius_factors[modality]
    grid_radius = actual_grid_radius * modality_grid_radius_factor
    kernel = kernels.gaussian(voxel_spacing, grid_radius)
    feature_image = signal.fftconvolve(voxels, kernel, mode='same')

    s = slicer.PointsSlicer(voxels, ijk_to_xyz, descriptors)
    s.cursor = cursor
    s.add_renderer(slicer.render_overlay(feature_image, ijk_to_xyz))
    s.add_renderer(slicer.render_points)
    s.add_renderer(slicer.render_cursor, hidden=True)
    s.add_renderer(slicer.render_legend)

    axaccept = plt.axes([0.7, 0.05, 0.1, 0.075])
    axreject = plt.axes([0.81, 0.05, 0.1, 0.075])
    baccept = Button(axaccept, 'Accept')
    breject = Button(axreject, 'Reject')
    baccept.on_clicked(lambda e: accept(original_point_xyz))
    breject.on_clicked(lambda e: reject(original_point_xyz))

    s.draw()
    plt.show()


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
    points_xyz = file_io.load_points(dataset['points'])['points']
    phantom_model = dataset['model']
    modality = dataset['modality']

    feature_detector = FeatureDetector(phantom_model, modality, voxels, ijk_to_xyz)
    detected_points_ijk = feature_detector.points_ijk

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

            show(
                phantom_model,
                modality,
                voxel_window,
                ijk_to_xyz,
                point_xyz,
                closest_detected_point_xyz,
                original_point_xyz,
                cursor,
            )

    filename = f"{os.path.splitext(os.path.basename(dataset['points']))[0]}.mat"
    output_path = f"data/rejected_points/{filename}"
    scipy.io.savemat(output_path, {'points': rejected_points})
