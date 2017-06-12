import math

import numpy as np
from orderedset import OrderedSet
from scipy.spatial import KDTree


def closest(A, point):
    dims, num_points = A.shape
    assert dims == 3
    assert num_points >= 1

    distances_squared = np.sum((A - point.reshape((3, 1)))**2, axis=0)
    closest_indice = np.argmin(distances_squared)
    distance = math.sqrt(distances_squared[closest_indice])
    return closest_indice, A[:, closest_indice], distance


def categorize(A, B, rho):
    '''
    Given an array of locations of detected features, B, and an array of known
    feature locations that HAVE BEEN REGISTERED into B's coordinate system,
    A, separate the points into three groups:

    - false negatives (points in A that should have a matching point in B, but don't)
    - matching points (points in A that have matching points in B)
    - false positives (points in B that have no matching point in A)

    These results are returned as four arrays

    1. FN_A (3 x O)
    2. TP_A (3 x M)
    3. TP_B (3 x M)
    4. FP_B (3 x N)

    where A is (3 x M+O) and B is (3 x N+M).  Each column of TP_A is a point
    that matches the corresponding column in TP_B.

    Two points, a and b, are matching if

    - they are within rho(|b|) distance from one another
    - neither point has already been matched
    - matching them minimizes the total sum of distances of all matched points.

    The last condition means that, in general, each point in A will be matched
    to the closest point in B.  The only exception to this is if there is a
    point, b in B, that could match multiples points in A.  In this case, b
    will be matched with whichever point in A minimizes the total sum of
    distances.

    In the case that there is a point in B that is equidistant from two points
    in A (both of which can ONLY match this one point), then the matching will
    be arbitrary.
    '''
    _, num_a = A.shape
    assert _ == 3

    _, num_b = B.shape
    assert _ == 3

    if num_a == 0:
        FN_A = np.empty((3, 0))
        TP_A = np.empty((3, 0))
        TP_B = np.empty((3, 0))
        FP_B = B

    elif num_b == 0:
        FN_A = A
        TP_A = np.empty((3, 0))
        TP_B = np.empty((3, 0))
        FP_B = np.empty((3, 0))

    else:
        kdtree = KDTree(B.T)

        a_b_distances, closest_b_indices = kdtree.query(A.T)

        seen_b_indices = OrderedSet()
        seen_a_indices = OrderedSet()

        TP_A_indices = np.zeros(num_a, dtype=bool)
        TP_B_indices = np.zeros(num_b, dtype=bool)

        a_indices = range(num_a)
        for a_indice, b_indice, a_b_distance in zip(a_indices, closest_b_indices, a_b_distances):
            b = B[:, b_indice]
            b_mag = np.linalg.norm(b)
            if a_b_distance < rho(b_mag):
                TP_A_indices[a_indice] = True
                TP_B_indices[b_indice] = True

                if b_indice in seen_b_indices:
                    continue
                    #raise NotImplementedError("Multiple points in A match same point in B")
                    # TODO: when there are multiple matching points, pick the
                    # closest match; once this is done, the two assertions
                    # below should be enabled; also there are skipped tests for
                    # this that should be enabled
                else:
                    seen_b_indices.add(b_indice)
                    seen_a_indices.add(a_indice)

        FN_A = A[:, ~TP_A_indices]
        TP_A = A[:, seen_a_indices]
        TP_B = B[:, seen_b_indices]
        FP_B = B[:, ~TP_B_indices]

    #assert FN_A.shape[1] + TP_A.shape[1] == num_a
    #assert FP_B.shape[1] + TP_B.shape[1] == num_b

    return FN_A, TP_A, TP_B, FP_B


def _valid_location(location, data_shape, kernel_shape):
    '''
    Is the location such that the kernel, when centered there, will fully fit
    inside the data?
    '''
    assert len(location) == len(data_shape) == len(kernel_shape)
    return all(d - (k - 1)/2 > l >= (k - 1)/2 for l, d, k in zip(location, data_shape, kernel_shape))


def metrics(FN_A, TP_A, TP_B, FP_B):
    '''
    Our standard metrics for comparing sets of points.
    '''
    num_points_a = len(FN_A.T) + len(TP_A.T)
    num_points_b = len(FP_B.T) + len(TP_B.T)

    TPF = len(TP_A.T)/num_points_a if num_points_a else float('nan')
    FPF = len(FP_B.T)/num_points_b if num_points_b else float('nan')

    error_percentiles = FLE_percentiles(TP_A, TP_B)

    return TPF, FPF, error_percentiles


def FLE_percentiles(TP_A, TP_B):
    percentiles = range(0, 100 + 1)

    if len(TP_B.T) == 0:
        error_percentiles = {
            p: {'p': p, 'r': float('nan'), 'x': float('nan'), 'y': float('nan'), 'z': float('nan')}
            for
            p
            in
            percentiles
        }
    else:
        error_vectors = TP_A - TP_B
        error_vector_norms = np.linalg.norm(error_vectors, axis=0)

        error_percentiles = {
            p: {'p': p, 'r': r, 'x': x, 'y': y, 'z': z}
            for
            p, r, x, y, z
            in
            zip(
                percentiles,
                np.percentile(error_vector_norms, percentiles),
                np.percentile(np.abs(error_vectors[0, :]), percentiles),
                np.percentile(np.abs(error_vectors[1, :]), percentiles),
                np.percentile(np.abs(error_vectors[2, :]), percentiles),
            )
        }

    return error_percentiles


def format_FLE_percentile(error_percentile):
    ep = error_percentile
    msg = "FLE_{} = {:06.4f}mm ({:06.4f}mm, {:06.4f}mm, {:06.4f}mm)"
    return msg.format(ep['p'], ep['r'], ep['x'], ep['y'], ep['z'])


def format_point_metrics(TPF, FPF, FLE_percentiles):
    return (
        f"TPF={TPF}, FPF={FPF}, FLE_100={FLE_percentiles[100]['r']}, "
        f"FLE_50={FLE_percentiles[50]['r']}"
    )
