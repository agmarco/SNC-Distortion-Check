#!/usr/bin/env python
import argparse

import numpy as np

from process import file_io

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_voxels')
    parser.add_argument('output_voxels')
    parser.add_argument('decimation_factor', type=int)
    args = parser.parse_args()

    voxels_data = file_io.load_voxels(args.input_voxels)
    ijk_to_patient_xyz_transform = voxels_data['ijk_to_patient_xyz_transform']
    input_voxels = voxels_data['voxels']
    phantom_name = voxels_data['phantom_name']

    if args.decimation_factor == 1:
        output_voxels = input_voxels
    else:
        output_voxels = np.zeros_like(input_voxels)
        for i in range(0, input_voxels.shape[2], args.decimation_factor):
            to_index = min(i+args.decimation_factor, input_voxels.shape[2] - 1)
            slices_to_average = input_voxels[:, :, i:to_index]
            average_slice = np.average(slices_to_average, axis=2)
            output_voxels[:, :, i:to_index] = np.dstack([average_slice]*(to_index-i))

    file_io.save_voxels(args.output_voxels, {
        'voxels': output_voxels,
        'ijk_to_patient_xyz_transform': ijk_to_patient_xyz_transform,
        'phantom_name': phantom_name,
    })
