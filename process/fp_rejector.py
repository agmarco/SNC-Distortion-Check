import math
import numpy as np

model = None

cube_size = 15
cube_size_half = math.floor(cube_size/2)
input_shape = (cube_size, cube_size, cube_size, 1)

INTERSECTION_PROB_THRESHOLD = 0.4

model = None

def get_model():
    global model
    if model is None:
        import sys
        stdout = sys.stdout
        sys.stdout = open('/dev/null', 'w')
        from keras.models import load_model
        model = load_model('data/keras_models/v2.h5')
        sys.stdout = stdout
    return model


def remove_fps(points_ijk_unfiltered, voxels):
    model = get_model()

    num_points = points_ijk_unfiltered.shape[1]
    is_fp = np.zeros((num_points,), dtype=bool)
    windows = []
    for i, point_ijk in enumerate(points_ijk_unfiltered.T):
        window = _window_from_ijk(point_ijk, voxels)
        if window is None:
            is_fp[i] = True
        else:
            windows.append(window)

    probablities = model.predict_proba(np.array(windows), verbose=0)
    is_fp[~is_fp] = probablities[:, 1] < INTERSECTION_PROB_THRESHOLD

    return points_ijk_unfiltered[:, ~is_fp]


def is_grid_intersection(point_ijk, voxels):
    '''
    Given an index within the CT or MRI data, use a deep learning algorithm to
    categorize it as being "on or near" a grid intersection or not.

    This is used to provide increased specificity to our peak-finding algorithm.
    '''
    model = get_model()

    window = _window_from_ijk(point_ijk, voxels)
    if window is not None:
        probablities = model.predict_proba(np.array([window]), verbose=0)
        return bool(probablities[0][1] > INTERSECTION_PROB_THRESHOLD)
    else:
        return False


def _window_from_ijk(point_ijk, voxels):
    i, j, k = np.round(point_ijk).astype(int)
    voxel_window = voxels[
        i - cube_size_half:i + cube_size_half + 1,
        j - cube_size_half:j + cube_size_half + 1,
        k - cube_size_half:k + cube_size_half + 1
    ]

    if voxel_window.shape == (cube_size, cube_size, cube_size):
        return np.expand_dims(voxel_window, axis=3)
    else:
        return None