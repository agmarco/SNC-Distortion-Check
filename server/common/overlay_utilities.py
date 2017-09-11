import logging

import numpy as np
import scipy.interpolate
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

GRADIENT_WIDTH = 10
GRADIENT_LENGTH = 90
GRADIENT_TOP_IDX = 5
GRADIENT_BOTTOM_IDX = 95


def add_colorbar_to_slice(voxel_slice, max_distortion, units='mm'):
    slice_shape = voxel_slice.shape
    if slice_shape[0] < 200 or slice_shape[1] < 200:
        logger.info('Not adding colorbar because slice shape is too small %s', slice_shape)
        return

    max_val = np.round(np.max(voxel_slice), decimals=1)
    colorbar = np.zeros((100, 60))
    gradient = np.linspace(max_val, 0, GRADIENT_LENGTH) * np.ones((GRADIENT_WIDTH, GRADIENT_LENGTH))
    colorbar[5:(GRADIENT_LENGTH+5), 10:(GRADIENT_WIDTH+10)] = gradient.T

    colorbar_img = Image.fromarray(colorbar)
    colorbar_canvas = ImageDraw.Draw(colorbar_img)
    add_unit_labels(colorbar_canvas, max_val, max_distortion, units)
    add_gradient_ticks(colorbar_canvas, max_val)

    colorbar = np.array(colorbar_img) * np.ones((100, 60))
    colorbar_area = voxel_slice[:100, :60]
    colorbar_area[colorbar != 0] = colorbar[colorbar != 0]
    colorbar_area[GRADIENT_BOTTOM_IDX-1, 10:(GRADIENT_WIDTH+10)] = np.zeros(GRADIENT_WIDTH)


def add_unit_labels(canvas, max_val, max_distortion, units='mm'):
    canvas.text((21, 0), str(max_distortion)+units, fill=max_val)
    canvas.text((21, 85), "0"+units, fill=max_val)


def add_gradient_ticks(canvas, max_val):
    number_of_ticks = 6
    tick_indices = np.linspace(GRADIENT_TOP_IDX, GRADIENT_BOTTOM_IDX-1, number_of_ticks)
    for idx, coord in enumerate(tick_indices):
        if idx == 0 or idx == len(tick_indices)-1:
            tick_coords = (1, coord, 7, coord)
        else:
            tick_coords = (3, coord, 7, coord)
        canvas.line(tick_coords, fill=max_val)
    canvas.line((7, tick_indices[0], 7, tick_indices[-1]), fill=max_val)


def convex_hull_region(points, grid_ranges):
    # HACK: use scipy's interpolation to indirectly find the convex hull (so we
    # can set values outside of it to zero); will swap this out once
    # naturalneighbor supports more extrapolation handling approaches

    grids = tuple(np.mgrid[
        grid_ranges[0][0]:grid_ranges[0][1]:grid_ranges[0][2],
        grid_ranges[1][0]:grid_ranges[1][1]:grid_ranges[1][2],
        grid_ranges[2][0]:grid_ranges[2][1]:grid_ranges[2][2],
    ])

    num_points, num_dimensions = points.shape
    assert num_dimensions == 3
    assert num_points >= 4
    values = np.zeros(num_points)
    interp_values = scipy.interpolate.griddata(points, values, grids, method='linear')

    return ~np.isnan(interp_values)
