import math
import numpy as np

from keras.models import load_model


cube_size = 15
cube_size_half = math.floor(cube_size/2)
input_shape = (cube_size, cube_size, cube_size, 1)

model = load_model('data/keras_models/v1.h5')


def is_grid_intersection(point_ijk, voxels):
    '''
    Given an index within the CT or MRI data, use a deep learning algorithm to
    categorize it as being "on or near" a grid intersection or not.

    This is used to provide increased specificity to our peak-finding algorithm.
    '''
    window = _window_from_ijk(point_ijk, voxels)
    if window is not None:
        predictions = model.predict_classes(np.array([window]), verbose=0)
        return bool(predictions[0])
    else:
        return False


def _window_from_ijk(point_ijk, voxels):
    i, j, k = point_ijk.astype(int)
    voxel_window = voxels[
        i - cube_size_half:i + cube_size_half + 1,
        j - cube_size_half:j + cube_size_half + 1,
        k - cube_size_half:k + cube_size_half + 1
    ]

    if voxel_window.shape == (cube_size, cube_size, cube_size):
        return np.expand_dims(voxel_window, axis=3)
    else:
        return None
