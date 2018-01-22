import logging
from math import sqrt, radians
from itertools import product

import numpy as np
import scipy.optimize

from process import points_utils
from process import affine
from process.utils import format_optimization_result, format_xyztpx, format_xyz
from process.exceptions import AlgorithmException


logger = logging.getLogger(__name__)


angle_cutoff = radians(15)

registeration_tolerance = 1e-4


def rigidly_register_and_categorize(A, B, grid_spacing, isocenter_in_B):
    '''
    This is the central function in the registration phase of our algorithm.

    A and B are both sets of points in 3D space, which we would like to
    register together.

    Set A contains a set of gold-standard points (which may come from a CAD model
    of the phantom, or may be measured from a CT).  The center of the phantom
    is assumed to be at the origin (0, 0, 0).

    Set B contains points that were measured from a phantom.  There may be
    False Negatives (points that are in A, that should be in B).  There may be
    False Positives (points that are in B, that do not exist in A).  The set of
    points A may be translated by large amounts (e.g. 60 mm), but not so much
    such that A and B don't overlap.  It also may be rotated from its correct
    orientation by up +/- 4 degrees along all three axes.

    The isocenter of the imager is located, within B's coordinate system, at
    `isocenter_in_B`.  This is important to know, because the points in B may
    also be distorted from their original locations.  The magnitude of this
    distortion is smallest near the isocenter, thus, when we perform the
    registration, we want to weight the points near the isocenter the most.

    We also use the `isocenter_in_B` as our initial "guess" when performing the
    registration.

    After registering the sets of points, this function also matches and
    categorizes pairs of points from A and B together; in one sense, this
    categorization step should be done separately, but because it also relies
    on `rho`, it seemed prudent to keep it in the registration module.
    '''
    # shift B's coordinate system so that its origin is centered at the
    # isocenter; the lower level registration functions assume B's origin is
    # the isocenter
    b_to_b_i_registration_matrix = affine.translation(*(-1*isocenter_in_B))
    B_i = affine.apply_affine(b_to_b_i_registration_matrix, B)
    logger.info(f'shifting golden points to isocenter: {format_xyz(*isocenter_in_B)}')

    xyztpx_a_to_b_i = rigidly_register(A, B_i, grid_spacing)

    # now apply both shifts (from A -> B_i and then from B_i -> B) back onto A.
    # This preservers the original patient coordinate system
    a_to_b_i_registration_matrix = affine.rotation_translation(*xyztpx_a_to_b_i)
    b_i_to_b_registration_matrix = affine.translation(*isocenter_in_B)
    a_to_b_registration_matrix = b_i_to_b_registration_matrix @ a_to_b_i_registration_matrix
    A_S = affine.apply_affine(a_to_b_registration_matrix, A)

    # note that adding these vectors works because we apply the rotations
    # first, before the translations, and the second vector ONLY has
    # translations
    xyztpx_a_to_b = xyztpx_a_to_b_i + np.array([*isocenter_in_B, 0, 0, 0])

    # TODO: think of how to avoid duplication between here and within `rigidly_register`
    rho = build_rho(calculate_g_cutoff(3, grid_spacing), grid_spacing)

    FN_A_S, TP_A_S, TP_B, FP_B = points_utils.categorize(A_S, B, rho)

    return xyztpx_a_to_b, FN_A_S, TP_A_S, TP_B, FP_B


def rigidly_register(A, B_i, grid_spacing, xtol=registeration_tolerance):
    '''
    Rigidly register two sets of points, where B has its isocenter located at its origin.

    1. Perform convex optimization on an objective function which will line up
       the grids of A and B_i.  If the original sets of points were optimized
       well, then registration may be done after this step, but if the initial
       datasets were offset by more than a grid intersection, we will likely
       have found a "local minimum" which has aligned the grids, but perhaps
       has the grids offset by one or more grid lengths.
    2. Perform a "grid search", wherein we search for grid shifts that maximize
       the number of matching points.  This should let us jump out of the
       valley that step 1 found, and into the valley that contains the correct grid alignment.
    3. Run another convex optimization like in step 1, so that we
       can fine tune the result from step 2.
    '''
    logger.info('beginning rigid registration')

    # We want to encompass at least the middle 125 points in a sphere (we will of course
    # get some extra points too in the corners)
    num_grid_spacings = 2
    g_cutoff = calculate_g_cutoff(num_grid_spacings, grid_spacing)
    g_near_isocenter = lambda bmag: 1 if bmag < g_cutoff else 0
    rho_initial = build_rho(0, grid_spacing)
    f_points_near_isocenter_initial = build_objective_function(A, B_i, g_near_isocenter, rho_initial)

    # During the grid search, we want to consider ALL points, regardless of how
    # far they are from the isocenter, since we want to ensure that A and B are
    # overlapping; thus, our g function is 1.0 everywhere; we can't use this in
    # earlier steps for performance reasons, and because we want to weight
    # points near the isocenter more during the fine-tuning optimization
    g_all = lambda bmag: 1.0
    rho = build_rho(g_cutoff, grid_spacing)
    f_all_points = build_objective_function(A, B_i, g_all, rho)
    f_points_near_isocenter = build_objective_function(A, B_i, g_near_isocenter, rho)

    xyztpx_initial = np.array([0, 0, 0, 0, 0, 0])
    xyztpx_initial_local_minimum = _run_optimizer(f_points_near_isocenter_initial, xyztpx_initial, xtol)
    xyztpx_global_minimum_rough = grid_search(f_all_points, grid_spacing, xyztpx_initial_local_minimum)
    xyztpx_global_minimum = _run_optimizer(f_points_near_isocenter, xyztpx_global_minimum_rough, xtol)
    logger.info('finished rigid registration')
    return xyztpx_global_minimum


