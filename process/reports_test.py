import numpy as np

from process.reports import generate_equidistant_sphere


def test_evenly_sampled_sphere_equidistant():
    '''
    Asserts the algorithm to evenly space points on a sphere appears to work as expected.
    '''
    n = 256
    points = generate_equidistant_sphere(n)
    min_distances_squared = []
    for point in points:
        distances_squared = np.sum((points.T - point.reshape((3, 1)))**2, axis=0)
        min_distance = np.min(distances_squared[distances_squared>0])
        min_distances_squared.append(min_distance)
    distances = np.sqrt(np.array(min_distances_squared))
    std = np.std(distances)
    mean = np.mean(distances)
    cv = std / mean
    assert cv < 0.02
