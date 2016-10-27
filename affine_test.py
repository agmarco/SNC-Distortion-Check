from math import pi

from numpy.testing import assert_allclose

from affine import translation_rotation as S


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

    def _test_rotate_y_90(self):
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 0, 0, 1], [0, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [1, 0, 0, 1], [1, 0, 0, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 1, 0, 1], [0, 0, -1, 1], atol=1e-10)
        assert_allclose(S(0, 0, 0, 0, pi/2, 0) @ [0, 0, 1, 1], [0, -1, 0, 1], atol=1e-10)
