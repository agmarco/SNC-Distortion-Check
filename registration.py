import numpy as np
from math import cos, sin, sqrt


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


def S(x, y, z, theta, phi, xi):
    return R_x(theta) @ R_y(phi) @ R_z(xi) @ T(x, y, z)


def build_f(A, B, g, rho):
    mm, m = A.shape
    assert mm == 3
    assert A.dtype == float

    nn, n = B.shape
    assert nn == 3
    assert B.dtype == float

    A1 = np.vstack((A, np.ones((1, m), dtype=float)))
    BT = B.T

    def f(inputs):
        x, y, z, theta, phi, xi = inputs
        S = R_x(theta) @ R_y(phi) @ R_z(xi) @ T(x, y, z)
        A1_S = S @ A1
        A_S = A1_S[:3, :]

        summation = 0.0
        for b in BT:
            b_norm = np.linalg.norm(b)
            g_b = g(b_norm)
            if g_b == 0:
                continue
            b_a_distances_squared = np.sum((A_S - b.reshape((3, 1)))**2, axis=0)
            min_b_a = sqrt(np.amin(b_a_distances_squared))
            rho_b = rho(b_norm)
            if min_b_a > rho_b:
                continue
            summation += g_b*(min_b_a/rho_b - 1)
        return summation
    return f


def apply_affine(affine_matrix, A):
    mm, m = A.shape
    assert mm == 3
    assert A.dtype == float

    A1 = np.vstack((A, np.ones((1, m), dtype=float)))
    A1_S = affine_matrix @ A1
    A_S = A1_S[:3, :]
    return A_S
