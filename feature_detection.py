import math

import numpy as np
from scipy import signal, ndimage

import affine
from utils import invert, unsharp_mask


def cylindrical_grid_kernel(pixel_spacing, radius):
    '''
    Generate a convolution kernel that can be used to detect "cylindrical grid
    intersections".

    The radius of the cylinders is assumed to be the same along each dimension.
    '''

    kernel_shape = tuple(math.ceil(2*4*radius/s) for s in pixel_spacing)
    kernel = np.zeros(kernel_shape)
    X, Y, Z = np.meshgrid(*(np.linspace(-4, 4, n) for n in kernel_shape), indexing='ij')
    kernel[X**2 + Y**2 < 1] = 1
    kernel[X**2 + Z**2 < 1] = 1
    kernel[Y**2 + Z**2 < 1] = 1
    return kernel


class FeatureDetector:
    def __init__(self, image, ijk_to_xyz):
        # TODO: detect whether we need to invert here
        self.image = invert(image)

        self.ijk_to_xyz = ijk_to_xyz

        # TODO: derive the kernel from the phantom model
        # the two supported phantoms currently have a 3 mm radius
        self.grid_radius = 3.0

        self.pixel_spacing = affine.pixel_spacing(self.ijk_to_xyz)

        self.threshold_max_percentile = 98
        self.threshold_frac = 0.5

    def run(self):
        self.kernel = self.build_kernel()
        self.preprocessed_image = self.preprocess()
        self.zero_mean_kernel = self.kernel - np.mean(self.kernel)
        self.feature_image = signal.fftconvolve(self.preprocessed_image, self.zero_mean_kernel, mode='same')
        self.label_image, self.num_labels = self.label()
        self.points_ijk = self.points()
        self.points_xyz = affine.apply_affine(self.ijk_to_xyz, self.points_ijk)
        return self.points_xyz

    def build_kernel(self):
        return cylindrical_grid_kernel(self.pixel_spacing, self.grid_radius)

    def preprocess(self):
        return unsharp_mask(self.image, 10*self.grid_radius/self.pixel_spacing, 1.0)

    def label(self):
        self.threshold = np.percentile(self.feature_image, self.threshold_max_percentile)*self.threshold_frac
        assert self.threshold > 0
        tresholded_image = self.feature_image > self.threshold
        return ndimage.label(tresholded_image)

    def points(self):
        label_list = range(1, self.num_labels + 1)
        points = ndimage.center_of_mass(self.feature_image, self.label_image, label_list)
        x, y, z = zip(*points)
        return np.array([x, y, z], dtype=float)
