from math import pi

from numpy.testing import assert_allclose
import numpy as np

from affine import translation_rotation as S, apply_xyztpx


class TestAffineMatrix:
    def test_shifts(self):
        assert_allclose(S(1, 0, 0, 0, 0, 0) @ [0, 0, 0, 1], [1, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 1, 0, 0, 0, 0) @ [0, 0, 0, 1], [0, 1, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 1, 0, 0, 0) @ [0, 0, 0, 1], [0, 0, 1, 1], atol=1e-10)

    def test_rotate_x_90(self):
        assert_allclose(S(0, 0, 0, pi/2, 0, 0) @ [0, 0, 0, 1], [0, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, pi/2, 0, 0) @ [1, 0, 0, 1], [1, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, pi/2, 0, 0) @ [0, 1, 0, 1], [0, 0, 1, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, pi/2, 0, 0) @ [0, 0, 1, 1], [0, -1, 0, 1], atol=1e-10)

    def test_rotate_x_180(self):
        assert_allclose(S(0, 0, 0, pi, 0, 0) @ [0, 0, 0, 1], [0, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, pi, 0, 0) @ [1, 0, 0, 1], [1, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, pi, 0, 0) @ [0, 1, 0, 1], [0, -1, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, pi, 0, 0) @ [0, 0, 1, 1], [0, 0, -1, 1], atol=1e-10)

    def test_rotate_y_90(self):
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 0, 0, 1], [0, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [1, 0, 0, 1], [0, 0, -1, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 1, 0, 1], [0, 1, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 0, 1, 1], [1, 0, 0, 1], atol=1e-10)

    def test_rotate_z_90(self):
        assert_allclose(S(0, 0, 0, 0, 0, pi/2) @ [0, 0, 0, 1], [0, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, 0, pi/2) @ [1, 0, 0, 1], [0, 1, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, 0, pi/2) @ [0, 1, 0, 1], [-1, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, 0, pi/2) @ [0, 0, 1, 1], [0, 0, 1, 1], atol=1e-10)


class TestApplyXYZTPX:
    def test_translation(self):
        points = np.array([[0, 0, 0], [1, 1, 1]], dtype=float).T
        expected_transformed = np.array([[1, -2, 3], [2, -1, 4]], dtype=float).T
        assert_allclose(apply_xyztpx([1, -2, 3, 0, 0, 0], points), expected_transformed)
