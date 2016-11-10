import math

import numpy as np


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
    indices of the points.
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
