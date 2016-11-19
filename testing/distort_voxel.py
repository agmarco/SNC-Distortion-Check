import argparse

import math
import numpy as np
import scipy.io
from scipy.ndimage.interpolation import geometric_transform

from affine import apply_affine

def deform(voxels, distort_factor=8e-2):
    '''
    Applies a arbitrary non-linear distortion simulating an MRI distortion. The magnitude of the distortion can be
    tweaked. Returns the distorted voxels array the same shape as the input voxels. Also returns the deformation
    used expressed as a set of points and values associated.
    '''
    i_c, j_c, k_c = np.array(voxels.shape) * 0.5
    distort_factor_i, distort_factor_j, distort_factor_k = distort_factor / np.array(voxels.shape)
    ijk_deform_points = []
    ijk_distort_values = []
    def map_func(ijk_out_coord):
        '''
        Maps coordinates in the output array to the corresponding coordinate in the input array.
        '''
        i, j, k = ijk_out_coord
        # the following was just hand tuned to produce some sort of interesting mri distortion field. This has no
        # basis in reality except for qualitatively looking like a reasonable distortion.
        i_in_coord = i - (i-i_c) * math.pow(abs(j-j_c), 1.4) * distort_factor_i
        j_in_coord = j - (j-j_c) * math.pow(abs(i-i_c), 1.4) * distort_factor_j
        k_in_coord = k - (k-k_c) * math.pow(abs(k-k_c), 1.4) * distort_factor_k
        ijk_deform_points.append((i_in_coord, j_in_coord, k_in_coord,))
        ijk_distort_values.append((i-i_in_coord, j-j_in_coord, k-k_in_coord,))
        return i_in_coord, j_in_coord, k_in_coord

    voxels_distorted = geometric_transform(voxels, map_func)
    return voxels_distorted, np.array(ijk_deform_points), np.array(ijk_distort_values)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Either undistorted input voxels or distorted points')
    parser.add_argument('output')
    parser.add_argument('--distort_factor', type=float, default=0.08, help='The magnitude of the distortion. Typically between 0 to 0.14')
    parser.add_argument('--reduction_factor', type=int, help='How much to decimate the input voxels by, useful for previewing the distortion before processing it.')
    args = parser.parse_args()

    input_data = scipy.io.loadmat(args.input)
    if 'voxels' in input_data:
        # generate the distorted voxels
        voxels = input_data['voxels']
        ijk_to_patient_xyz_transform = input_data['ijk_to_patient_xyz_transform']
        if args.reduction_factor:
            voxels = voxels[::args.reduction_factor, ::args.reduction_factor, ::args.reduction_factor]

        voxels_distorted, ijk_distort_points, ijk_distort_values = deform(voxels, distort_factor=args.distort_factor)
        xyz_distort_points = apply_affine(ijk_to_patient_xyz_transform, ijk_distort_points.T)
        xyz_distort_values = apply_affine(ijk_to_patient_xyz_transform, ijk_distort_values.T)

        scipy.io.savemat(args.output, {
            'voxels': voxels_distorted,
            'ijk_to_patient_xyz_transform': ijk_to_patient_xyz_transform,
            'xyz_distort_points': xyz_distort_points,
            'xyz_distort_values': xyz_distort_values,
        })
