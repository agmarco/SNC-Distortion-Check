import logging

import numpy as np
#import naturalneighbor
import scipy.interpolate

from process.affine import scaling, translation

logger = logging.getLogger(__name__)


def interpolate_distortion(TP_A_S, error_mags, grid_density_mm):
    # TODO: add good docstring
    # TODO: add buffer so that we don't have natural neighbor boundary artifacts
    coord_min_xyz = np.amin(TP_A_S, axis=1)
    coord_max_xyz = np.amax(TP_A_S, axis=1)

    interp_grid_ranges = [
        [coord_min_xyz[0], coord_max_xyz[0], grid_density_mm],
        [coord_min_xyz[1], coord_max_xyz[1], grid_density_mm],
        [coord_min_xyz[2], coord_max_xyz[2], grid_density_mm],
    ]
    output_dimensions = (coord_max_xyz - coord_min_xyz)/grid_density_mm
    msg = "Performing naturalneighbor interpolation from %fx%fx%f to %fx%fx%f with %f resolution"
    logger.info(msg, *coord_min_xyz, *coord_max_xyz, grid_density_mm)

    # interpolated_error_mags = naturalneighbor.griddata(TP_A_S.T, error_mags.T, interp_grid_ranges)
    grids = tuple(np.mgrid[
        interp_grid_ranges[0][0]:interp_grid_ranges[0][1]:interp_grid_ranges[0][2],
        interp_grid_ranges[1][0]:interp_grid_ranges[1][1]:interp_grid_ranges[1][2],
        interp_grid_ranges[2][0]:interp_grid_ranges[2][1]:interp_grid_ranges[2][2],
    ])
    interpolated_error_mags = scipy.interpolate.griddata(TP_A_S.T, error_mags.T, grids, method='nearest')

    extrapolated_region = ~convex_hull_region(TP_A_S.T, interp_grid_ranges)
    logger.info("Zeroing %d of %d extrapolated voxels in the overlay",
            np.sum(extrapolated_region), extrapolated_region.size)

    interpolated_error_mags[extrapolated_region] = 0.0
    ijk_to_xyz = translation(*list(coord_min_xyz)) @ scaling(grid_density_mm, grid_density_mm, grid_density_mm)
    return ijk_to_xyz, interpolated_error_mags


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
