import pytest
import numpy as np

from points import segment, categorize


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


@pytest.mark.david
class TestCategorize:
    def assert_categorized(FN_A, TP_A, TP_B, FP_B, rho):
        # keep test cases clean by casting and handling empty arrays
        FN_A = np.array(FN_A) if FN_A else np.zeros((3, 0))
        TP_A = np.array(TP_A) if TP_A else np.zeros((3, 0))
        TP_B = np.array(TP_B) if TP_B else np.zeros((3, 0))
        FP_B = np.array(FP_B) if FP_B else np.zeros((3, 0))

        B = np.hstack(FP_B, TP_B)
        A = np.hstack(TP_A, FN_A)

        fn_a, tp_a, tp_b, fp_b = categorize(A, B, rho)

        # depends on implementation preserving column order
        assert np.alltrue(fn_a == FN_A)
        assert np.alltrue(tp_a == TP_A)
        assert np.alltrue(tp_b == TP_B)
        assert np.alltrue(fp_b == FP_B)

    def test_two_matches(self):
        self.assert_categorized(
            [],
            [[0, 0, 0], [0, 0, 1]],
            [[0, 0, 0], [0, 0, 1]],
            [],
            lambda bmag: bmag < 0.5
        )

    def test_points_beyond_rho(self):
        self.assert_categorized(
            [[0, 0, 0]],
            [],
            [],
            [[0, 0, 1]],
            lambda bmag: bmag < 0.5
        )

    def test_points_in_B_matched_correctly(self):
        self.assert_categorized(
            [],
            [[0, 0, 0]],
            [[0, 0, 0.1]],
            [[0, 0, 0.2]],
            lambda bmag: bmag < 0.5
        )

    def test_points_in_A_matched_correctly(self):
        self.assert_categorized(
            [[0, 0, 1]],
            [[0, 0, 0]],
            [[0, 0, 0.4]],
            [],
            lambda bmag: bmag < 1
        )
