#!/usr/bin/env python
import argparse
import math
from functools import partial

import numpy as np
from scipy.ndimage.interpolation import geometric_transform

from process import file_io
from process.affine import translation_rotation, apply_affine


def affine_point(mat, point):
    i_in_coord, j_in_coord, k_in_coord, _ = mat @ np.array([*point, 1]).T
    return i_in_coord, j_in_coord, k_in_coord


def chain_transformers(func_list):
    def chained(ijk_out_coord):
        ijk = ijk_out_coord
        for func in func_list:
            ijk = func(ijk)
        return ijk
    return chained


def deform_func(distort_factor=8e-4):
    '''
    Applies a arbitrary non-linear error_mags simulating an MRI error_mags. The magnitude of the error_mags can be
    tweaked. Returns the distorted voxels array the same shape as the input voxels. Also returns the deformation
    used expressed as a set of points and values associated.
    '''
    def undistort_func(ijk_out_coord):
        '''
        Maps coordinates in the output array to the corresponding coordinate in the input array.
        '''
        i, j, k = ijk_out_coord
        # the following was just hand tuned to produce some sort of interesting mri error_mags field. This has no
        # basis in reality except for qualitatively looking like a reasonable error_mags.
        i_in_coord = i - i * math.pow(abs(j), 1.4) * distort_factor
        j_in_coord = j - j * math.pow(abs(i), 1.4) * distort_factor
        k_in_coord = k - k * math.pow(abs(k)+abs(i), 1.3) * distort_factor
        return i_in_coord, j_in_coord, k_in_coord

    def objective(objective_point, distorted_point):
        return np.linalg.norm(objective_point - np.array(undistort_func(distorted_point)))

    def distort_func(ijk_in_coord):
        # find the distorted point that maps to the undistorted_point
        initial_guess = 2 * np.array(ijk_in_coord) - np.array(undistort_func(ijk_in_coord))
        minimize = scipy.optimize.minimize(partial(objective, ijk_in_coord), initial_guess, tol=1e-8)
        if minimize.fun > 0.01:

            raise Exception('Failed to find inverse solution of error_mags function.')
        return minimize.x

    return distort_func, undistort_func


def affine_transform_func(x, y, z, theta, phi, xi):
    '''
    Applies a rigid affine transform to voxels about the center.
    '''
    tmat = translation_rotation(x, y, z, theta, phi, xi)
    itmat = np.linalg.inv(tmat)
    def distort_func(ijk_out_coord):
        return affine_point(tmat, ijk_out_coord)

    def undistort_func(ijk_out_coord):
        return affine_point(itmat, ijk_out_coord)

    return distort_func, undistort_func


def to_xyz(voxels, ijk_to_patient_xyz_transform):
    to_xyz = ijk_to_patient_xyz_transform
    from_ijk = np.linalg.inv(ijk_to_patient_xyz_transform)
    def distort_func(ijk_out_coord):
        return affine_point(to_xyz, ijk_out_coord)

    def undistort_func(ijk_in_coord):
        return affine_point(from_ijk, ijk_in_coord)

    return distort_func, undistort_func

def progress_indicator(expected_iterations, func):
    processed_iterations = 0
    print_every = int(expected_iterations/100)
    def progress_undistort_func(ijk_out_coord):
        nonlocal processed_iterations
        if processed_iterations % print_every == 0:
            print('{}% done'.format(round(processed_iterations/expected_iterations * 100)))
        processed_iterations += 1

        return undistort_func(ijk_out_coord)
    return progress_undistort_func

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('undistorted_voxels', help='Source voxels.')
    parser.add_argument('distorted_voxels', help='Destination to save the distorted voxels')
    parser.add_argument('undistorted_points', help='Undistorted points. Typically this is the manually annotated of the source voxels.')
    parser.add_argument('distorted_points', help='Destination to save the distorted points.')
    parser.add_argument('--distort_factor', type=float, help='The magnitude of the error_mags. Typically between 0 to 0.14')
    parser.add_argument('--xyz_tpx', type=float, nargs=6, help='space separated x,y,z displacement and theta,phi,xi rotation. Rotations should be in degrees.')
    parser.add_argument('--reduction_factor', type=int, help='How much to decimate the input voxels by, useful for previewing the error_mags before processing it.')
    args = parser.parse_args()
    voxel_data = file_io.load_voxels(args.undistorted_voxels)
    voxels = voxel_data['voxels']
    ijk_to_patient_xyz_transform = voxel_data['ijk_to_patient_xyz_transform']
    phantom_name = voxel_data['phantom_name']

    if args.reduction_factor:
        voxels = voxels[::args.reduction_factor, ::args.reduction_factor, ::args.reduction_factor]

    to_xyz_func, from_xyz_func = to_xyz(voxels, ijk_to_patient_xyz_transform)
    undistorters = [from_xyz_func]
    distorters = [to_xyz_func]
    if args.xyz_tpx and args.distort_factor:
        raise Exception("Provide either rotation or error_mags, not both because order is ambiguous (and important.)")
    if args.xyz_tpx:
        x, y, z, theta, pi, xhi = args.xyz_tpx
        theta, pi, xhi = np.deg2rad(theta), np.deg2rad(pi), np.deg2rad(xhi)
        distort_func, undistort_func = affine_transform_func(x, y, z, theta, pi, xhi)
        distorters.append(distort_func)
        undistorters.append(undistort_func)
    if args.distort_factor:
        distort_func, undistort_func = deform_func(distort_factor=args.distort_factor)
        distorters.append(distort_func)
        undistorters.append(undistort_func)

    undistorters.append(to_xyz_func)
    undistorters.reverse()
    distorters.append(from_xyz_func)

    distort_func = chain_transformers(distorters)
    undistort_func = chain_transformers(undistorters)

    print('distorting points for {}'.format(args.distorted_points))
    undistorted_points_xyz = file_io.load_points(args.undistorted_points)['points']
    undistorted_points_ijk = apply_affine(np.linalg.inv(ijk_to_patient_xyz_transform), undistorted_points_xyz)
    distorted_points_ijk = np.array(list(map(distort_func, undistorted_points_ijk.T))).T
    distorted_points_xyz = apply_affine(ijk_to_patient_xyz_transform, distorted_points_ijk)
    file_io.save_points(args.distorted_points, {
        'points': distorted_points_xyz,
        'undistorted_points': undistorted_points_xyz,
    })
    print('Done distorting points')

    print('distorting voxels for {}'.format(args.distorted_voxels))
    voxels_distorted = geometric_transform(voxels, progress_indicator(voxels.size, undistort_func))
    file_io.save_voxels(args.distorted_voxels, {
        'voxels': voxels_distorted,
        'ijk_to_patient_xyz_transform': ijk_to_patient_xyz_transform,
        'phantom_name': phantom_name,
    })
    print('Done distorting voxels')
