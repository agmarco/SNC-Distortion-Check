
import argparse
import math
import numpy as np

import file_io

from slicer import show_slices, Slicer, render_cursor

from keras.models import load_model
import matplotlib.pyplot as plt
import matplotlib.patches as patches

cube_size = 15
cube_size_half = math.floor(cube_size / 2)
input_shape = (cube_size,cube_size,cube_size,1)


def window_from_ijk(point_ijk, voxels):
    i, j, k = point_ijk.astype(int)
    voxel_window = voxels[i - cube_size_half:i + cube_size_half + 1, j - cube_size_half:j + cube_size_half + 1,
                   k - cube_size_half:k + cube_size_half + 1]
    if voxel_window.shape == (cube_size, cube_size, cube_size):
       return np.expand_dims(voxel_window, axis=3)
    else:
        return None

def predict_from_ijk(point_ijk, voxels):
    window = window_from_ijk(point_ijk, voxels)
    if window is not None:
        predictions = model.predict_classes(np.array([window]), verbose=0)
        return bool(predictions[0])
    else:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('voxels')
    args = parser.parse_args()

    voxels = file_io.load_voxels(args.voxels)['voxels']

    model = load_model('data/keras_models/v1.h5')
    model.summary()

    def render_intersection_square(slicer):
        is_intersection = predict_from_ijk(slicer.cursor, voxels)
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


