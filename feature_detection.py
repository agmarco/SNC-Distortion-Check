import numpy as np
from scipy import signal, ndimage


def invert(data):
    return 2*np.mean(data) - data


def farray(data):
    return np.array(data, dtype=float)


def convolution_feature_detection(data, nrx, nry, nrz, threshold_frac):
    inverted_data = invert(data)
    kernel = grid_intersection_kernel(nrx, nry, nrz)
    intersections = signal.fftconvolve(data, kernel, mode='same')
    intersections_thresholded = intersections > np.max(intersections)*threshold_frac
    labels, number_of_labels = ndimage.label(intersections_thresholded)
    grid_intersections = ndimage.center_of_mass(data, labels, range(1, number_of_labels + 1))
    x, y, z = zip(*grid_intersections)
    return farray(x), farray(y), farray(z)


def grid_intersection_kernel(nrx, nry, nrz):
    '''
    Generate a convolution kernel that can be used to detect "grid intersections".
    
    Grid intersections are modeled as the intersections between three cylinders.
    
    The radius of the cylinders along each dimension, nrx, nry, and nrz, are 
    specified in pixels.
    
    The kernel rejects the 0-frequency (i.e. its mean is 0), hence the values 
    outside of the grid will be negative.  In this way, matching features in the
    image will stand out against a background that is approximately 0.
    '''
    kernel_shape = tuple(round(2*4*n) for n in (nrx, nry, nrz))
    kernel = np.zeros(kernel_shape)
    X, Y, Z = np.meshgrid(*(np.linspace(-4, 4, n) for n in kernel_shape), indexing='ij')
    kernel[X**2 + Y**2 < 1] = 1
    kernel[X**2 + Z**2 < 1] = 1
    kernel[Y**2 + Z**2 < 1] = 1
    return kernel - np.mean(kernel[:])
