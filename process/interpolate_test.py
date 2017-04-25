import numpy as np

from process import interpolate


class TestInterpolateDistortion:
    def test_rectangle_no_distortion(self):
        '''
        Points on the edge of the convex hull defined by TP_B should not be
        NaN, hence ALL of the points in the grid should not be NaNs.
        '''
        side = np.array([0.0, 1.0])
        X, Y, Z = np.meshgrid(side, side, side, indexing='ij')
        TP_A_S = np.vstack((X.ravel(), Y.ravel(), Z.ravel()))
        assert TP_A_S.shape == (3, 8)
        TP_B = TP_A_S.copy()

        ijk_to_xyz = np.array([
            [1/3, 0, 0, 0],
            [0, 1/3, 0, 0],
            [0, 0, 1/3, 0],
            [0, 0, 0, 1],
        ])
        ijk_shape = (4, 4, 4)
        distortion = interpolate.interpolate_distortion(TP_A_S, TP_B, ijk_to_xyz, ijk_shape)

        distortion_magnitude = np.linalg.norm(distortion, axis=3)
        num_nan = np.sum(np.isnan(distortion_magnitude))
        num_zero = np.sum(distortion_magnitude == 0)
        assert num_nan == 0
        assert num_zero == 4*4*4

    def test_smaller_rectangle_no_distortion(self):
        '''
        Slightly shriink the locations of TP_A_S and TP_B such that the outer
        most set of points in the 4x4x4 grid are now outside the convex hull.
        '''
        delta = 0.00001
        side = np.array([0 + delta, 1.0 - delta])
        X, Y, Z = np.meshgrid(side, side, side, indexing='ij')
        TP_A_S = np.vstack((X.ravel(), Y.ravel(), Z.ravel()))
        assert TP_A_S.shape == (3, 8)
        TP_B = TP_A_S.copy()

        ijk_to_xyz = np.array([
            [1/3, 0, 0, 0],
            [0, 1/3, 0, 0],
            [0, 0, 1/3, 0],
            [0, 0, 0, 1],
        ])
        ijk_shape = (4, 4, 4)
        distortion = interpolate.interpolate_distortion(TP_A_S, TP_B, ijk_to_xyz, ijk_shape)

        distortion_magnitude = np.linalg.norm(distortion, axis=3)
        num_nan = np.sum(np.isnan(distortion_magnitude))
        num_zero = np.sum(distortion_magnitude == 0)
        assert num_nan == 4*4*4 - 2*2*2
        assert num_zero == 2*2*2

    def test_rectangle_slight_distortion(self):
        '''
        Introduce error_mags into one corner of the grid.
        '''
        side = np.array([0.0, 1.0])
        X, Y, Z = np.meshgrid(side, side, side, indexing='ij')
        TP_A_S = np.vstack((X.ravel(), Y.ravel(), Z.ravel()))
        assert TP_A_S.shape == (3, 8)
        TP_B = TP_A_S.copy()
        TP_A_S[:, -1] = [1.0, 1.0, 2.0]

        ijk_to_xyz = np.array([
            [1/3, 0, 0, 0],
            [0, 1/3, 0, 0],
            [0, 0, 1/3, 0],
            [0, 0, 0, 1],
        ])
        ijk_shape = (4, 4, 4)
        distortion = interpolate.interpolate_distortion(TP_A_S, TP_B, ijk_to_xyz, ijk_shape)

        distortion_magnitude = np.linalg.norm(distortion, axis=3)
        num_nan = np.sum(np.isnan(distortion_magnitude))
        num_zero = np.sum(np.isclose(distortion_magnitude, 0, atol=1e-16))
        num_one_third = np.sum(np.isclose(distortion_magnitude, 1/3, atol=1e-16))
        num_two_third = np.sum(np.isclose(distortion_magnitude, 2/3, atol=1e-16))
        num_one = np.sum(distortion_magnitude == 1.0)
        assert num_nan == 0
        assert num_zero == 4*4*4 - (3*3 + 2*2 + 1*1)
        assert num_one_third == 3*3
        assert num_two_third == 2*2
        assert num_one == 1*1
