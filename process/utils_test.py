import numpy as np
import pytest

from process.utils import decimate


class TestDecimate:
    def test_simple_three_dimensions(self):
        a = np.zeros((10, 20, 10))
        a[:5, :16, :5] = 1
        a_decimated = decimate(a, 5)
        assert np.allclose(a_decimated, np.array([
            [[1, 0], [1, 0], [1, 0], [0.2, 0]],
            [[0, 0], [0, 0], [0, 0], [0, 0]],
        ]))

    def test_size_mismatch(self):
        a = np.zeros((10, 20))
        with pytest.raises(AssertionError):
            decimate(a, 6)
