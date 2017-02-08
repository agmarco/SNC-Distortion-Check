import math
import logging

import numpy as np
from scipy import ndimage
import pyopencl as cl

from points_utils import _valid_location
import kernels


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

    search_offsets_absolute = np.where(neighborhood)
    center = np.expand_dims((np.array(neighborhood.shape) - 1)/2, axis=1)
    offset_around_center = search_offsets_absolute - center
    search_offsets = np.vstack(offset_around_center).T.astype(np.int32)

    ctx = cl.create_some_context(interactive=True)
    queue = cl.CommandQueue(ctx)
    mf = cl.mem_flags
    hostbuf = data.astype(np.float32)
    source_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(hostbuf))
    offsets_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(search_offsets))
    res_np = np.zeros_like(hostbuf)
    res_g = cl.Buffer(ctx, mf.WRITE_ONLY, size=res_np.nbytes)
    prg_source = open("peak_detection.cl", "r").read()
    prg = cl.Program(ctx, prg_source).build()
    prg.find_peaks(queue, data.shape, None, source_g, res_g, offsets_g, np.int32(search_offsets.shape[0]))
    cl.enqueue_copy(queue, res_np, res_g)
    return res_np


def detect_peaks(data, pixel_spacing, search_radius):
    """
    Detect peaks using a local maximum filter.  A peak is defined as the
    maximum value within a binary neighborhood.  In order to provide subpixel
    resolution---once the maximum values are detected, a center-of-mass
    calculation is calculated within the same neighborhood.

    Inspired by http://stackoverflow.com/a/3689710/1146963

    Returns the peak locations in ijk coordinates.
    """
    logger.info('building neighborhood')
    search_neighborhood = kernels.sphere(pixel_spacing, search_radius, upsample=1).astype(bool)

    assert np.sum(search_neighborhood) > 1, 'search neighborhood is too small'

    logger.info('voxel-resolution peak-finding')
    peak_heights = neighborhood_peaks(data, search_neighborhood)

    logger.info('filtering out small peaks')
    threshold = 0.3*np.percentile(peak_heights[peak_heights > 0], 98)
    peaks_thresholded = peak_heights > threshold

    logger.info('removing peaks too close to edge')
    distance_to_edge = [math.ceil(s/2.0) for s in search_neighborhood.shape]
    peaks_thresholded[0:distance_to_edge[0], :, :] = False
    peaks_thresholded[:, 0:distance_to_edge[1], :] = False
    peaks_thresholded[:, :, 0:distance_to_edge[2]] = False

    peaks_thresholded[-distance_to_edge[0]:, :, :] = False
    peaks_thresholded[:, -distance_to_edge[1]:, :] = False
    peaks_thresholded[:, :, -distance_to_edge[2]:] = False

    logger.info('labeling')
    subvoxel_neighborhood = np.ones((3, 3, 3), dtype=bool)
    dilated_peaks_thresholded = ndimage.binary_dilation(peaks_thresholded, subvoxel_neighborhood)
    labels, num_labels = ndimage.label(dilated_peaks_thresholded)

    logger.info('subvoxel-resolution peak-finding')
    peaks = np.empty((len(data.shape), num_labels))
    for i, object_slices in enumerate(ndimage.measurements.find_objects(labels)):
        slice_corner_ijk = np.array([s.start for s in object_slices])
        roi = data[object_slices]
        subvoxel_offset = subvoxel_maximum(roi, 7)
        peaks[:, i] = slice_corner_ijk + subvoxel_offset

    return peaks, labels


def subvoxel_maximum(data, zoom):
    data_zoomed = ndimage.zoom(data, zoom)

    # NOTE: if there are multiple maximums, this will return the first
    maximum_indice = np.argmax(data_zoomed)
    maximum_coord = np.unravel_index(maximum_indice, data_zoomed.shape)

    return np.array([c*(s - 1)/(zs - 1) for c, s, zs in \
            zip(maximum_coord, data.shape, data_zoomed.shape)])
