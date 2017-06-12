import logging
from math import sqrt
from math import pi

import numpy as np
import scipy.optimize

from process import points_utils
from process import affine
from process.utils import format_optimization_result, format_xyztpx, format_xyz
from process.exceptions import AlgorithmException

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
        logger.warning("no non-zero values in B")
        return lambda xyztpx: 0

    def f(xyztpx):
        affine_matrix = affine.rotation_translation(*xyztpx)
        A1_S = affine_matrix @ A1
        A_S = A1_S[:3, :]

        summation = 0.0
        for a_s in A_S.T:
            b_to_a_s = B_consideration_order - a_s.reshape((3, 1))
            b_to_a_s_distances_squared = np.sum(b_to_a_s**2, axis=0)
            closest_b_indice = np.argmin(b_to_a_s_distances_squared)

            b_min_to_a_s = (b_to_a_s_distances_squared[closest_b_indice])**(1.0/2.0)

            rho_b = rho_consideration_order[closest_b_indice]
            if b_min_to_a_s > rho_b:
                continue

            g_b = g_consideration_order[closest_b_indice]

            summation += g_b*(b_min_to_a_s/rho_b - 1)
        return summation
    return f


def rigidly_register(A, B, g, rho, xtol=1e-4, brute_search_slices=None):
    '''
    Assumes that the isocenter is locate at the origin of B.
    '''
    logger.info('beginning rigid registration')
    f = build_f(A, B, g, rho)

    if not brute_search_slices:
        xyztpx_0 = np.array([0, 0, 0, 0, 0, 0])
    else:
        # reproduce grid used in `optimize.brute`, so we know its size
        brute_search_shape = np.mgrid[brute_search_slices].shape[1:]

        logger.info('beginning brute force search of %s points around the isocenter', brute_search_shape)
        xyztpx_0 = scipy.optimize.brute(f, brute_search_slices, finish=None, full_output=False)
        logger.info('finishing brute force search, found %s', format_xyztpx(xyztpx_0))

    max_iterations = 4000
    ftol = 1e-10
    options = {
        'xtol': xtol,
        'ftol': ftol,
        'maxiter': max_iterations,
    }
    result = scipy.optimize.minimize(f, xyztpx_0, method='Powell', options=options)
    logger.info(format_optimization_result(result))
    logger.info(format_xyztpx(result.x))

    if not result.success:
        raise AlgorithmException(
            f'The detected grid intersections could not be registered to the '
            f'golden grid intersection locations within {max_iterations} optimization '
            f'iterations.  Aborting processing.'
        )

    logger.info('finished rigid registration')
    return result.x


# points further than `g_cutoff` are not considered during registration
g_cutoff = 50
registeration_tolerance = 1e-4


def g(bmag):
    '''
    The g function specifies the relative importance of points near the
    isocenter vs points away from the isocenter.

    It should never drop to 0, since if it does, the optimizer may shift the
    match over by an integer grid_spacing.
    '''
    return 1 - bmag/g_cutoff if bmag < 0.8*g_cutoff else 0.2


def rho(bmag):
    '''
    The rho function determines how close two points need to be to be
    considered a "match", as a function of distance from the isocenter, "bmag".
    Points further from the isocenter are expected to have more distortion, and
    thus may be further apart while still being considered "matched".
    '''
    return 3.0 + 3.0*bmag/g_cutoff if bmag < g_cutoff else 6.0


def rigidly_register_and_categorize(A, B, isocenter_in_B, brute_search_slices=None):
    # shift B's coordinate system so that its origin is centered at the
    # isocenter; the lower level registration functions assume B's origin is
    # the isocenter
    b_to_b_i_registration_matrix = affine.translation(*(-1*isocenter_in_B))
    B_i = affine.apply_affine(b_to_b_i_registration_matrix, B)
    logger.info(f'shifting golden points to isocenter: {format_xyz(*isocenter_in_B)}')

    xyztpx_a_to_b_i = rigidly_register(A, B_i, g, rho, registeration_tolerance, brute_search_slices)

    # now apply both shifts (from A -> B_i and then from B_i -> B) back onto A.
    # This preservers the original patient coordinate system
    a_to_b_i_registration_matrix = affine.rotation_translation(*xyztpx_a_to_b_i)
    b_i_to_b_registration_matrix = affine.translation(*isocenter_in_B)
    a_to_b_registration_matrix =  b_i_to_b_registration_matrix @ a_to_b_i_registration_matrix
    A_S = affine.apply_affine(a_to_b_registration_matrix, A)

    # note that adding these vectors works because we apply the rotations
    # first, before the translations, and the second vector ONLY has
    # translations
    xyztpx_a_to_b = xyztpx_a_to_b_i + np.array([*isocenter_in_B, 0, 0, 0])

    FN_A_S, TP_A_S, TP_B, FP_B = points_utils.categorize(A_S, B, rho)

    return xyztpx_a_to_b, FN_A_S, TP_A_S, TP_B, FP_B
