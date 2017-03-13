import logging
from math import sqrt

import numpy as np
import scipy.optimize

from process import points_utils
from process import affine
from process.utils import print_optimization_result

logger = logging.getLogger(__name__)
import sys; logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# TODO: handle this in a "ConsoleApp" class


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

    print_optimization_result(result)
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