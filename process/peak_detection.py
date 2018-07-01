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


def detect_peaks(data, voxel_spacing, search_radius_mm, center_of_mass_radius_mm):
    """
    Detect peaks using a local maximum filter.  A peak is defined as the
    maximum value within a binary neighborhood.  In order to provide subpixel
    resolution---once the maximum values are detected, a subvoxel peak
    detection is performed within the neighborhood of the maximum.

    Inspired by http://stackoverflow.com/a/3689710/1146963

    Returns the peak locations in ijk coordinates.
    """
    logger.info('started peak detection')
    search_neighborhood = kernels.rectangle(voxel_spacing, search_radius_mm).astype(bool)

    assert np.sum(search_neighborhood) > 1, 'search neighborhood is too small'

    peak_heights = neighborhood_peaks(data, search_neighborhood)
    num_total_peaks = np.sum(peak_heights > 0)
    logger.info('found %d peaks in total, using %s search area', num_total_peaks, search_neighborhood.shape)

    cutoff_peak_percentile = 98
    cutoff_peak = np.percentile(peak_heights[peak_heights > 0], cutoff_peak_percentile)
    cutoff_peak_fraction = 0.03
    threshold = cutoff_peak_fraction*cutoff_peak
    peaks_thresholded = peak_heights > threshold
    num_tall_peaks = np.sum(peaks_thresholded)
    logger.info('found %d peaks with amplitude greater than %f (using %f times the %f percentile peak)',
            num_tall_peaks, threshold, cutoff_peak_fraction, cutoff_peak_percentile)

    distance_to_edge = [math.ceil(s/2.0) for s in search_neighborhood.shape]
    peaks_thresholded[0:distance_to_edge[0], :, :] = False
    peaks_thresholded[:, 0:distance_to_edge[1], :] = False
    peaks_thresholded[:, :, 0:distance_to_edge[2]] = False

    peaks_thresholded[-distance_to_edge[0]:, :, :] = False
    peaks_thresholded[:, -distance_to_edge[1]:, :] = False
    peaks_thresholded[:, :, -distance_to_edge[2]:] = False

    num_tall_peaks_in_middle = np.sum(peaks_thresholded)
    logger.info('found %d peaks within %r voxels from the corresponding edges',
            num_tall_peaks_in_middle, distance_to_edge)

    labels, num_labels = ndimage.label(peaks_thresholded)
    logger.info('found %d independent peaks', num_labels)

    peaks = np.empty((len(data.shape), num_labels))
    rough_peak_locations = ndimage.center_of_mass(peaks_thresholded, labels, list(range(1, num_labels + 1)))
    num_peaks_with_region_touching_sides = 0

    com_r_px = center_of_mass_radius_mm / voxel_spacing
    logger.info('performing thresholded COM using radius = %f mm [%r]',
            center_of_mass_radius_mm, np.round(com_r_px).astype(int)),
    for i, rough_peak_location in enumerate(rough_peak_locations):
        rmin = np.round(np.maximum(rough_peak_location - com_r_px, 0)).astype(int)
        rmax = np.round(np.minimum(rough_peak_location + com_r_px + 1, np.array(data.shape))).astype(int)
        roi_com = data[rmin[0]:rmax[0], rmin[1]:rmax[1], rmin[2]:rmax[2]]
        pi, pj, pk = np.round(rough_peak_location).astype(int)
        peak_intensity = data[pi, pj, pk]
        com_offset = center_of_mass_threshold(roi_com, peak_intensity)
        if com_offset is not None:
            peaks[:, i] = rmin + com_offset
        else:
            num_peaks_with_region_touching_sides += 1
            peaks[:, i] = np.array([0, 0, 0])

    logger.info('found %d peaks after thresholded COM; finished peak detection',
            num_labels - num_peaks_with_region_touching_sides)
    return peaks, labels


def center_of_mass_threshold(roi, peak_intensity, p1=0.2, p2=0.7):
    roi_sides = [
        roi[0, :, :],
        roi[-1, :, :],
        roi[:, 0, :],
        roi[:, -1, :],
        roi[:, :, 0],
        roi[:, :, -1],
    ]
    side_maximums = [np.max(side) for side in roi_sides if np.max(side) < peak_intensity]
    if len(side_maximums) == 0:
        return None
    roi_surface_max = np.max(side_maximums)
    p = p1 if len(side_maximums) == 6 else p2
    threshold = roi_surface_max + (peak_intensity - roi_surface_max) * p
    labeled_array, num_features = ndimage.label(roi > threshold)
    labeled_array_surface = labeled_array.copy()
    labeled_array_surface[1:-1, 1:-1, 1:-1] = 0
    labels_touching_surface = np.unique(labeled_array_surface)
    labels_touching_surface = labels_touching_surface[labels_touching_surface > 0]
    if len(labels_touching_surface) != num_features - 1:
        return None
    for label in labels_touching_surface:
        labeled_array[labeled_array == label] = 0
    labeled_array[labeled_array > 0] = 1
    com = ndimage.center_of_mass(roi, labeled_array, [1])[0]
    return com
