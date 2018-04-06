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


def detect_peaks(data, voxel_spacing, search_radius, grid_radius):
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
    logger.info('found %d peaks in total, using %s search area', num_total_peaks, search_neighborhood.shape)

    threshold = 0.03*np.percentile(peak_heights[peak_heights > 0], 98)
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
    del peaks_thresholded
    labels, num_labels = ndimage.label(dilated_peaks_thresholded)
    del dilated_peaks_thresholded
    logger.info('found %d independent peaks', num_labels)

    peaks = np.empty((len(data.shape), num_labels))
    num_big_rois = 0
    for i, object_slices in enumerate(ndimage.measurements.find_objects(labels)):
        slice_corner_ijk = np.array([s.start for s in object_slices])
        roi = data[object_slices]
        if roi.size <= 5*5*5:
            zoom = 7
            subvoxel_offset = subvoxel_maximum(roi, zoom)
            subvoxel_peak = slice_corner_ijk + subvoxel_offset
            #peaks[:, i] = subvoxel_peak
            # grid_radius + peak detection uncertainty + ensure ROI surface is far enough away from intersection
            r_mm = grid_radius + 1.5 + 4.0
            r_px = r_mm / voxel_spacing
            rmin = np.round(np.maximum(subvoxel_peak - r_px, 0)).astype(int)
            rmax = np.round(np.minimum(subvoxel_peak + r_px + 1, np.array(data.shape))).astype(int)
            roi_com = data[rmin[0]:rmax[0], rmin[1]:rmax[1], rmin[2]:rmax[2]]
            pi, pj, pk = np.round(subvoxel_peak).astype(int)
            peak_intensity = data[pi, pj, pk]
            com_offset = center_of_mass_threshold(roi_com, peak_intensity)
            if com_offset is not None:
                peaks[:, i] = rmin + com_offset
            else:
                peaks[:, i] = np.array([0, 0, 0])
        else:
            # If the ROI is too big then this label is almost certainly not
            # centered on a real grid intersection.  Chances are something went
            # wrong during the 3x3 binary dilation step; the dilation step
            # grows the detected peaks so we can do a sub-voxel zoom, and it
            # also handles cases where two adjacent voxels are both the maximum
            # inside the binary search neighborhood (and thus equal).
            # Occasionally, you can have a whole bunch of peaks that are
            # adjacent, and after dilation they form a really big ROI.  If this
            # happens, we just push back the slice corner into `peaks` so that
            # the CNN can't then reject it
            num_big_rois += 1
            peaks[:, i] = np.array([0, 0, 0])

    if num_big_rois > 0:
        logger.info('skipped over %d peaks that had big rois', num_big_rois)
    logger.info('finished peak detection')
    return peaks, labels


def subvoxel_maximum(data, zoom):
    data_zoomed = ndimage.zoom(data, zoom, mode='nearest')

    # NOTE: if there are multiple maximums, this will return the first
    maximum_indice = np.argmax(data_zoomed)
    maximum_coord = np.unravel_index(maximum_indice, data_zoomed.shape)

    return np.array([c*(s - 1)/(zs - 1) for c, s, zs in zip(maximum_coord, data.shape, data_zoomed.shape)])


def center_of_mass_threshold(roi, peak_intensity, p1=0.2, p2=0.6):
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
