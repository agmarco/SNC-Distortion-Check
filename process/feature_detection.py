import logging
import os

from scipy import signal

from . import kernels
from . import peak_detection
from . import phantoms
from . import affine
from .utils import invert

logger = logging.getLogger(__name__)


# MRIs tend to effectively expand the grid radius beyond its underlying
# physical size; this dict contains fudge factors that account for this
# phenomena and allow the algorithm to adjust.
modality_grid_radius_factors = {
    'mri': 1.5,
    'ct': 1.0,
}


class FeatureDetector:
    def __init__(self, phantom_model, modality, image, ijk_to_xyz):
        logger.info('starting feature detection')
        self.image = image.copy()
        self.phantom_model = phantom_model
        self.modality = modality

        self.ijk_to_xyz = ijk_to_xyz
        self.voxel_spacing = affine.voxel_spacing(self.ijk_to_xyz)

        actual_grid_radius = phantoms.paramaters[phantom_model]['grid_radius']
        modality_grid_radius_factor = modality_grid_radius_factors[self.modality]
        self.grid_radius = actual_grid_radius*modality_grid_radius_factor

        self.grid_spacing = phantoms.paramaters[phantom_model]['grid_spacing']

        logger.info('building kernel')
        self.kernel = self._build_kernel()

        logger.info('preprocessing image')
        self.preprocessed_image = self._preprocess()

        logger.info('convolving with feature kernel')
        self.feature_image = signal.fftconvolve(self.preprocessed_image, self.kernel, mode='same')

        logger.info('detecting peaks')
        search_radius = self.grid_spacing/2.0
        self.points_ijk, self.label_image = peak_detection.detect_peaks(
            self.feature_image,
            self.voxel_spacing,
            search_radius,
        )

        self.points_xyz = affine.apply_affine(self.ijk_to_xyz, self.points_ijk)

    def _build_kernel(self):
        return kernels.gaussian(self.voxel_spacing, self.grid_radius*0.6)

    def _preprocess(self):
        if self.modality == 'mri':
            return invert(self.image)
        else:
            return self.image
