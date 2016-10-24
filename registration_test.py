from math import pi

import pytest
import numpy as np
from numpy.testing import assert_allclose
import scipy.optimize

from registration import build_f, S, apply_affine


@pytest.fixture
def simple_f():
    B = np.array([[0, 0, 1]], dtype=float).T
    A = np.array([[0, 0, 1], [0, 0, 2]], dtype=float).T
    g = lambda bmag: 1.0 if bmag <= 10 else 0.0
    rho = lambda bmag: 1.0
    return build_f(A, B, g, rho)


class TestSimpleF:
    def test_overlapping_points(self, simple_f):
        '''
        The first point in a overlaps with b.
        With a shift of [0, 0, -1] the second point will overlap.
        '''
        assert simple_f([0, 0, 0, 0, 0, 0]) == -1.0
        assert simple_f([0, 0, -1, 0, 0, 0]) == -1.0

    def test_grabs_closest_point_at_rho(self, simple_f):
        '''
        A shift in the +z direction will move the second point further away,
        and the first point right on the edge of rho.
        '''
        assert simple_f([0, 0, 1, 0, 0, 0]) == 0

    def test_grabs_closest_point_at_half_rho(self, simple_f):
        '''
        Moving the first point by 0.5 in any direction should result in a
        value that is "halfway out" of the cone.
        '''
        assert simple_f([0, 0, -0.5, 0, 0, 0]) == -0.5
        assert simple_f([0, 0,  0.5, 0, 0, 0]) == -0.5
        assert simple_f([0, 0.5, 0, 0, 0, 0]) == -0.5
        assert simple_f([ 0.5, 0, 0, 0, 0, 0]) == -0.5
        assert simple_f([-0.5, 0, 0, 0, 0, 0]) == -0.5


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

    def _test_rotate_y(self):
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 0, 0, 1], [0, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [1, 0, 0, 1], [1, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 1, 0, 1], [0, 0, -1, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 0, 1, 1], [0, -1, 0, 1], atol=1e-10)



def test_basic_registration():
    A = []
    for x in range(-10, 10):
        for y in range(-10, 10):
            for z in range(-10, 10):
                A.append((x, y, z))

    A = np.array(A, dtype=float).T
    print(A.shape)

    x = 0.2
    y = 0.1
    z = -0.4

    B = apply_affine(S(x, y, z, 0, 0, 0), A)

    g = lambda bmag: 1.0 if bmag <= 10 else 0.0
    rho = lambda bmag: 1.0

    f = build_f(A, B, g, rho)

    r0 = np.array([0, 0, 0, 0, 0, 0])
    result = scipy.optimize.minimize(f, r0)

    assert_allclose(result.x, [x, y, z, 0, 0, 0])
