import numpy as np
from scipy.interpolate.ndgriddata import griddata

from process import affine


def interpolate_distortion(TP_A_S, TP_B, ijk_to_xyz, ijk_shape):
    distortion_points = TP_B - TP_A_S
    ni, nj, nk = ijk_shape

    xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
    TP_B_in_ijk = affine.apply_affine(xyz_to_ijk, TP_B)

    grid = tuple(np.meshgrid(np.arange(0, ni), np.arange(0, nj), np.arange(0, nk), indexing='ij'))

    distortion_grid = np.empty((ni, nj, nk, 3))
    for d in range(3):
        distortion_grid[:, :, :, d] = griddata(TP_B_in_ijk.T, distortion_points[d, :], grid, method='linear')

    assert distortion_grid.shape == (ni, nj, nk, 3)
    return distortion_grid
