import pytest
import numpy as np
from numpy.testing import assert_allclose

from peak_detection import neighborhood_peaks


class TestDetectPeaks:
    def test_bad_neighborhood_dtype(self):
        data = np.array([[0, 0]])
        neighborhood = np.array([[1.0]])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_mismatched_number_of_dimensions(self):
        data = np.array([[0, 0]])
        neighborhood = np.array([True])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_even_length(self):
        data = np.array([[0, 0]])
        neighborhood = np.array([[False, True]])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_large_neighborhood(self):
        data = np.array([[0, 0]])
        neighborhood = np.array([[True, True, True]])
        with pytest.raises(ValueError):
            neighborhood_peaks(data, neighborhood)

    def test_1px_neighborhood_1d(self):
        data = np.random.rand(3)
        neighborhood = np.array([True])
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, np.zeros_like(data))

    def test_1px_neighborhood_2d(self):
        data = np.random.rand(3, 3)
        neighborhood = np.array([[True]])
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, np.zeros_like(data))

    def test_1px_neighborhood_3d(self):
        data = np.random.rand(3, 3, 3)
        neighborhood = np.array([[[True]]])
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, np.zeros_like(data))

    def test_simple_2d_vertical_neighborhood(self):
        data = np.array([
            [0, 0.5, 0, 0],
            [0,   1, 0, 0],
            [0, 0.5, 0, 2],
        ])
        neighborhood = np.array([[True], [True], [True]])
        expected_peaks = np.array([
            [0,   0, 0, 0],
            [0, 0.5, 0, 0],
            [0,   0, 0, 2],
        ])
        peaks = neighborhood_peaks(data, neighborhood)
        assert_allclose(peaks, expected_peaks)

    def test_simple_2d_horizontal_neighborhood(self):
        data = np.array([
            [0, 0.5, 0, 0],
            [0,   1, 0, 0],
            [0, 0.5, 0, 2],
        ])
        expected_peaks = np.array([
            [0, 0.5, 0, 0],
            [0,   1, 0, 0],
            [0, 0.5, 0, 2],
        ])
        neighborhood = np.array([[True, True, True]])
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
