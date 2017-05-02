import math
import numpy as np
from scipy.ndimage.interpolation import zoom

model = None

cube_size_ijk = 15
cube_size_mm = 15
input_shape = (cube_size_ijk, cube_size_ijk, cube_size_ijk, 1)

INTERSECTION_PROB_THRESHOLD = 0.4

model = None

def get_model():
    global model
    if model is None:
        import sys
        stdout = sys.stdout
        sys.stdout = open('/dev/null', 'w')
        from keras.models import load_model
        model = load_model('data/keras_models/v5.h5')
        sys.stdout = stdout
    return model


def remove_fps(points_ijk_unfiltered, voxels, voxel_spacing):
    model = get_model()

    num_points = points_ijk_unfiltered.shape[1]
    is_fp = np.zeros((num_points,), dtype=bool)
    windows = []
    for i, point_ijk in enumerate(points_ijk_unfiltered.T):
        window = window_from_ijk(point_ijk, voxels, voxel_spacing)
        if window is None:
            is_fp[i] = True
        else:
            window = np.expand_dims(window, axis=3)
            windows.append(window)
    probablities = model.predict_proba(np.array(windows), verbose=0)
    is_fp[~is_fp] = probablities[:, 1] < INTERSECTION_PROB_THRESHOLD

    return points_ijk_unfiltered[:, ~is_fp]


def is_grid_intersection(point_ijk, voxels, voxel_spacing):
    '''
    Given an index within the CT or MRI data, use a deep learning algorithm to
    categorize it as being "on or near" a grid intersection or not.

    This is used to provide increased specificity to our peak-finding algorithm.
    '''
    model = get_model()
    window = window_from_ijk(point_ijk, voxels, voxel_spacing)
    if window is not None:
        window = np.expand_dims(window, axis=3)
        probablities = model.predict_proba(np.array([window]), verbose=0)
        return bool(probablities[0][1] > INTERSECTION_PROB_THRESHOLD)
    else:
        return False

def zoom_like(voxels, to_shape):
    zoom_factor = np.array(to_shape) / np.array(voxels.shape)
    return zoom(voxels, zoom_factor)

def window_from_ijk(point_ijk, voxels, voxel_spacing):
    """
    Samples a window of size cube_size_mm to a window of size cube_sizexcube_sizexcube_size voxels.
    :param point_ijk:
    :param voxels:
    :param voxel_spacing:
    :return: A voxel of the shape (cube_size, cube_size, cube_size) that covers size (cube_size_mm, cube_size_mm, cube_size_mm)
    """
    i, j, k = np.round(point_ijk).astype(int)
    window_size_half = np.floor(cube_size_mm*0.5 / voxel_spacing).astype(int)
    voxel_window = voxels[
        i - window_size_half[0]:i + window_size_half[0] + 1,
        j - window_size_half[1]:j + window_size_half[1] + 1,
        k - window_size_half[2]:k + window_size_half[2] + 1
    ]
    if np.allclose(voxel_window.shape,  window_size_half*2+1):
        voxel_window = zoom_like(voxel_window, (cube_size_ijk, cube_size_ijk, cube_size_ijk))
        assert voxel_window.shape == (cube_size_ijk, cube_size_ijk, cube_size_ijk)
        return voxel_window
    else:
        return None
