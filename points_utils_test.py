import pytest
import numpy as np

from points_utils import segment, categorize, metrics, closest


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


class TestCategorize:
    def assert_categorized(self, FN_A, TP_A, TP_B, FP_B, rho):
        # keep test cases clean by casting and handling empty arrays
        FN_A = np.array(FN_A).T if FN_A else np.zeros((3, 0))
        TP_A = np.array(TP_A).T if TP_A else np.zeros((3, 0))
        TP_B = np.array(TP_B).T if TP_B else np.zeros((3, 0))
        FP_B = np.array(FP_B).T if FP_B else np.zeros((3, 0))

        B = np.hstack((FP_B, TP_B))
        A = np.hstack((TP_A, FN_A))

        fn_a, tp_a, tp_b, fp_b = categorize(A, B, rho)
        print(fn_a, tp_a, tp_b, fp_b)

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
            lambda bmag: 0.5
        )

    def test_points_beyond_rho(self):
        self.assert_categorized(
            [[0, 0, 0]],
            [],
            [],
            [[0, 0, 1]],
            lambda bmag: 0.5
        )

    def test_points_in_B_matched_correctly(self):
        self.assert_categorized(
            [],
            [[0, 0, 0]],
            [[0, 0, 0.1]],
            [[0, 0, 0.2]],
            lambda bmag: 0.5
        )

    @pytest.mark.xfail(reason='Not implemented')
    def test_points_in_A_matched_correctly(self):
        self.assert_categorized(
            [[0, 0, 1]],
            [[0, 0, 0]],
            [[0, 0, 0.4]],
            [],
            lambda bmag: 1
        )

    @pytest.mark.xfail(reason='Not implemented')
    def test_rejects_closest_point_for_global_max(self):
        '''
        The first point in A is closer to the second point in B, however it
        should still match with the first point in B because the second point
        in A can not match with the first point in B, hence matching with a
        point further away allows for a global maximum.
        '''
        self.assert_categorized(
            [],
            [[0, 0, 0], [0, 0, 1]],
            [[0, 0.9, 0], [0, 0, 0.4]],
            [],
            lambda bmag: 1
        )


class TestMetrics:
    def test_two_perfectly_matched_points(self):
        A = np.array([
            [0, 0, 0],
        ]).T

        B = np.array([
            [0, 0, 0],
        ]).T

        rho = lambda bmag: 1
        total_error, average_error, random_error_average, TPF, FNF = metrics(*categorize(A, B, rho))

        assert average_error == 0.0
        assert random_error_average == 0.0
        assert TPF == 1.0
        assert FNF == 0.0

    def test_two_matched_points(self):
        A = np.array([
            [0, 0, 0],
        ]).T

        B = np.array([
            [0, 0, 0.1],
        ]).T

        rho = lambda bmag: 1
        total_error, average_error, random_error_average, TPF, FNF = metrics(*categorize(A, B, rho))

        assert average_error == 0.1
        assert random_error_average == 0.0
        assert TPF == 1.0
        assert FNF == 0.0

    def test_four_matched_one_false_negative(self):
        A = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0, 0, 2],
        ]).T

        B = np.array([
            [0, 0, 0.1],
            [1, 0, -0.1],
        ]).T

        rho = lambda bmag: 1
        total_error, average_error, random_error_average, TPF, FNF = metrics(*categorize(A, B, rho))

        assert total_error == 0.1*(2.0/3.0) + 0.1*(1.0/3.0)
        assert average_error == 0.0
        assert random_error_average == 0.1
        assert TPF == 2/3
        assert FNF == 1/3


class TestClosest:
    def assert_ind_distance(self, point, expected_ind, expected_distance):
        A = np.array([
            [0, 0, 0],
            [0, 0, 5],
        ], dtype=float).T

        ind, _, distance = closest(A, np.array(point, dtype=float))
        assert ind == expected_ind
        assert distance == expected_distance

    def test_overlapped(self):
        self.assert_ind_distance([0, 0, 0], 0, 0)

    def test_appart(self):
        self.assert_ind_distance([0, 0, 2], 0, 2)

    def test_seccond_point(self):
        self.assert_ind_distance([0, 1, 5], 1, 1)
