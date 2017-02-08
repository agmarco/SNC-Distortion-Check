import argparse
import math
import numpy as np

import file_io

from slicer import show_slices, Slicer, render_cursor

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from fp_rejector import is_grid_intersection, cube_size_half, cube_size


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('voxels')
    args = parser.parse_args()

    voxels = file_io.load_voxels(args.voxels)['voxels']

    def render_intersection_square(slicer):
        is_intersection = is_grid_intersection(slicer.cursor, voxels)
        color = "green" if is_intersection else "red"
        i,j,k = slicer.cursor
        slicer.i_ax.add_patch(patches.Rectangle(
            (k-cube_size_half,j-cube_size_half), cube_size, cube_size, fill=False,
            linestyle='solid',
            edgecolor=color,
            linewidth=2
        ))

        slicer.j_ax.add_patch(patches.Rectangle(
            (k-cube_size_half,i-cube_size_half), cube_size, cube_size, fill=False,
            linestyle='solid',
            edgecolor=color,
            linewidth=2
        ))

        slicer.k_ax.add_patch(patches.Rectangle(
            (j-cube_size_half,i-cube_size_half), cube_size, cube_size, fill=False,
            linestyle='solid',
            edgecolor=color,
            linewidth=2
        ))

    slicer = Slicer(voxels)
    slicer.add_renderer(render_intersection_square)
    slicer.add_renderer(render_cursor)
    slicer.draw()
    plt.show()
