from math import cos, sin, pi, radians

import numpy as np


def rotation_x(theta):
    return np.array([
        [1, 0,          0,           0],
        [0, cos(theta), -sin(theta), 0],
        [0, sin(theta), cos(theta), 0],
        [0, 0,          0,           1]
    ])


def rotation_y(phi):
    return np.array([
        [cos(phi),  0, sin(phi), 0],
        [0,         1,        0, 0],
        [-sin(phi), 0, cos(phi), 0],
        [0,         0,        0, 1]
    ], dtype='f')


def rotation_z(xi):
    return np.array([
        [cos(xi), -sin(xi), 0, 0],
        [sin(xi), cos(xi), 0, 0],
        [0,        0,       1, 0],
        [0,        0,       0, 1]
    ], dtype='f')


def scaleing(x, y, z):
    return np.array([
        [x, 0, 0, 0],
        [0, y, 0, 0],
        [0, 0, z, 0],
        [0, 0, 0, 1]
    ], dtype='f')


def translation(x, y, z):
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1]
    ], dtype='f')


def rotation(theta, phi, xi):
    return rotation_x(theta) @ rotation_y(phi) @ rotation_z(xi)


def rotation_translation(x, y, z, theta, phi, xi):
    return translation(x, y, z) @ rotation(theta, phi, xi)


def apply_affine(affine_matrix, A):
    mm, m = A.shape
    assert mm == 3
    assert A.dtype == float

    A1 = np.vstack((A, np.ones((1, m), dtype=float)))
    A1_transformed = affine_matrix @ A1
    A_transformed = A1_transformed[:3, :]
    return A_transformed


def apply_affine_1(affine_matrix, A):
    (m,) = A.shape
    assert m == 3
    assert A.dtype == float

    A1 = np.array([[*A, 1]]).T
    A1_transformed = affine_matrix @ A1
    A_transformed = A1_transformed[:3, :].T.squeeze()
    return A_transformed


def apply_xyztpx(xyztpx, points):
    return apply_affine(rotation_translation(*xyztpx), points)


def voxel_spacing(ijk_to_xyz):
    test_ijk_points = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ], dtype=float).T
    test_xyz_points = apply_affine(ijk_to_xyz, test_ijk_points)
    dvec = test_xyz_points[:, 1:] - test_xyz_points[:, 0].reshape(3, 1)
    return np.abs(np.linalg.norm(dvec, axis=0))


def rotate_about(points, x, y, z, theta, phi, xi):
    affine = translation(x, y, z) @ \
             rotation_x(radians(theta)) @ \
             rotation_y(radians(phi)) @ \
             rotation_z(radians(xi)) @ \
             translation(-x, -y, -z)
    return apply_affine(affine, points)


def translate(points, x, y, z):
    affine = translation(x, y, z)
    return apply_affine(affine, points)
