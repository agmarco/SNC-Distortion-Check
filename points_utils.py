import math
import logging

import numpy as np
from orderedset import OrderedSet
from scipy.spatial import KDTree
from scipy import ndimage
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, binary_erosion, iterate_structure

import kernels

logger = logging.getLogger(__name__)


def closest(A, point):
    dims, num_points = A.shape
    assert dims == 3
    assert num_points >= 1

    distances_squared = np.sum((A - point.reshape((3, 1)))**2, axis=0)
    closest_indice = np.argmin(distances_squared) 
    distance = math.sqrt(distances_squared[closest_indice])
    return closest_indice, A[:, closest_indice], distance


def categorize(A, B, rho):
    '''
    Given an array of locations of detected features, B, and an array of known
    feature locations that HAVE BEEN REGISTERED into B's coordinate system,
    A, separate the points into three groups:

    - false negatives (points in A that should have a matching point in B, but don't)
    - matching points (points in A that have matching points in B)
    - false positives (points in B that have no matching point in A)

    These results are returned as four arrays

    1. FN_A (3 x O)
    2. TP_A (3 x M)
    3. TP_B (3 x M)
    4. FP_B (3 x N)

    where A is (3 x M+O) and B is (3 x N+M).  Each column of TP_A is a point
    that matches the corresponding column in TP_B.

    Two points, a and b, are matching if

    - they are within rho(|b|) distance from one another
    - neither point has already been matched
    - matching them minimizes the total sum of distances of all matched points.

    The last condition means that, in general, each point in A will be matched
    to the closest point in B.  The only exception to this is if there is a
    point, b in B, that could match multiples points in A.  In this case, b
    will be matched with whichever point in A minimizes the total sum of
    distances.

    In the case that there is a point in B that is equidistant from two points
    in A (both of which can ONLY match this one point), then the matching will
    be arbitrary.
    '''
    _, num_b = B.shape
    assert _ == 3
    _, num_a = A.shape
    assert _ == 3

    kdtree = KDTree(B.T)

    a_b_distances, closest_b_indices = kdtree.query(A.T)

    seen_b_indices = OrderedSet()
    seen_a_indices = OrderedSet()

    TP_A_indices = np.zeros(num_a, dtype=bool)
    TP_B_indices = np.zeros(num_b, dtype=bool)

    a_indices = range(num_a)
    for a_indice, b_indice, a_b_distance in zip(a_indices, closest_b_indices, a_b_distances):
        b = B[:, b_indice]
        b_mag = np.linalg.norm(b)
        if a_b_distance < rho(b_mag):
            TP_A_indices[a_indice] = True
            TP_B_indices[b_indice] = True

            if b_indice in seen_b_indices:
                continue
                #raise NotImplementedError("Multiple points in A match same point in B")
            else:
                seen_b_indices.add(b_indice)
                seen_a_indices.add(a_indice)

    FN_A = A[:, ~TP_A_indices]
    TP_A = A[:, seen_a_indices]
    TP_B = B[:, seen_b_indices]
    FP_B = B[:, ~TP_B_indices]

    #assert FN_A.shape[1] + TP_A.shape[1] == num_a
    #assert FP_B.shape[1] + TP_B.shape[1] == num_b

    return FN_A, TP_A, TP_B, FP_B


def neighborhood_peaks(data, neighborhood):
    '''
    Given an array of data and a binary array defining a "neighborhood" to
    detect peaks within, return an array of the same size and dtype as data
    whose values are:

    - 0 if the given point is not the maximum value within a neighborhood
      centered at this location
    - the height of the peak (defined as the maximum - minimum value in the
      neighborhood).

    Note that the neighborhood must have the same number of dimensions as
    "data", it must have an odd number of components along each dimension, and
    the neighborhood must be smaller (or equal) to the data array along each
    dimension.
    '''
    if neighborhood.dtype != bool:
        raise ValueError("Neighborhood must be a boolean array")
    if len(data.shape) != len(neighborhood.shape):
        raise ValueError("Neighborhood and data array must have same number of dimensions")
    if not all(nd <= dd for nd, dd in zip(neighborhood.shape, data.shape)):
        raise ValueError("Neighborhood can not be larger than the data array")
    if not all(nd % 2 for nd in neighborhood.shape):
        raise ValueError("Neighborhood must have an odd number of components in each dimension")

    maximums = ndimage.maximum_filter(data, footprint=neighborhood, mode='constant')
    peak_locations = maximums == data

    minimums = ndimage.minimum_filter(data, footprint=neighborhood, mode='constant')

    peak_heights = np.zeros_like(data)
    peak_heights[peak_locations] = maximums[peak_locations] - minimums[peak_locations]

    return peak_heights


def detect_peaks(data, pixel_spacing, search_radius, COM_radius):
    """
    Detect peaks using a local maximum filter.  A peak is defined as the
    maximum value within a binary neighborhood.  In order to provide subpixel
    resolution---once the maximum values are detected, a center-of-mass
    calculation is calculated within the same neighborhood.

    Inspired by http://stackoverflow.com/a/3689710/1146963

    Returns the peak locations in ijk coordinates.

    Note that there are some performance optimizations that make the
    implementation more complex.

    In particular, for larger kernel sizes, we perform a first pass search
    using a smaller kernel.  This is because the maximum_filter is slow with
    larger kernel sizes.
    """
    logger.info('building neighborhood')
    search_neighborhood = kernels.sphere(pixel_spacing, search_radius, upsample=1)

    logger.info('finding neighborhood peaks')
    peak_heights = neighborhood_peaks(data, search_neighborhood)

    logger.info('filtering out small peaks')
    threshold = 0.2*np.percentile(peak_heights[peak_heights > 0], 98)
    peaks_thresholded = peak_heights > threshold

    logger.info('labeling')
    COM_neighborhood = kernels.sphere(pixel_spacing, COM_radius, upsample=1)
    labels, num_labels = ndimage.label(ndimage.binary_dilation(peaks_thresholded, COM_neighborhood))

    logger.info('center of mass calculations')
    label_list = range(1, num_labels + 1)
    points = ndimage.center_of_mass(data, labels, label_list)
    coords = zip(*points)
    return np.array(list(list(c) for c in coords), dtype=float), labels


def _valid_location(location, data_shape, kernel_shape):
    '''
    Is the location such that the kernel, when centered there, will fully fit
    inside the data?
    '''
    return all(d - (k - 1)/2 > l >= (k - 1)/2 for l, d, k in zip(location, data_shape, kernel_shape))


def metrics(FN_A, TP_A, TP_B, FP_B):
    '''
    Our standard metrics for comparing sets of points.
    '''
    num_points_a = len(FN_A.T) + len(TP_A.T)
    num_points_b = len(FP_B.T) + len(TP_B.T)

    assert num_points_a > 0

    if len(TP_B.T) == 0:
        return float('NaN'), 0.0, 1.0, float('inf')
    else:

        error_vectors = (TP_A - TP_B).T
        FLEs = np.linalg.norm(error_vectors, axis=1)
        FLE_mean = np.mean(FLEs)

        TPF = len(TP_A.T)/num_points_a
        FNF = len(FN_A.T)/num_points_a
        FPF = len(FP_B.T)/num_points_b

        return FLE_mean, TPF, FNF, FPF
