import pytest
import numpy as np

from ..overlay_utilities import add_colorbar_to_slice, convex_hull_region
from ..overlay_utilities import (GRADIENT_WIDTH, GRADIENT_LENGTH,
                                 GRADIENT_TOP_IDX, GRADIENT_BOTTOM_IDX)

def test_dicom_overlay():
    max_value = 20
    test_volume = np.ones((700,512,512))*(max_value/2)
    test_volume[:,300,300] = max_value
    max_value_in_xz = np.max(test_volume, 1)
    max_value = np.max(max_value_in_xz, 1) 
    for slice_arr in test_volume:
        slice_arr = add_colorbar_to_slice(slice_arr, np.max(slice_arr))
    new_colorbar_top = test_volume[:, GRADIENT_TOP_IDX, 10:(GRADIENT_WIDTH+10)]
    expected_colorbar_top = max_value * np.ones((GRADIENT_WIDTH, len(max_value)))
    new_colorbar_bottom = test_volume[:, GRADIENT_BOTTOM_IDX-1, 10:(GRADIENT_WIDTH+10)]
    assert False not in np.equal(new_colorbar_top, expected_colorbar_top.T)
    assert False not in np.equal(new_colorbar_bottom, 0)


def test_dicom_overlay_ticks_aligned():
    max_value = 20
    test_volume = np.ones((700,512,512))*(max_value/2)
    test_volume[:,300,300] = max_value
    for slice_arr in test_volume:
        slice_arr = add_colorbar_to_slice(slice_arr, max_value)
    top_tick = test_volume[:, GRADIENT_TOP_IDX, 1:8]
    bottom_tick = test_volume[:, GRADIENT_BOTTOM_IDX-1, 1:8]
    assert False not in np.equal(top_tick, max_value)
    assert False not in np.equal(bottom_tick, max_value)


def test_dicom_overlay_not_added_when_slice_too_small():
    test_slice = np.random.rand(100, 140)
    original_slice = test_slice.copy()
    max_value = 20
    add_colorbar_to_slice(test_slice, max_value)
    assert np.array_equal(original_slice, test_slice)


@pytest.fixture
def unit_cube():
    return np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 1],
    ], dtype=np.float)


def test_convex_hull_region_cube_in_corner(unit_cube):
    grid_ranges = [[0, 2, 3j], [0, 2, 3j], [0, 2, 3j]]
    expected_output = np.zeros((3, 3, 3), dtype=np.bool)
    expected_output[:2, :2, :2] = True
    actual_output = convex_hull_region(unit_cube, grid_ranges)
    assert np.array_equal(expected_output, actual_output)


def test_convex_hull_region_cube_in_center(unit_cube):
    grid_ranges = [[-1, 2, 4j], [-1, 2, 4j], [-1, 2, 4j]]
    expected_output = np.zeros((4, 4, 4), dtype=np.bool)
    expected_output[1:3, 1:3, 1:3] = True
    actual_output = convex_hull_region(unit_cube, grid_ranges)
    assert np.array_equal(expected_output, actual_output)


def test_convex_hull_region_cube_in_center_corner_removed(unit_cube):
    grid_ranges = [[-1, 2, 4j], [-1, 2, 4j], [-1, 2, 4j]]
    expected_output = np.zeros((4, 4, 4), dtype=np.bool)
    expected_output[1:3, 1:3, 1:3] = True
    expected_output[2, 2, 2] = False
    unit_cube_wihout_111_corner = unit_cube[:-1]
    actual_output = convex_hull_region(unit_cube_wihout_111_corner, grid_ranges)
    assert np.array_equal(expected_output, actual_output)
