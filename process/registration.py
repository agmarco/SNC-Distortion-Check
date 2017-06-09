import logging
from math import sqrt
from math import pi

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
            b_to_a_s = B_consideration_order - a_s.reshape((3, 1))
            b_to_a_s_distances_squared = np.sum(b_to_a_s**2, axis=0)
            closest_b_indice = np.argmin(b_to_a_s_distances_squared)

            # by taking the root (1/1.8) of the squared distance, we are
            # effectively optimizing over the distance^(1.2); this means we are
            # ignoring outlers somewhat---but not completely like the L1 norm does
            b_min_to_a_s = (b_to_a_s_distances_squared[closest_b_indice])**(1.2/2.0)

            rho_b = rho_consideration_order[closest_b_indice]
            if b_min_to_a_s > rho_b:
                continue

            g_b = g_consideration_order[closest_b_indice]

            summation += g_b*(b_min_to_a_s/rho_b - 1)
        return summation
    return f


def rigidly_register(A, B, g, rho, tol=1e-4, skip_brute=False):
    logger.info('Beginning rigid registration')
    f = build_f(A, B, g, rho)
    logger.info('Built f')

    if skip_brute:
        x0 = np.array([0, 0, 0, 0, 0, 0])
        logger.info('Skipping brute force search')
    else:
        logger.info('Begining brute force search')

        # TODO: remove this
        center_of_mass_shift = np.mean(B, axis=1) - np.mean(A, axis=1)
        assert center_of_mass_shift.shape[0] == 3

        search_degrees = pi/180*5
        brute_force_ranges = [
            (-4 + center_of_mass_shift[0], 4 + center_of_mass_shift[0]),
            (-4 + center_of_mass_shift[1], 4 + center_of_mass_shift[1]),
            (-4 + center_of_mass_shift[2], 4 + center_of_mass_shift[2]),
            (-search_degrees, search_degrees),
            (-search_degrees, search_degrees),
            (-search_degrees, search_degrees),
        ]
        x0 = scipy.optimize.brute(f, brute_force_ranges, Ns=3)
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


# points further than `g_cutoff` are not considered during registration
g_cutoff = 50
registeration_tolerance = 1e-6


def g(bmag):
    return 1 - bmag/g_cutoff if bmag < g_cutoff else 0


def rho(bmag):
    return 5.0


def rigidly_register_and_categorize(A, B, isocenter_in_B, skip_brute=False):
    # shift B's coordinate system so that its origin is centered at the
    # isocenter; the lower level registration functions assume B's origin is
    # the isocenter
    b_to_b_i_registration_matrix = affine.T(*(-1*isocenter_in_B))
    B_i = affine.apply_affine(b_to_b_i_registration_matrix, B)

    xyztpx_i = rigidly_register(A, B_i, g, rho, registeration_tolerance, skip_brute=skip_brute)

    # now apply both shifts (from A -> B_i and then from B_i -> B) back onto A.
    # This preservers the original patient coordinate system
    a_to_b_i_registration_matrix = affine.translation_rotation(*xyztpx_i)
    b_i_to_b_registration_matrix = affine.T(*isocenter_in_B)
    a_to_b_registration_matrix =  b_i_to_b_registration_matrix @ a_to_b_i_registration_matrix
    A_S = affine.apply_affine(a_to_b_registration_matrix, A)

    xyztpx = affine.xyztpx_from_rotation_translation(a_to_b_registration_matrix)

    FN_A_S, TP_A_S, TP_B, FP_B = points_utils.categorize(A_S, B, rho)

    return xyztpx, FN_A_S, TP_A_S, TP_B, FP_B
