import argparse

import numpy as np
import scipy.io

from points import categorize


def calc_metrics(FN_A, TP_A, TP_B, FP_B):
    num_points_a = len(FN_A.T) + len(TP_A.T)
    error_vec = (TP_A - TP_B).T
    average_error_vec = np.average(error_vec, axis=0)
    error_vec_norms = np.linalg.norm(error_vec, axis=1)
    average_error = np.average(error_vec_norms)

    random_error_vec = error_vec - average_error_vec
    random_error_norms = np.linalg.norm(random_error_vec, axis=1)
    random_error_average = np.average(random_error_norms)

    FPF = len(FP_B.T) / num_points_a
    FNF = len(FN_A.T) / num_points_a
    TPF = len(TP_A.T) / num_points_a
    return average_error, random_error_average, TPF, FPF, FNF


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('known_points')
    parser.add_argument('detected_points')
    args = parser.parse_args()
    known_points_xyz = scipy.io.loadmat(args.known_points)['points']
    detected_points_xyz = scipy.io.loadmat(args.detected_points)['points']
    FN_A, TP_A, TP_B, FP_B = categorize(known_points_xyz, detected_points_xyz, lambda x: 5)
    print(calc_metrics(FN_A, TP_A, TP_B, FP_B))
