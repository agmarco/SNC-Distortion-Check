import argparse
import matplotlib.pyplot as plt
import numpy as np

from process import file_io, affine, slicer
from process.affine import apply_affine


cube_size = 45
window_shape = np.array((cube_size, cube_size, cube_size))
cube_size_half = window_shape // 2

datasets = {
    '604-1': {
        'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
        'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
    },
}


def show(voxels, ijk_to_xyz, point_ijk, cursor):
    point_xyz = affine.apply_affine_1(ijk_to_xyz, point_ijk)
    descriptors = [
        {
            'points_xyz': np.array([point_xyz]).T,
            'scatter_kwargs': {
                'color': 'g',
                'label': 'Gold Standard',
                'marker': 'o',
            }
        },
    ]

    s = slicer.PointsSlicer(voxels, ijk_to_xyz, descriptors)
    s.cursor = cursor
    s.add_renderer(slicer.render_points)
    s.add_renderer(slicer.render_cursor)
    s.draw()
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phantom')
    args = parser.parse_args()
    assert args.phantom in datasets
    dataset = datasets[args.phantom]
    voxel_data = file_io.load_voxels(dataset['voxels'])
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_xyz']
    xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
    voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
    golden_points = file_io.load_points(dataset['points'])['points']
    points_ijk = apply_affine(xyz_to_ijk, golden_points)
    for point_ijk in points_ijk.T:
        i, j, k = np.round(point_ijk).astype(int)
        window = (
            (i - cube_size_half[0], i + cube_size_half[0]),
            (j - cube_size_half[1], j + cube_size_half[1]),
            (k - cube_size_half[2], k + cube_size_half[2]),
        )
        window_adjusted = (
            (max(window[0][0], 0), min(window[0][1], voxels.shape[0])),
            (max(window[1][0], 0), min(window[1][1], voxels.shape[1])),
            (max(window[2][0], 0), min(window[2][1], voxels.shape[2])),
        )
        window_slice_tup = tuple(slice(*bounds) for bounds in window_adjusted)
        voxel_window = voxels[window_slice_tup]
        if voxel_window is not None:  # TODO
            ijk_offset = np.array([-a for a, b in window_adjusted])
            translation = np.array([
                [1, 0, 0, ijk_offset[0]],
                [0, 1, 0, ijk_offset[1]],
                [0, 0, 1, ijk_offset[2]],
                [0, 0, 0, 1],
            ])
            point_ijk = affine.apply_affine_1(translation, point_ijk)

            cursor = np.array([(b - a) / 2 for a, b in window], dtype=int)
            cursor_offset = np.array([min(a, 0) for a, b in window])
            cursor = np.add(cursor, cursor_offset)

            show(voxel_window, ijk_to_xyz, point_ijk, cursor)
