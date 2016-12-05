import math

import numpy as np
from scipy import signal, ndimage

import affine
from utils import invert, unsharp_mask


def convolution_feature_detection(data, kernel, threshold_frac):
    '''
    Subtracting out the mean ensures that the kernel rejects the 0-frequency
    (i.e. its mean is 0), hence the values outside of the grid will be
    negative.  In this way, matching features in the image will stand out
    against a background that is approximately 0.
    '''
    zero_mean_kernel = kernel - np.mean(kernel)
    intersections = signal.fftconvolve(data, zero_mean_kernel, mode='same')

    threshold = np.percentile(intersections, 98)*threshold_frac
    assert threshold > 0

    intersections[intersections < threshold] = - 100
    import slicer; slicer.show_slices(intersections)
    intersections_thresholded = intersections > threshold

    labels, number_of_labels = ndimage.label(intersections_thresholded)
    grid_intersections = ndimage.center_of_mass(intersections, labels, range(1, number_of_labels + 1))
    x, y, z = zip(*grid_intersections)
    return np.array([x, y, z], dtype=float)


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


def detect_features(voxels, ijk_to_xyz):
    # TODO: derive the kernel from the phantom model
    pixel_spacing = affine.pixel_spacing(ijk_to_xyz)
    radius = 3.0  # the two supported phantoms currently have a 3 mm radius
    kernel = cylindrical_grid_kernel(pixel_spacing, radius)

    threshold_frac = 0.5

    # TODO: detect whether we need to invert here
    inverted_voxels = invert(voxels)
    blurred_voxels = unsharp_mask(inverted_voxels, 10*radius/pixel_spacing, 1.0)

    points_ijk = convolution_feature_detection(blurred_voxels, kernel, threshold_frac)
    points_xyz = affine.apply_affine(ijk_to_xyz, points_ijk)

    return points_xyz
