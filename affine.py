from math import cos, sin, pi

import numpy as np


def R_x(theta):
    return np.array([
        [1, 0,          0,           0],
        [0, cos(theta), -sin(theta), 0],
        [0, sin(theta), cos(theta), 0],
        [0, 0,          0,           1]
    ])


def R_y(phi):
    return np.array([
        [cos(phi),  0, sin(phi), 0],
        [0,         1,        0, 0],
        [-sin(phi), 0, cos(phi), 0],
        [0,         0,        0, 1]
    ], dtype='f')


def R_z(xi):
    return np.array([
        [cos(xi),  sin(xi), 0, 0],
        [-sin(xi), cos(xi), 0, 0],
        [0,        0,       1, 0],
        [0,        0,       0, 1]
    ], dtype='f')


def T(x, y, z):
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1]
    ], dtype='f')


def translation_rotation(x, y, z, theta, phi, xi):
    return R_x(theta) @ R_y(phi) @ R_z(xi) @ T(x, y, z)


def apply_affine(affine_matrix, A):
    mm, m = A.shape
    assert mm == 3
    assert A.dtype == float

    A1 = np.vstack((A, np.ones((1, m), dtype=float)))
    A1_transformed = affine_matrix @ A1
    A_transformed = A1_transformed[:3, :]
    return A_transformed
