import math

import numpy as np
from scipy.spatial import KDTree


def segment(points, distance):
    '''
    Partition an array of (3xM) points into sets that are within a specified
    distance from each other.

    Returns a set of sets of indices that partition the original array of points.
    '''
    adjacency_matrix = _within_distance_adjacency_matrix(points, distance)
    return _extract_subgraphs(adjacency_matrix)


def _within_distance_adjacency_matrix(points, distance):
    '''
    Create an adjacency matrix, where adjacency of any two points is defined as
    being with a certain distance of each other.
    '''
    num_points = points.shape[1]
    adjacency_matrix = np.empty((num_points, num_points), dtype=bool)
    for i in range(num_points):
        for j in range(i + 1):
            if i == j:
                adjacency_matrix[i, j] = True
            else:
                distance_i_j = np.linalg.norm(points[:, i] - points[:, j])
                are_adjacent = distance_i_j <= distance
                adjacency_matrix[i, j] = are_adjacent
                adjacency_matrix[j, i] = are_adjacent
    return adjacency_matrix


def _extract_subgraphs(adjacency_matrix):
    '''
    Given a adjacency matrix (binary and square), return a set of sets of the
    indices of the points that can be reached by hopping from node to node in
    the adjacency matrix (i.e. the subgraph).
    '''
    # flatten the adjacency matrix so that "neighbors of neighbors" are
    # themselves considered "neighbors"; accomplish this by multiplying the
    # matrix at least as many times as there are possible "hops" in the
    # adjacency matrix
    max_number_of_hops = adjacency_matrix.shape[0] - 1
    flattened = adjacency_matrix
    for i in range(_minpow2(max_number_of_hops)):
        flattened = flattened @ flattened

    # NOTE: this depends on the set filtering out duplicates
    return {frozenset(np.nonzero(a)[0]) for a in flattened}


def _minpow2(value):
    return math.ceil(math.log2(value))


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
    _, num_b = B.shape
    assert _ == 3
    _, num_a = A.shape
    assert _ == 3

    kdtree = KDTree(B.T)

    a_b_distances, closest_b_indices = kdtree.query(A.T)

    seen_b_indices = set()

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
                raise NotImplementedError("Multiple points in A match same point in B")
            else:
                seen_b_indices.add(b_indice)

    FN_A = A[:, ~TP_A_indices]
    TP_A = A[:, TP_A_indices]
    TP_B = B[:, TP_B_indices]
    FP_B = B[:, ~TP_B_indices]

    assert FN_A.shape[1] + TP_A.shape[1] == num_a
    assert FP_B.shape[1] + TP_B.shape[1] == num_b

    return FN_A, TP_A, TP_B, FP_B
