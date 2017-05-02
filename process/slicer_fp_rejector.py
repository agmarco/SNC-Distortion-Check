import numpy as np
from matplotlib import patches

from process.fp_rejector import is_grid_intersection, cube_size_mm


def render_intersection_square(voxels, voxel_spacing, slicer):
    is_intersection = is_grid_intersection(slicer.cursor, voxels, voxel_spacing)
    window_size_half = np.floor(cube_size_mm*0.5 / voxel_spacing).astype(int)

    color = "green" if is_intersection else "red"
    i, j, k = slicer.cursor
    slicer.i_ax.add_patch(patches.Rectangle(
        (k - window_size_half[2], j - window_size_half[1]), window_size_half[2]*2, window_size_half[1]*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))

    slicer.j_ax.add_patch(patches.Rectangle(
        (k - window_size_half[2], i - window_size_half[0]), window_size_half[2]*2, window_size_half[0]*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))

    slicer.k_ax.add_patch(patches.Rectangle(
        (j - window_size_half[1], i - window_size_half[0]), window_size_half[1]*2, window_size_half[0]*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))
