import itertools
import copy

import matplotlib.pylab as plt
import numpy as np

from affine import apply_affine


def overlay_points(voxels, ijk_to_xyz_transform, points_descriptors):
    points_descriptors = copy.deepcopy(points_descriptors)

    xyz_to_ijk_transform = np.linalg.inv(ijk_to_xyz_transform)
    for descriptor in points_descriptors:
        descriptor['points_ijk'] = apply_affine(xyz_to_ijk_transform, descriptor['points_xyz'])
        del descriptor['points_xyz']

    fig = plt.figure()
    ax = fig.add_subplot(111)
    figure_state = {'z':  0}

    def draw():
        clear_axis(ax)
        ax.imshow(voxels[:, :, figure_state['z']], origin='upper', cmap='Greys_r')
        for d in points_descriptors:
            scatter_in_slice(ax, d['points_ijk'], figure_state['z'], d['scatter'])
        fig.canvas.draw()

    def onscroll(event):
        if event.step < 0:
            figure_state['z'] = max(figure_state['z'] - 1, 0)
        elif event.step > 0:
            figure_state['z'] = min(figure_state['z'] + 1, voxels.shape[2] - 1)
        draw()

    fig.canvas.mpl_connect('scroll_event', onscroll)
    draw()
    plt.show()


def scatter_in_slice(ax, points_ijk, slice_location, scatter_kwargs):
    points_in_slice = points_ijk[:, in_slice(slice_location, points_ijk)]
    x_points = points_in_slice[1, :]
    y_points = points_in_slice[0, :]
    r_points = 2.0*np.abs(points_in_slice[2, :] - slice_location)
    ax.scatter(x_points, y_points, s=r_points, edgecolors='face', **scatter_kwargs)
    ax.legend()


def in_slice(slice_location, points):
    # this was qualitatively set to make the visualization look nice, and was
    # not set based on the grid intersection size in the phantom
    point_radius_in_z_pixels = 9.0
    return np.abs(points[2, :] - slice_location) < point_radius_in_z_pixels


def clear_axis(ax):
    ax.images = []
    ax.collections = []
