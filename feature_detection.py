import logging

import numpy as np
from scipy import signal, ndimage

import affine
from utils import invert, unsharp_mask
import phantoms
import kernels
import points_utils
import peak_detection

logger = logging.getLogger(__name__)
import sys; logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# TODO: handle this in a "ConsoleApp" class


class FeatureDetector:
    def __init__(self, phantom_name, image, ijk_to_xyz):
        # TODO: detect whether we need to invert here
        self.image = invert(image)
        self.phantom_name = phantom_name

        self.ijk_to_xyz = ijk_to_xyz

        self.grid_radius = phantoms.paramaters[phantom_name]['grid_radius']
        self.grid_spacing = phantoms.paramaters[phantom_name]['grid_spacing']

        self.pixel_spacing = affine.pixel_spacing(self.ijk_to_xyz)

    def run(self):
        logger.info('building kernel')
        self.kernel = self.build_kernel()
        logger.info('preprocessing image')
        self.preprocessed_image = self.preprocess()
        logger.info('convolving with feature kernel')
        self.feature_image = signal.fftconvolve(self.preprocessed_image, self.kernel, mode='same')

        logger.info('detecting peaks')
        self.points_ijk, self.label_image = peak_detection.detect_peaks(
            self.feature_image,
            self.pixel_spacing,
            self.grid_spacing/2,
            self.grid_radius
        )

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
