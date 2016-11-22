#!/usr/bin/env python
import argparse

import numpy as np
import scipy.io

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_voxels')
    parser.add_argument('output_voxels')
    parser.add_argument('decimation_factor', type=int)
    args = parser.parse_args()

    input_mat = scipy.io.loadmat(args.input_voxels)
    ijk_to_patient_xyz_transform = input_mat['ijk_to_patient_xyz_transform']
    input_voxels = input_mat['voxels']
    if args.decimation_factor == 1:
        output_voxels = input_voxels
    else:
        output_voxels = np.zeros_like(input_voxels)
        for i in range(0, input_voxels.shape[2], args.decimation_factor):
            to_index = min(i+args.decimation_factor, input_voxels.shape[2] - 1)
            slices_to_average = input_voxels[:, :, i:to_index]
            average_slice = np.average(slices_to_average, axis=2)
            output_voxels[:, :, i:to_index] = np.dstack([average_slice]*(to_index-i))

    scipy.io.savemat(args.output_voxels, {
        'voxels': output_voxels,
        'ijk_to_patient_xyz_transform': ijk_to_patient_xyz_transform
    })
