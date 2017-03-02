import logging
import os

from scipy import signal

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

    def run(self):
        logger.info('building kernel')
        self.kernel = self.build_kernel()
        logger.info('preprocessing image')
        self.preprocessed_image = self.preprocess()
        logger.info('convolving with feature kernel')
        self.feature_image = signal.fftconvolve(self.preprocessed_image, self.kernel, mode='same')

        logger.info('detecting peaks')
        search_radius = self.grid_spacing/3.0
        points_ijk_unfiltered, self.label_image = peak_detection.detect_peaks(
            self.feature_image,
            self.pixel_spacing,
            search_radius,
        )

        logger.info('discarding false positives using neural network')

        # TODO: switch to using original image after updating the model
        inverted_image = invert(self.image)
        self.points_ijk = remove_fps(points_ijk_unfiltered, inverted_image)
        assert self.points_ijk.shape[1] > 0, 'All of the points were filtered out!'

        self.points_xyz = affine.apply_affine(self.ijk_to_xyz, self.points_ijk)
        return self.points_xyz

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
            self.grid_radius
        )

    def preprocess(self):
        if self.modality == 'MR':
            return invert(self.image)
        else:
            return self.image
