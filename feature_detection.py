import logging
import os

import numpy as np
from scipy import signal, ndimage

import affine
from utils import invert, unsharp_mask
import phantoms
import kernels
import points_utils
import peak_detection
from fp_rejector import is_grid_intersection

logger = logging.getLogger(__name__)
import sys; logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# TODO: handle this in a "ConsoleApp" class


class FeatureDetector:
    def __init__(self, phantom_name, modality, image, ijk_to_xyz):
        # TODO: detect whether we need to invert here
        self.image = invert(image)
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

    def run(self):
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
        num_points = points_ijk_unfiltered.shape[1]
        is_tp = np.empty((num_points,), dtype=bool)
        for i, point in enumerate(points_ijk_unfiltered.T):
            is_tp[i] = is_grid_intersection(np.round(point), self.image)

        # TODO: find a better way to clear out the old points
        self.points_ijk = ((points_ijk_unfiltered.T)[is_tp]).T
        assert self.points_ijk.shape[1] > 0, 'All of the points were filtered out!'

        self.points_xyz = affine.apply_affine(self.ijk_to_xyz, self.points_ijk)
        return self.points_xyz

    def build_kernel(self):
        return kernels.cylindrical_grid_intersection(
            self.pixel_spacing,
            self.grid_radius,
            self.grid_spacing
        )

    def preprocess(self):
        return self.image
        #return unsharp_mask(self.image, self.grid_spacing/self.pixel_spacing, 1.0)
