import logging

import numpy as np
from math import pi
import scipy.optimize

import affine


logger = logging.getLogger(__name__)


def build_f(A, B, g, rho):
    mm, m = A.shape
    assert mm == 3
    assert A.dtype == float

    nn, n = B.shape
    assert nn == 3
    assert B.dtype == float

    A1 = np.vstack((A, np.ones((1, m), dtype=float)))
    BT = B.T

    matches = {}  # b index -> a index

    def f(inputs):
        x, y, z, theta, phi, xi = inputs
        affine_matrix = affine.translation_rotation(x, y, z, theta, phi, xi)
        A1_S = affine_matrix @ A1
        A_S = A1_S[:3, :]

        summation = 0.0
        for i, b in enumerate(BT):
            b_norm = np.linalg.norm(b)
            g_b = g(b_norm)
            if g_b == 0:
                continue

            if i not in matches:
                b_a_distances_squared = np.sum((A_S - b.reshape((3, 1)))**2, axis=0)
                matches[i] = np.argmin(b_a_distances_squared)

            a = A_S[:, matches[i]]
            min_b_a = np.linalg.norm(a - b)
            rho_b = rho(b_norm)
            if min_b_a > rho_b:
                continue
            summation += g_b*(min_b_a/rho_b - 1)
        return summation
    return f


def register(A, B):
    '''
    Our "best known" optimization strategy.
    '''
    g = lambda bmag: 1.0 if bmag <= 10 else 0.0
    rho = lambda bmag: 1.0

    f = build_f(A, B, g, rho)

    r0 = np.array([0, 0, 0, 0, 0, 0])

    deg5 = pi*5/180
    bounds = [(-50, 50), (-50, 50), (-50, 50), (-deg5, deg5), (-deg5, deg5), (-deg5, deg5)]

    result = scipy.optimize.minimize(f, r0, method='TNC', bounds=bounds)
    _handle_optimization_result(result)
    return result.x


def _handle_optimization_result(result):
    logger.info('Optimization completed in {} iterations'.format(result.nit))
    logger.info('Objective function evaluated {} times'.format(result.nfev))
    logger.info('Cause of termination: {}'.format(result.message))
    if not result.success:
        raise ValueError('Optimization did not succeed')
