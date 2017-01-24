import pytest
import numpy as np
from numpy.testing import assert_allclose

from points_utils import categorize, metrics, closest, _valid_location


def fs(*args):
    return frozenset(args)


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
        FLE_mean, TPF, FNF, FPF = metrics(*categorize(A, B, rho))

        assert FLE_mean == 0.0
        assert TPF == 1.0
        assert FNF == 0.0
        assert FPF == 0.0

    def test_two_matched_points(self):
        A = np.array([
            [0, 0, 0],
        ]).T

        B = np.array([
            [0, 0, 0.1],
        ]).T

        rho = lambda bmag: 1
        FLE_mean, TPF, FNF, FPF = metrics(*categorize(A, B, rho))

        assert FLE_mean == 0.1
        assert TPF == 1.0
        assert FNF == 0.0
        assert FPF == 0.0

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
        FLE_mean, TPF, FNF, FPF = metrics(*categorize(A, B, rho))

        assert FLE_mean == 0.1
        assert TPF == 2/3
        assert FNF == 1/3
        assert FPF == 0.0


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


class TestValidLocation:
    def test_location_in_center(self):
        assert not _valid_location((0, 1), data_shape=(4, 5), kernel_shape=(3, 3))
        assert not _valid_location((0, 0), data_shape=(4, 5), kernel_shape=(3, 3))
        assert not _valid_location((1, 0), data_shape=(4, 5), kernel_shape=(3, 3))
        assert not _valid_location((-1, -1), data_shape=(4, 5), kernel_shape=(3, 3))

        assert _valid_location((1, 1), data_shape=(4, 5), kernel_shape=(3, 3))
        assert _valid_location((2, 3), data_shape=(4, 5), kernel_shape=(3, 3))
        assert _valid_location((2, 2), data_shape=(4, 5), kernel_shape=(3, 3))
        assert _valid_location((1, 3), data_shape=(4, 5), kernel_shape=(3, 3))
        assert _valid_location((2, 1), data_shape=(4, 5), kernel_shape=(3, 3))

        assert not _valid_location((3, 3), data_shape=(4, 5), kernel_shape=(3, 3))
        assert not _valid_location((3, 4), data_shape=(4, 5), kernel_shape=(3, 3))
