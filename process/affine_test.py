from math import pi

import pytest
from numpy.testing import assert_allclose
import numpy as np

from .affine import translation_rotation as S, apply_xyztpx, voxel_spacing, \
        xyztpx_from_rotation_translation, translation_rotation


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


class TestPixelSpacing:
    def test_simple(self):
        di, dj, dk = 1.0, 1.2, 5.0
        ijk_to_xyz = np.array([
            [di, 0, 0, 0],
            [0, dj, 0, 0],
            [0, 0, dk, 0],
            [0, 0, 0, 1],
        ]).T
        assert_allclose(voxel_spacing(ijk_to_xyz), np.array((di, dj, dk)))

    def test_with_translation(self):
        di, dj, dk = 1.0, 1.2, 5.0
        ijk_to_xyz = np.array([
            [di, 0, 0, 0],
            [0, dj, 0, 0],
            [0, 0, dk, 0],
            [0, 0, 0, 1],
        ]).T
        ijk_to_xyz = ijk_to_xyz @ S(23, 45, 566, 0, 0, 0)
        assert_allclose(voxel_spacing(ijk_to_xyz), np.array((di, dj, dk)))

@pytest.mark.skip(reason="Work in progress")
@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_extract_xyztpx(seed):
    np.random.seed(seed)
    x, y, z = np.random.uniform(-10, 10, (3,))
    #theta, phi, xi = np.random.uniform(-pi/2, pi/2, (3,))
    theta, phi, xi = 0, 0, 0
    affine_matrix = translation_rotation(x, y, z, theta, phi, xi)
    print(x, y, z)
    print(affine_matrix)
    xp, yp, zp, thetap, phip, xip = xyztpx_from_rotation_translation(affine_matrix)
    assert x == xp
    assert y == yp
    assert z == zp
    assert theta == thetap
    assert phi == phip
    assert xi == xip