def calculate_g_cutoff(num_grid_spacings, grid_spacing):
    '''
    Determine a cutoff distance that will encompass a cubic grid up to
    `num_grid_spacings` away from the center.
    '''
    g_cutoff_buffer = 3
    return grid_spacing*num_grid_spacings*sqrt(3) + g_cutoff_buffer


def build_rho(g_cutoff, grid_spacing):
    '''
    The rho function determines how close two points need to be to be
    considered a "match", as a function of distance from the isocenter, "bmag".
    Points further from the isocenter are expected to have more distortion, and
    thus may be further apart while still being considered "matched".
    '''
    min_match_distance = 3
    max_match_distance = grid_spacing * 0.45

    def rho(bmag):
        if bmag < g_cutoff:
            return min_match_distance + min_match_distance*bmag/g_cutoff
        else:
            return max_match_distance

    return rho


def build_objective_function(A, B, g, rho):
    '''
    Create an objective function that we will optimize during our point cloud
    registration.

    The g function specifies the relative importance of points near the
    isocenter vs points away from the isocenter.

    The rho function determines how close two points need to be to be
    considered a "match", as a function of distance from the isocenter, "bmag".
    Points further from the isocenter are expected to have more distortion, and
    thus may be further apart while still being considered "matched".

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
        _, _, _, theta, phi, xi = xyztpx
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
        return summation/((1 + (theta/angle_cutoff)**4)*(1 + (phi/angle_cutoff)**4)*(1 + (xi/angle_cutoff)**4))
    return f


def _run_optimizer(f, xyztpx, xtol):
    max_iterations = 4000
    ftol = 1e-10
    options = {
        'xtol': xtol,
        'ftol': ftol,
        'maxiter': max_iterations,
    }
    result = scipy.optimize.minimize(f, xyztpx, method='Powell', options=options)
    logger.info(format_optimization_result(result))
    logger.info(format_xyztpx(result.x))

    if result.success:
        return result.x
    else:
        raise AlgorithmException(
            f'The detected grid intersections could not be registered to the '
            f'golden grid intersection locations within {max_iterations} optimization '
            f'iterations.  Aborting processing.'
        )


def grid_search(f, grid_spacing, initial_xyztpx, max_iterations=100):
    logger.info("beginning grid search")
    origin_26 = np.array([[x, y, z] for x, y, z
        in product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1])
        if x != 0 or y != 0 or z != 0], dtype=np.double).T*grid_spacing

    current_xyztpx = initial_xyztpx
    current_f = f(current_xyztpx)

    iteration = 0
    while iteration < max_iterations:
        surrounding_26 = affine.apply_xyztpx(current_xyztpx, origin_26)
        surrounding_f = [f(np.hstack((p, current_xyztpx[3:]))) for p in surrounding_26.T]
        if all(current_f <= f for f in surrounding_f):
            logger.info(f"finished grid search at {format_xyz(*current_xyztpx[:3])} with {current_f}")
            return current_xyztpx
        index_of_min, current_f = min(enumerate(surrounding_f), key=lambda p: p[1])
        current_xyztpx = np.hstack((surrounding_26[:, index_of_min], current_xyztpx[3:]))
        logger.info(f"{iteration}: jumping to grid location at {format_xyz(*current_xyztpx[:3])} with {current_f}")
        iteration += 1

    raise AlgorithmException(f'Unable to find a grid minimum after {max_iterations}')
