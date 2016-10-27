import pytest
import numpy as np
from numpy.testing import assert_allclose

from registration import build_f, register
from affine import apply_affine, translation_rotation


@pytest.fixture
def simple_f():
    B = np.array([[0, 0, 1]], dtype=float).T
    A = np.array([[0, 0, 1], [0, 0, 2]], dtype=float).T
    g = lambda bmag: 1.0 if bmag <= 10 else 0.0
    rho = lambda bmag: 1.0
    return build_f(A, B, g, rho)


class TestSimpleF:
    def test_overlapping_points_no_shift(self, simple_f):
        '''
        The first point in a overlaps with b.
        '''
        assert simple_f([0, 0, 0, 0, 0, 0]) == -1.0

    def test_overlapping_points_with_shift(self, simple_f):
        '''
        With a shift of [0, 0, -1] the second point will overlap.
        '''
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


def test_basic_registration():
    A = []
    for x in range(-5, 5):
        for y in range(-5, 5):
            for z in range(-5, 5):
                A.append((x, y, z))

    A = np.array(A, dtype=float).T
    m, mm = A.shape
    assert m == 3

    x = 0.2
    y = 0.1
    z = -0.4

    B = apply_affine(translation_rotation(x, y, z, 0, 0, 0), A)

    g = lambda bmag: 1.0 if bmag <= 10 else 0.0
    rho = lambda bmag: 5.0

    tolerance = 1e-5
    resulting_params = register(A, B, g, rho, tolerance)

    assert_allclose(resulting_params, [x, y, z, 0, 0, 0], atol=tolerance*2)
