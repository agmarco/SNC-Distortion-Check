"""
This module is for previewing and selecting grid intersections that the
CNN should learn to reject due to nearby artifacts.
"""

import argparse
import logging

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from process import file_io, affine, slicer, kernels, phantoms
from process.annotate import AnnotateSlicer
from process.feature_detection import modality_grid_radius_factors, FeatureDetector

log = logging.getLogger(__name__)

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


class RejectPointsSlicer(AnnotateSlicer):
    def __init__(self, voxels, ijk_to_xyz, golden_points_xyz, rejected_points_xyz, detected_points_xyz):
        points_descriptors = [
            {
                'points_xyz': golden_points_xyz,
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Gold Standard',
                    'marker': 'o',
                }
            },
            {
                'points_xyz': rejected_points_xyz,
                'scatter_kwargs': {
                    'color': 'r',
                    'label': 'Rejected',
                    'marker': 'o',
                }
            },
            {
                'points_xyz': detected_points_xyz,
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'Detected',
                    'marker': 'x',
                }
            },
        ]
        super(AnnotateSlicer, self).__init__(voxels, ijk_to_xyz, points_descriptors)
        self.selected_descriptor = None
        self.selected_indice = None
        self.f.canvas.mpl_connect('key_press_event', lambda e: self.on_key_press(e))

    def reclassify_point(self, new_descriptor_index):
        if self.selected_descriptor == 2:
            old_points = self.points_descriptors[self.selected_descriptor]['points_ijk']
            new_points = self.points_descriptors[new_descriptor_index]['points_ijk']
            selected_point = old_points[:, self.selected_indice]
            new_points = np.append(new_points, np.array([selected_point]).T, axis=1)
            self.points_descriptors[new_descriptor_index]['points_ijk'] = new_points
            self.selected_descriptor = new_descriptor_index
            self.selected_indice = new_points.shape[1] - 1

        elif self.selected_descriptor != new_descriptor_index:
            old_points = self.points_descriptors[self.selected_descriptor]['points_ijk']
            new_points = self.points_descriptors[new_descriptor_index]['points_ijk']
            num_old_points = old_points.shape[1]
            selected_point = old_points[:, self.selected_indice]
            old_points = old_points[:, np.arange(num_old_points) != self.selected_indice]
            self.points_descriptors[self.selected_descriptor]['points_ijk'] = old_points
            new_points = np.append(new_points, np.array([selected_point]).T, axis=1)
            self.points_descriptors[new_descriptor_index]['points_ijk'] = new_points
            self.selected_descriptor = new_descriptor_index
            self.selected_indice = new_points.shape[1] - 1

    def on_key_press(self, event):
        if self.selected_descriptor is not None and self.selected_indice is not None:
            if event.key == 'g':
                self.reclassify_point(0)
                self.draw()
            elif event.key == 'r':
                self.reclassify_point(1)
                self.draw()
            elif event.key in ['d', 'e', 'delete']:
                if self.selected_descriptor == 2:
                    pass
                else:
                    super().on_key_press(event)
            else:
                super().on_key_press(event)
        else:
            super().on_key_press(event)


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

    try:
        golden_points_xyz = file_io.load_points(dataset['points'])['points']
    except FileNotFoundError:
        golden_points_xyz = np.array([[], [], []])

    try:
        rejected_points_xyz = file_io.load_points(dataset['rejected'])['points']
    except FileNotFoundError:
        rejected_points_xyz = np.array([[], [], []])

    phantom_model = dataset['model']
    modality = dataset['modality']

    feature_detector = FeatureDetector(phantom_model, modality, voxels, ijk_to_xyz)
    detected_points_ijk = feature_detector.points_ijk
    detected_points_xyz = affine.apply_affine(ijk_to_xyz, detected_points_ijk)

    feature_image = get_feature_image(voxels, ijk_to_xyz, phantom_model, modality)

    s = RejectPointsSlicer(voxels, ijk_to_xyz, golden_points_xyz, rejected_points_xyz, detected_points_xyz)
    s.add_renderer(slicer.render_overlay(feature_image, ijk_to_xyz))
    s.add_renderer(slicer.render_points)
    s.add_renderer(slicer.render_cursor, hidden=True)
    s.add_renderer(slicer.render_legend)

    s.draw()
    plt.show()

    golden_points_ijk = s.points_descriptors[0]['points_ijk']
    rejected_points_ijk = s.points_descriptors[1]['points_ijk']
    golden_points_xyz = affine.apply_affine(ijk_to_xyz, golden_points_ijk)
    rejected_points_xyz = affine.apply_affine(ijk_to_xyz, rejected_points_ijk)

    # file_io.save_points(dataset['points'], {
    #     'points': golden_points_xyz,
    # })
    log.info(f"Wrote {golden_points_xyz.shape[1]} points to {dataset['points']}")

    # file_io.save_points(dataset['rejected'], {
    #     'points': rejected_points_xyz,
    # })
    log.info(f"Wrote {rejected_points_xyz.shape[1]} points to {dataset['rejected']}")
