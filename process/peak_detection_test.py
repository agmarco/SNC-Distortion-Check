import math

import numpy as np
import pytest
from numpy.testing import assert_allclose

from process.peak_detection import neighborhood_peaks, detect_peaks


class TestDetectPeaks:
    def test_bad_neighborhood_dtype(self):
        data = np.atleast_3d([0, 0])
        neighborhood = np.atleast_3d(1.0)
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_bad_number_of_dimensions(self):
        data = np.array([[0, 0]])
        neighborhood = np.array([[True]])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_even_length(self):
        data = np.atleast_3d([0, 0])
        neighborhood = np.atleast_3d([False, True])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_large_neighborhood(self):
        data = np.atleast_3d([0, 0])
        neighborhood = np.atleast_3d([True, True, True])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_1px_neighborhood_3d(self):
        data = np.random.rand(3, 3, 3)
        neighborhood = np.atleast_3d(True)
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, np.zeros_like(data))

    def test_simple_vertical_neighborhood(self):
        data = np.array([[
            [0, 0.5, 0, 0],
            [0,   1, 0, 0],
            [0, 0.5, 0, 2],
        ]])
        neighborhood = np.array([[[True], [True], [True]]])
        expected_peaks = np.array([[
            [0,   0, 0, 0],
            [0, 0.5, 0, 0],
            [0,   0, 0, 2],
        ]])
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, expected_peaks)

    def test_simple_horizontal_neighborhood(self):
        data = np.array([[
            [0, 0.5, 0, 0],
            [0,   1, 0, 0],
            [0, 0.5, 0, 2],
        ]])
        expected_peaks = np.array([[
            [0, 0.5, 0, 0],
            [0,   1, 0, 0],
            [0, 0.5, 0, 2],
        ]])
        neighborhood = np.array([[[True, True, True]]])
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, expected_peaks)

    def test_peak_all_zeros(self):
        voxels = np.zeros((3,3,3))
        search_neighborhood = np.ones(voxels.shape, dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(voxels, peaks)

    def test_peak_all_ones(self):
        voxels = np.ones((3,3,3))
        search_neighborhood = np.ones(voxels.shape, dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(np.zeros((3,3,3)), peaks)

    def test_peak_simple_center(self):
        voxels = np.zeros((3,3,3))
        voxels[1, 1, 1] = 1
        search_neighborhood = np.ones(voxels.shape, dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(voxels, peaks)

    def test_peak_simple_corner(self):
        voxels = np.zeros((3,3,3))
        voxels[0, 0, 0] = 1
        search_neighborhood = np.ones(voxels.shape, dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(voxels, peaks)

    def test_peak_height(self):
        voxels = np.ones((3,3,3))
        voxels[1, 1, 1] = 2
        voxels[0, 0, 0] = 0

        expected_voxels = np.zeros((3,3,3))
        expected_voxels[1, 1, 1] = 2

        search_neighborhood = np.ones(voxels.shape, dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(expected_voxels, peaks)

    def test_tiled_peaks(self):
        voxels = np.zeros((3,3,3))
        voxels[1, 1, 1] = 1
        voxels = np.tile(voxels, (3,3,3))
        assert voxels.shape == (9,9,9)
        search_neighborhood = np.ones((3,3,3), dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(voxels, peaks)

    def test_tiled_peaks_2(self):
        voxels = np.zeros((3,3,3))
        voxels[1, 1, 1] = 1
        voxels = np.tile(voxels, (3,3,3))
        voxels[4, 4, 4] = 2
        assert voxels.shape == (9,9,9)
        search_neighborhood = np.ones((3,3,3), dtype=bool)
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(voxels, peaks)

    def test_tiled_peaks_3(self):
        voxels = np.zeros((3,3,3))
        voxels[1, 1, 1] = 1
        voxels = np.tile(voxels, (3,3,3))
        voxels[4, 4, 4] = 2
        assert voxels.shape == (9,9,9)

        search_neighborhood = np.ones((7,7,7), dtype=bool)
        expected_peaks = np.zeros_like(voxels)
        expected_peaks[4, 4, 4] = 2
        peaks = neighborhood_peaks(voxels, search_neighborhood)
        assert np.allclose(expected_peaks, peaks)


class TestDetectPeaks:
    def test_rejects_peaks_on_edge(self):
        d = np.zeros((7, 9, 11))
        d[0, 0, 0] = 1
        d[4, 4, 4] = 1
        voxel_spacing = np.array([1.0, 1.0, 1.0])
        search_radius = 1.1
        center_of_mass_radius = 11

        expected_peaks = np.array([[4, 4, 4]], dtype=float).T
        peaks, labels = detect_peaks(d, voxel_spacing, search_radius, center_of_mass_radius)
        assert_allclose(expected_peaks, peaks)

    def test_performs_subvoxel_peak_detection(self):
        d = np.zeros((7, 9, 11))
        d[4, 4, 4] = 1
        d[4, 4, 5] = 1
        voxel_spacing = np.array([1.0, 1.0, 1.0])
        search_radius = 1.1
        center_of_mass_radius = 11

        expected_peaks = np.array([[4, 4, 4.5]], dtype=float).T
        peaks, labels = detect_peaks(d, voxel_spacing, search_radius, center_of_mass_radius)
        assert_allclose(expected_peaks, peaks, atol=0.001)
