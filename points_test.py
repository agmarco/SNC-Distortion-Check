import numpy as np

from points import segment


def fs(*args):
    return frozenset(args)


class TestSegment:
    def test_two_groups(self):
        assert segment(np.array([
            [0, 0, 0],
            [0, 0, 1],
            [0, 0, 4],
        ]).T, 2) == {fs(0, 1), fs(2)}

    def test_two_groups_swapped_indices(self):
        assert segment(np.array([
            [0, 0, 0],
            [0, 0, 4],
            [0, 0, 1],
        ]).T, 2) == {fs(0, 2), fs(1)}

    def test_one_group(self):
        assert segment(np.array([
            [0, 0, 0],
            [0, 0, 1],
            [0, 0, 4],
        ]).T, 3) == {fs(0, 1, 2)}

    def test_multiple_dimensions(self):
        assert segment(np.array([
            [0, 0, 0],
            [0, 0, 1],
            [-1, 0, 0],
            [1, 0, 0],
            [0, 4, 0],
        ]).T, 1) == {fs(0, 1, 2, 3), fs(4)}

    def test_neighbors_of_neighbors_clumped(self):
        assert segment(np.array([
            [0, 0, 0],
            [0, 0, 1],
            [0, 0, 2],
            [0, 0, 3],
            [0, 0, 5],
        ]).T, 1) == {fs(0, 1, 2, 3), fs(4)}
