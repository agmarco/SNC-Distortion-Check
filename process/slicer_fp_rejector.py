import numpy as np
from matplotlib import patches

from process.fp_rejector import is_grid_intersection, cube_size_mm


def render_intersection_square(voxels, voxel_spacing, phantom_model, slicer):
    is_intersection = is_grid_intersection(slicer.cursor, voxels, voxel_spacing, phantom_model)
    window_size_half = np.floor(cube_size_mm*0.5 / voxel_spacing).astype(int)

    color = "green" if is_intersection else "red"
    i, j, k = slicer.cursor
    di, dj, dk = window_size_half
    slicer.i_ax.add_patch(patches.Rectangle(
        (i - di, j - dj), di*2, dj*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))

    slicer.j_ax.add_patch(patches.Rectangle(
        (i - di, k - dk), di*2, dk*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))

    slicer.k_ax.add_patch(patches.Rectangle(
        (j - dj, k - dk), dj*2, dk*2, fill=False,
        linestyle='solid',
        edgecolor=color,
        linewidth=2
    ))
