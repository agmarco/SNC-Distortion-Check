import math

import numpy as np
from scipy import signal, ndimage

import affine
from utils import invert, unsharp_mask, decimate


def cylindrical_grid_kernel(pixel_spacing, radius, spacing, upsample=3):
    '''
    Generate a convolution kernel that can be used to detect "cylindrical grid
    intersections".  This is a set of cylinders that are lined up on a three
    dimensional grid.  The grid spacing is the distance in mm between the
    cylinders (assumed to be the same along each dimension).  The grid radius
    is the radius of the grid spacing (also assumed to be the same along each
    axis).
    '''
    assert spacing > 2*radius
    assert type(upsample) == int
    assert upsample >= 1
    assert upsample % 2 == 1

    corner_shape = tuple(1 + math.ceil((1.5*spacing - 0.5*p)/p) for p in pixel_spacing)
    upsampled_corner_shape = tuple(upsample*n - int((upsample - 1)/2) for n in corner_shape)

    slices = [np.linspace(0, (n - 1)*p/upsample, n) for p, n in zip(pixel_spacing, upsampled_corner_shape)]

    X, Y, Z = np.meshgrid(*slices, indexing='ij')

    upsampled_kernel_corner = np.zeros(upsampled_corner_shape)

    upsampled_kernel_corner[Y**2 + Z**2 < radius] = 1
    upsampled_kernel_corner[Y**2 + (Z - spacing)**2 < radius] = 1
    upsampled_kernel_corner[(Y - spacing)**2 + Z**2 < radius] = 1
    upsampled_kernel_corner[(Y - spacing)**2 + (Z - spacing)**2 < radius] = 1

    upsampled_kernel_corner[X**2 + Z**2 < radius] = 1
    upsampled_kernel_corner[X**2 + (Z - spacing)**2 < radius] = 1
    upsampled_kernel_corner[(X - spacing)**2 + Z**2 < radius] = 1
    upsampled_kernel_corner[(X - spacing)**2 + (Z - spacing)**2 < radius] = 1

    upsampled_kernel_corner[Y**2 + X**2 < radius] = 1
    upsampled_kernel_corner[Y**2 + (X - spacing)**2 < radius] = 1
    upsampled_kernel_corner[(Y - spacing)**2 + X**2 < radius] = 1
    upsampled_kernel_corner[(Y - spacing)**2 + (X - spacing)**2 < radius] = 1

    upsampled_kernel = _fill_corners(upsampled_kernel_corner)
    kernel = decimate(upsampled_kernel, upsample)

    return kernel


def _fill_corners(corner):
    '''
    Given 1 corner of a symmetrical 3D kernel, reflect and copy the corner into
    the other 7 corners.  Assumes the first corner is oriented in the +++
    quadrant.
    '''
    full_shape = tuple(1 + 2*(n - 1) for n in corner.shape)
    full = np.empty(full_shape, dtype=corner.dtype)
    ni, nj, nk = corner.shape
    full[ni-1:, nj-1:, nk-1:] = corner                    # +++
    full[ni:, nj:, :nk] = corner[1:, 1:, -1::-1]          # ++-
    full[ni:, :nj, nk:] = corner[1:, -1::-1, 1:]          # +-+
    full[:ni, nj:, nk:] = corner[-1::-1, 1:, 1:]          # -++
    full[:ni, :nj, nk:] = corner[-1::-1, -1::-1, 1:]      # --+
    full[:ni, nj:, :nk] = corner[-1::-1, 1:, -1::-1]      # -+-
    full[ni:, :nj, :nk] = corner[1:, -1::-1, -1::-1]      # +--
    full[:ni, :nj, :nk] = corner[-1::-1, -1::-1, -1::-1]  # ---
    return full


class FeatureDetector:
    def __init__(self, image, ijk_to_xyz):
        # TODO: detect whether we need to invert here
        self.image = invert(image)

        self.ijk_to_xyz = ijk_to_xyz

        # TODO: derive the kernel from the phantom model
        # the two supported phantoms currently have a 3 mm radius
        self.grid_radius = 1.5
        self.grid_spacing = 15.0

        self.pixel_spacing = affine.pixel_spacing(self.ijk_to_xyz)

        self.threshold_max_percentile = 98
        self.threshold_frac = 0.90

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
        return cylindrical_grid_kernel(self.pixel_spacing, self.grid_radius, self.grid_spacing)

    def preprocess(self):
        return self.image
        #return unsharp_mask(self.image, 10*self.grid_radius/self.pixel_spacing, 1.0)

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
