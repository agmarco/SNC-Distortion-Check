import logging
import math

import numpy as np
from scipy import ndimage

from process import kernels

logger = logging.getLogger(__name__)


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
    if len(data.shape) != 3:
        raise ValueError("Data array must have three dimensions")
    if len(neighborhood.shape) != 3:
        raise ValueError("Neighborhood array must have three dimensions")
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


def detect_peaks(data, voxel_spacing, search_radius):
    """
    Detect peaks using a local maximum filter.  A peak is defined as the
    maximum value within a binary neighborhood.  In order to provide subpixel
    resolution---once the maximum values are detected, a subvoxel peak
    detection is performed within the neighborhood of the maximum.

    Inspired by http://stackoverflow.com/a/3689710/1146963

    Returns the peak locations in ijk coordinates.
    """
    logger.info('started peak detection')
    search_neighborhood = kernels.rectangle(voxel_spacing, search_radius).astype(bool)

    assert np.sum(search_neighborhood) > 1, 'search neighborhood is too small'

    peak_heights = neighborhood_peaks(data, search_neighborhood)
    num_total_peaks = np.sum(peak_heights > 0)
    logger.info('found %d peaks in total', num_total_peaks)

    threshold = 0.1*np.percentile(peak_heights[peak_heights > 0], 98)
    peaks_thresholded = peak_heights > threshold
    num_tall_peaks = np.sum(peaks_thresholded)
    logger.info('found %d peaks with amplitude greater than %f', num_tall_peaks, threshold)

    distance_to_edge = [math.ceil(s/2.0) for s in search_neighborhood.shape]
    peaks_thresholded[0:distance_to_edge[0], :, :] = False
    peaks_thresholded[:, 0:distance_to_edge[1], :] = False
    peaks_thresholded[:, :, 0:distance_to_edge[2]] = False

    peaks_thresholded[-distance_to_edge[0]:, :, :] = False
    peaks_thresholded[:, -distance_to_edge[1]:, :] = False
    peaks_thresholded[:, :, -distance_to_edge[2]:] = False

    num_tall_peaks_in_middle = np.sum(peaks_thresholded)
    logger.info('found %d peaks within %r voxels from the corresponding edges', num_tall_peaks_in_middle, distance_to_edge)

    subvoxel_neighborhood = np.ones((3, 3, 3), dtype=bool)
    dilated_peaks_thresholded = ndimage.binary_dilation(peaks_thresholded, subvoxel_neighborhood)
    labels, num_labels = ndimage.label(dilated_peaks_thresholded)
    logger.info('found %d independent peaks', num_labels)

    peaks = np.empty((len(data.shape), num_labels))
    for i, object_slices in enumerate(ndimage.measurements.find_objects(labels)):
        slice_corner_ijk = np.array([s.start for s in object_slices])
        roi = data[object_slices]
        zoom = 7
        subvoxel_offset = subvoxel_maximum(roi, zoom)
        peaks[:, i] = slice_corner_ijk + subvoxel_offset

    logger.info('finished peak detection')
    return peaks, labels


def subvoxel_maximum(data, zoom):
    data_zoomed = ndimage.zoom(data, zoom, mode='nearest')

    # NOTE: if there are multiple maximums, this will return the first
    maximum_indice = np.argmax(data_zoomed)
    maximum_coord = np.unravel_index(maximum_indice, data_zoomed.shape)

    return np.array([c*(s - 1)/(zs - 1) for c, s, zs in \
            zip(maximum_coord, data.shape, data_zoomed.shape)])
