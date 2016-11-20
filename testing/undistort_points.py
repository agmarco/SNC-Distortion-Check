import argparse
import base64
import math

import numpy as np
import scipy.io
import dill as pickle

from affine import apply_affine


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('distorted_voxels')
    parser.add_argument('distorted_points')
    parser.add_argument('undistorted_points')
    args = parser.parse_args()
    loaded_distorted_voxels = scipy.io.loadmat(args.distorted_voxels)
    distort_func = pickle.loads(base64.b64decode(loaded_distorted_voxels['distort_func']))
    ijk_to_patient_xyz_transform = loaded_distorted_voxels['ijk_to_patient_xyz_transform']
    distorted_points_xyz = scipy.io.loadmat(args.distorted_points)['points']
    distorted_points_ijk = apply_affine(np.linalg.inv(ijk_to_patient_xyz_transform), distorted_points_xyz)
    undistorted_points_ijk = np.array(list(map(distort_func, distorted_points_ijk.T))).T
    undistorted_points_xyz = apply_affine(ijk_to_patient_xyz_transform, undistorted_points_ijk)
    scipy.io.savemat(args.undistorted_points, {
        'points': undistorted_points_xyz
    })
