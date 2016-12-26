import logging

import numpy as np
from math import pi, sqrt
import scipy.optimize
from scipy.spatial import KDTree

import affine
import points_utils


logger = logging.getLogger(__name__)
import sys; logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


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
    g_div_rho_consideration_order = g_consideration_order/rho_consideration_order

    max_rho = np.max(rho_consideration_order)

    kdtree = KDTree(B_consideration_order.T)

    _, num_B_considered = B_consideration_order.shape
    if num_B_considered == 0:
        print("Warning: no non-zero values in `B`!")
        return lambda xyztpx: 0

    def f(xyztpx):
        affine_matrix = affine.translation_rotation(*xyztpx)
        A1_S = affine_matrix @ A1
        A_S = A1_S[:3, :]

        a_s_to_b_distances, closest_b_indices = kdtree.query(A_S.T, distance_upper_bound=max_rho)

        # points above the distance upper bound have an infinite distance, prune them out
        finite_indices = np.isfinite(a_s_to_b_distances)
        closest_b_indices = closest_b_indices[finite_indices]
        a_s_to_b_distances = a_s_to_b_distances[finite_indices]

        # prune out points that are below the distance upper bound (rho_max) and rho_b
        valid_indices = a_s_to_b_distances < rho_consideration_order[closest_b_indices]

        closest_b_indices = closest_b_indices[valid_indices]
        a_s_to_b_distances = a_s_to_b_distances[valid_indices]

        if len(np.unique(closest_b_indices)) < len(closest_b_indices):
            raise NotImplementedError("Not all points are unique")

        g_div_rho = g_div_rho_consideration_order[closest_b_indices]
        rho = rho_consideration_order[closest_b_indices]
        return np.sum(g_div_rho*(a_s_to_b_distances - rho))
    return f


def rigidly_register(A, B, g, rho, tol=1e-4):
    logger.info('Beginning rigid registration')
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


def rigidly_register_and_categorize(A, B):
    # TODO: determine rho and g based on our knowledge of the phantom
    # for now, we assume that the distortion is always within 5 mm
    g = lambda bmag: 1.0
    rho = lambda bmag: 5.0

    xyztpx = rigidly_register(A, B, rho, g, 1e-6)

    a_to_b_registration_matrix = affine.translation_rotation(*xyztpx)
    A_S = affine.apply_affine(a_to_b_registration_matrix, A)

    FN_A_S, TP_A_S, TP_B, FP_B = points_utils.categorize(A_S, B, rho)
    return xyztpx, FN_A_S, TP_A_S, TP_B, FP_B
