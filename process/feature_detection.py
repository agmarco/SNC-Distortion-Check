import logging
import os

from scipy import signal
from scipy.ndimage.filters import gaussian_filter

from . import kernels
from . import peak_detection
from . import phantoms
from . import affine
from .utils import invert

logger = logging.getLogger(__name__)


modality_sigmas_mm = {
    'mri': 1.65,
    'ct': 1.2,
}


class FeatureDetector:
    def __init__(self, phantom_model, modality, image, ijk_to_xyz, limit_memory_usage=False):
        logger.info('starting feature detection')

        self.phantom_model = phantom_model
        self.modality = modality

        self.ijk_to_xyz = ijk_to_xyz
        self.voxel_spacing = affine.voxel_spacing(self.ijk_to_xyz)

        r_mm = 3.5  # NOTE: this should probably be proportional to the grid_radius
        sigma_mm = modality_sigmas_mm[self.modality]

        self.grid_spacing = phantoms.paramaters[phantom_model]['grid_spacing']

        self.preprocessed_image = self._preprocess_image(image)

        sigmas = sigma_mm / self.voxel_spacing
        logger.info('blurring with gaussian kernel, sigma=%.2f %s', sigma_mm, str(sigmas))
        self.feature_image = gaussian_filter(self.preprocessed_image, sigmas, mode='reflect')

        if limit_memory_usage: del self.preprocessed_image

        search_radius = self.grid_spacing/4
        self.points_ijk, self.label_image = peak_detection.detect_peaks(
            self.feature_image,
            self.voxel_spacing,
            search_radius,
            r_mm,
        )
        if limit_memory_usage: del self.label_image
        if limit_memory_usage: del self.feature_image

        self.points_xyz = affine.apply_affine(self.ijk_to_xyz, self.points_ijk)
        logger.info('finishing feature detection')

    def _preprocess_image(self, image):
        if self.modality == 'mri':
            logger.info('inverting image, modality=%s', self.modality)
            return invert(image)
        else:
            return image
