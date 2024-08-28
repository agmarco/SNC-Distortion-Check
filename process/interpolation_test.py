import pytest
import numpy as np

from .interpolation import convex_hull_region


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
