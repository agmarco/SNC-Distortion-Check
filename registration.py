import logging

import numpy as np
from math import pi, sqrt
import scipy.optimize

import affine


logger = logging.getLogger(__name__)


def build_f(A, B, g, rho):
    '''
    Create an objective function for our point cloud registration.

    Do as much of the calculations up front as is possible.
    '''
    mm, num_A = A.shape
    assert mm == 3
    assert A.dtype == float

    nn, num_B = B.shape
    assert nn == 3
    assert B.dtype == float

    A1 = np.vstack((A, np.ones((1, num_A), dtype=float)))

    g_ufunc = np.frompyfunc(g, 1, 1)
    rho_ufunc = np.frompyfunc(rho, 1, 1)

    B_norms = np.linalg.norm(B, axis=0)
    B_g_values = g_ufunc(B_norms)
    B_rho_values = rho_ufunc(B_norms)

    # Find the indices of the original B array that have non-zero g values
    # (there is no reason to consider values that are 0). Also sort these
    # indices from high g-values to low g-values.  The sorting ensures that,
    # when deciding between two points in B that are equidistant to a point in
    # A, we choose the point with the higher g-value.  The argmin function used
    # inside `f` picks the first value it finds in the case where there are
    # multiple minimums
    indices = range(num_B)
    sorted_B_g_values_w_indices = sorted(zip(B_g_values, indices), reverse=True)
    indices_sorted = [i for (g_value, i) in sorted_B_g_values_w_indices if g_value > 0]

    B_consideration_order = B[:, indices_sorted]
    g_consideration_order = B_g_values[indices_sorted]
    rho_consideration_order = B_rho_values[indices_sorted]

    _, num_B_considered = B_consideration_order.shape
    if num_B_considered == 0:
        print("Warning: no non-zero values in `B`!")
        return lambda xyztpx: 0

    def f(xyztpx):
        affine_matrix = affine.translation_rotation(*xyztpx)
        A1_S = affine_matrix @ A1
        A_S = A1_S[:3, :]

        summation = 0.0
        for a_s in A_S.T:
            b_to_a_s_distances_squared = np.sum((B_consideration_order - a_s.reshape((3, 1)))**2, axis=0)
            closest_b_indice = np.argmin(b_to_a_s_distances_squared) 
            b_min_to_a_s = sqrt(b_to_a_s_distances_squared[closest_b_indice])

            rho_b = rho_consideration_order[closest_b_indice]
            if b_min_to_a_s > rho_b:
                continue

            g_b = g_consideration_order[closest_b_indice]

            summation += g_b*(b_min_to_a_s/rho_b - 1)
        return summation
    return f


def register(A, B, g, rho, tol=1e-4):
    logger.info('Beginning Registration')
    f = build_f(A, B, g, rho)
    logger.info('Built f')

    brute_force_ranges = [
        slice(-4, 4, 2),
        slice(-4, 4, 2),
        slice(-4, 4, 2),
        slice(-0.08, 0.08, 0.04),
        slice(-0.08, 0.08, 0.04),
        slice(-0.08, 0.08, 0.04),
    ]
    x0 = scipy.optimize.brute(f, brute_force_ranges)
    logger.info('Brute force stage complete')

    options = {
        'xtol': tol,
        'ftol': 1e-20,
        'maxiter': 4000,
    }

    result = scipy.optimize.minimize(f, x0, method='Powell', options=options)

    logger.info('Optimization completed in {} iterations'.format(result.nit))
    logger.info('Objective function evaluated {} times'.format(result.nfev))
    logger.info('Cause of termination: {}'.format(result.message))
    if not result.success:
        raise ValueError('Optimization did not succeed')

    return result.x
