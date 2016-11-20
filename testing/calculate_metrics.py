import argparse

import numpy as np
import scipy.io

from points import categorize


def calc_metrics(known_points_xyz, detected_points_xyz):
    FN_A, TP_A, TP_B, FP_B = categorize(known_points_xyz, detected_points_xyz, lambda x: 5)
    average_error = np.average(np.linalg.norm((TP_A - TP_B).T, axis=1))
    FPF = len(FP_B.T) / len(known_points_xyz.T)
    FNF = len(FN_A.T) / len(known_points_xyz.T)
    TPF = len(TP_A.T) / len(known_points_xyz.T)
    return average_error, TPF, FPF, FNF


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('known_points')
    parser.add_argument('detected_points')
    args = parser.parse_args()
    known_points_xyz = scipy.io.loadmat(args.known_points)['points']
    detected_points_xyz = scipy.io.loadmat(args.detected_points)['points']
    average_error, TPF, FPF, FNF = calc_metrics(known_points_xyz, detected_points_xyz)
    print(average_error, TPF, FPF, FNF)
