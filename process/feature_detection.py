import logging
import os
from functools import partial

from matplotlib import patches
from scipy import signal

from process.fp_rejector import is_grid_intersection, cube_size_mm
import argparse

from process import file_io
from process.slicer import PointsSlicer, render_points, render_cursor, render_legend
from matplotlib import pyplot as plt
import numpy as np

from . import kernels
from . import peak_detection
from . import phantoms
from .fp_rejector import remove_fps
from . import affine
from .utils import invert

logger = logging.getLogger(__name__)
import sys; logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# TODO: handle this in a "ConsoleApp" class


class FeatureDetector:
    def __init__(self, phantom_name, modality, image, ijk_to_xyz):
        self.image = image.copy()
        self.phantom_name = phantom_name
        self.modality = modality

        self.ijk_to_xyz = ijk_to_xyz

        actual_grid_radius = phantoms.paramaters[phantom_name]['grid_radius']
        modality_factor = {'mri': 1.5, 'ct': 1.0}[self.modality]
        grid_radius_environment_factor = float(os.environ.get('GRID_RADIUS', '1'))
        self.grid_radius = actual_grid_radius*modality_factor*grid_radius_environment_factor

        actual_grid_spacing = phantoms.paramaters[phantom_name]['grid_spacing']
        grid_spacing_environment_factor = float(os.environ.get('GRID_SPACING', '1'))
        self.grid_spacing = actual_grid_spacing*grid_spacing_environment_factor

        self.pixel_spacing = affine.pixel_spacing(self.ijk_to_xyz)

    def run(self, return_false_positives=False):
        # TODO: David when you split out the FP removal hdats please find a better way to do the return_false_positives
        # for visualization.
        logger.info('building kernel')
        self.kernel = self.build_kernel()
        logger.info('preprocessing image')
        self.preprocessed_image = self.preprocess()
        logger.info('convolving with feature kernel')
        self.feature_image = signal.fftconvolve(self.preprocessed_image, self.kernel, mode='same')

        logger.info('detecting peaks')
        search_radius = self.grid_spacing/2
        points_ijk_unfiltered, self.label_image = peak_detection.detect_peaks(
            self.feature_image,
            self.pixel_spacing,
            search_radius,
        )

        logger.info('discarding false positives using neural network')

        # TODO: switch to using original image after updating the model
        self.points_ijk, false_positives_points_ijk = remove_fps(points_ijk_unfiltered, self.image, self.pixel_spacing)
        assert self.points_ijk.shape[1] > 0, 'All of the points were filtered out!'

        self.points_xyz = affine.apply_affine(self.ijk_to_xyz, self.points_ijk)
        if not return_false_positives:
            return self.points_xyz
        else:
            false_positives_points_xyz = affine.apply_affine(self.ijk_to_xyz, false_positives_points_ijk)
            return self.points_xyz, false_positives_points_xyz


    def build_kernel(self):
        # TODO: consider using cross initially, and then gaussian.  This would
        # be as "backup" for the CNN.
        # return kernels.cylindrical_grid_intersection(
            # self.pixel_spacing,
            # self.grid_radius,
            # self.grid_spacing
        # )
        return kernels.gaussian(
            self.pixel_spacing,
            self.grid_radius*0.6
        )

    def preprocess(self):
        if self.modality == 'MR' or self.modality == 'mri':
            return invert(self.image)
        else:
            return self.image

def render_intersection_square(voxels, voxel_spacing, slicer):
    is_intersection = is_grid_intersection(slicer.cursor, voxels, voxel_spacing)
    window_size_half = np.floor(cube_size_mm*0.5 / voxel_spacing).astype(int)

    print('cursor: {}, {}'.format(slicer.cursor, is_intersection))
    color = "green" if is_intersection else "red"
    i, j, k = slicer.cursor
    slicer.i_ax.add_patch(patches.Rectangle(
        (k - window_size_half[2], j - window_size_half[1]), window_size_half[2]*2, window_size_half[1]*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))

    slicer.j_ax.add_patch(patches.Rectangle(
        (k - window_size_half[2], i - window_size_half[0]), window_size_half[2]*2, window_size_half[0]*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))

    slicer.k_ax.add_patch(patches.Rectangle(
        (j - window_size_half[1], i - window_size_half[0]), window_size_half[1]*2, window_size_half[0]*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('voxels', help='Input path to read voxels-file')
    parser.add_argument('points', nargs='?', help='Output path to write points-file')
    parser.add_argument('--plot', action='store_true', help='Plot the result overlaid')
    args = parser.parse_args()

    voxel_data = file_io.load_voxels(args.voxels)
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
    phantom_name = voxel_data['phantom_name']
    modality = voxel_data['modality']

    points_in_patient_xyz, false_positives_points_xyz = FeatureDetector(phantom_name, modality, voxels, ijk_to_xyz).run(return_false_positives=True)
    if args.plot:
        slicer = PointsSlicer(voxels, ijk_to_xyz,  [
            {
                'points_xyz': points_in_patient_xyz,
                'scatter_kwargs': {
                    'color': 'g',
                    'label': 'predicted',
                    'marker': 'o'
                }
            },
            {
                'points_xyz': false_positives_points_xyz,
                'scatter_kwargs': {
                    'color': 'y',
                    'label': 'removed FPs',
                    'marker': 'o'
                }
            },
        ])
        slicer.add_renderer(render_points)
        slicer.add_renderer(partial(render_intersection_square, voxels, affine.pixel_spacing(ijk_to_xyz)))
        slicer.add_renderer(render_cursor)
        slicer.add_renderer(render_legend)
        slicer.draw()
        plt.show()

    if args.points:
        file_io.save_points(args.points, {'points': points_in_patient_xyz})
