import argparse

import numpy as np
import scipy.io

import points


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('known_points')
    parser.add_argument('detected_points')
    args = parser.parse_args()
    known_points_xyz = scipy.io.loadmat(args.known_points)['points']
    detected_points_xyz = scipy.io.loadmat(args.detected_points)['points']
    FN_A, TP_A, TP_B, FP_B = points.categorize(known_points_xyz, detected_points_xyz, lambda x: 5)
    print(points.calc_metrics(FN_A, TP_A, TP_B, FP_B))
