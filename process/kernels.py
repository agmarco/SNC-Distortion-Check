import math
import collections
import itertools

import numpy as np

from .utils import decimate


def _kernel_shape(pixel_spacing, sides):
    '''
    Figure out the kernel shape, for a given rectangular size.

    Ensures:
    - The number of elements is odd along each dimension
    - The pixel size on each end is rounded up.
    '''
    if not isinstance(sides, collections.Iterable):
        sides = itertools.repeat(sides)
    return tuple(1 + 2*math.ceil((0.5*s - 0.5*p)/p) for p, s in zip(pixel_spacing, sides))


def gaussian(pixel_spacing, sigma):
    shape = _kernel_shape(pixel_spacing, 2*2.5*sigma)
    slices = [np.linspace(-(n - 1)/2*p, (n - 1)/2*p, n) for p, n in zip(pixel_spacing, shape)]
    X, Y, Z = np.meshgrid(*slices, indexing='ij')
    kernel = np.exp(-(X**2 + Y**2 + Z**2)/(2*sigma**2))
    return kernel/np.sum(kernel)


def rectangle(pixel_spacing, sides):
    shape = _kernel_shape(pixel_spacing, sides)
    return np.ones(shape, dtype=float)


def sphere(pixel_spacing, radius, upsample=3):
    #assert all(radius > p for p in pixel_spacing)

    assert type(upsample) == int
    assert upsample >= 1
    assert upsample % 2 == 1

    corner_shape = tuple(1 + math.ceil((radius - 0.5*p)/p) for p in pixel_spacing)
    upsampled_corner_shape = tuple(upsample*n - int((upsample - 1)/2) for n in corner_shape)

    slices = [
        np.linspace(0, (n - 1)*p/upsample, n)
        for p, n
        in zip(pixel_spacing, upsampled_corner_shape)
    ]

    X, Y, Z = np.meshgrid(*slices, indexing='ij')

    upsampled_kernel_corner = np.zeros(upsampled_corner_shape)

    upsampled_kernel_corner[X**2 + Y**2 + Z**2 < radius**2] = 1

    upsampled_kernel = _fill_corners(upsampled_kernel_corner)
    kernel = decimate(upsampled_kernel, upsample)

    return kernel



def cylindrical_grid_intersection(pixel_spacing, radius, spacing, upsample=3):
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

    corner_shape = tuple(1 + math.ceil((0.5*spacing - 0.5*p)/p) for p in pixel_spacing)
    upsampled_corner_shape = tuple(upsample*n - int((upsample - 1)/2) for n in corner_shape)

    slices = [np.linspace(0, (n - 1)*p/upsample, n) for p, n in zip(pixel_spacing, upsampled_corner_shape)]

    X, Y, Z = np.meshgrid(*slices, indexing='ij')

    upsampled_kernel_corner = np.zeros(upsampled_corner_shape)

    upsampled_kernel_corner[Y**2 + Z**2 < radius**2] = 1
    upsampled_kernel_corner[X**2 + Z**2 < radius**2] = 1
    upsampled_kernel_corner[Y**2 + X**2 < radius**2] = 1

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
