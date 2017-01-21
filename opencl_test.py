from pyopencl.tools import pytest_generate_tests_for_pyopencl as pytest_generate_tests

import pyopencl as cl
import numpy as np

from opencl import find_peaks


def test_peak_all_zeros():
    voxels = np.zeros((3,3,3))
    search_neighborhood = np.ones_like(voxels)
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(voxels, peaks)

def test_peak_all_ones():
    voxels = np.ones((3,3,3))
    search_neighborhood = np.ones_like(voxels)
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(np.zeros((3,3,3)), peaks)

def test_peak_simple_center():
    voxels = np.zeros((3,3,3))
    voxels[1, 1, 1] = 1
    search_neighborhood = np.ones_like(voxels)
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(voxels, peaks)

def test_peak_simple_corner():
    voxels = np.zeros((3,3,3))
    voxels[0, 0, 0] = 1
    search_neighborhood = np.ones_like(voxels)
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(voxels, peaks)

def test_peak_height():
    voxels = np.ones((3,3,3))
    voxels[1, 1, 1] = 2
    voxels[0, 0, 0] = 0

    expected_voxels = np.zeros((3,3,3))
    expected_voxels[1, 1, 1] = 2

    search_neighborhood = np.ones_like(voxels)
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(expected_voxels, peaks)

def test_tiled_peaks():
    voxels = np.zeros((3,3,3))
    voxels[1, 1, 1] = 1
    voxels = np.tile(voxels, (3,3,3))
    assert voxels.shape == (9,9,9)
    search_neighborhood = np.ones((3,3,3))
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(voxels, peaks)

def test_tiled_peaks_2():
    voxels = np.zeros((3,3,3))
    voxels[1, 1, 1] = 1
    voxels = np.tile(voxels, (3,3,3))
    voxels[4, 4, 4] = 2
    assert voxels.shape == (9,9,9)
    search_neighborhood = np.ones((3,3,3))
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(voxels, peaks)

def test_tiled_peaks_3():
    voxels = np.zeros((3,3,3))
    voxels[1, 1, 1] = 1
    voxels = np.tile(voxels, (3,3,3))
    voxels[4, 4, 4] = 2
    assert voxels.shape == (9,9,9)
    search_neighborhood = np.ones((7,7,7))
    expected_peaks = np.zeros_like(voxels)
    expected_peaks[4, 4, 4] = 2
    peaks = find_peaks(voxels, search_neighborhood)
    assert np.allclose(expected_peaks, peaks)
