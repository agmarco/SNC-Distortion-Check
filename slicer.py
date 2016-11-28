import copy

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

import affine


class Slicer:
    def __init__(self, voxels):
        self.f = plt.figure()
        self.voxels = voxels
        self.vmin = np.min(voxels)
        self.vmax = np.max(voxels)
        self.cursor = np.array([0, 0, 0], dtype=int)
        self.i_ax = self.f.add_subplot(224)
        self.j_ax = self.f.add_subplot(223)
        self.k_ax = self.f.add_subplot(221)
        self.f.canvas.mpl_connect('scroll_event', lambda e: self.onscroll(e))
        self._renderers = []

    def add_renderer(self, renderer):
        self._renderers.append(renderer)

    def onscroll(self, event):
        if event.inaxes == self.i_ax:
            scroll_dimension = 0
        elif event.inaxes == self.j_ax:
            scroll_dimension = 1
        elif event.inaxes == self.k_ax:
            scroll_dimension = 2
        else:
            return  # scroll occurred off-axis

        self.cursor[scroll_dimension] += event.step
        self.ensure_cursor_in_bounds()
        self.draw()

    def ensure_cursor_in_bounds(self):
        maximums = np.array(self.voxels.shape, dtype=int) - 1
        minimums = np.array([0, 0, 0], dtype=int)
        self.cursor = np.minimum(maximums, np.maximum(minimums, self.cursor))

    def clear_axes(self):
        self.i_ax.images = []
        self.i_ax.collections = []
        self.j_ax.images = []
        self.j_ax.collections = []
        self.k_ax.images = []
        self.k_ax.collections = []

    def draw(self):
        self.clear_axes()
        for renderer in self._renderers:
            renderer(self)
        plt.draw()


def render_slices(slicer):
    imshow_kwargs = {
        'origin': 'upper',
        'cmap': 'Greys_r',
        'vmin': slicer.vmin,
        'vmax': slicer.vmax,
    }

    i, j, k = slicer.cursor
    slicer.i_ax.imshow(slicer.voxels[i, :, :], **imshow_kwargs)
    slicer.j_ax.imshow(slicer.voxels[:, j, :], **imshow_kwargs)
    slicer.k_ax.imshow(slicer.voxels[:, :, k], **imshow_kwargs)


class PointsSlicer(Slicer):
    def __init__(self, voxels, ijk_to_xyz, points_descriptors):
        super().__init__(voxels)
        self.ijk_to_xyz = ijk_to_xyz
        self.xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        self.pixel_spacing = affine.pixel_spacing(ijk_to_xyz)
        self.points_descriptors = self._transform_points_descriptors(points_descriptors)

    def _transform_points_descriptors(self, points_descriptors):
        points_descriptors = copy.deepcopy(points_descriptors)
        for descriptor in points_descriptors:
            descriptor['points_ijk'] = affine.apply_affine(self.xyz_to_ijk, descriptor['points_xyz'])
            del descriptor['points_xyz']
        return points_descriptors


def render_points(slicer):
    for descriptor in slicer.points_descriptors:
        scatter_in_slice(slicer, 0, descriptor)
        scatter_in_slice(slicer, 1, descriptor)
        scatter_in_slice(slicer, 2, descriptor)


def scatter_in_slice(slicer, slice_dimension, descriptor):
    if slice_dimension == 0:
        x_dimension, y_dimension, ax = 2, 1, slicer.i_ax
    elif slice_dimension == 1:
        x_dimension, y_dimension, ax = 2, 0, slicer.j_ax
    elif slice_dimension == 2:
        x_dimension, y_dimension, ax = 1, 0, slicer.k_ax
    else:
        raise ValueError()

    points = points_in_slice(slicer, slice_dimension, descriptor)
    x = points[x_dimension, :]
    y = points[y_dimension, :]

    slice_location = slicer.cursor[slice_dimension]
    r = 4.0*np.abs(points[slice_dimension, :] - slice_location)

    ax.scatter(x, y, s=r, edgecolors='face', **descriptor['scatter_kwargs'])


def points_in_slice(slicer, slice_dimension, descriptor):
    points = descriptor['points_ijk']
    slice_location = slicer.cursor[slice_dimension]
    point_radius_mm = descriptor.get('point_radius_mm', 4)
    point_radius_pixels = point_radius_mm/slicer.pixel_spacing[slice_dimension]
    distance_to_slice = np.abs(points[slice_dimension, :] - slice_location)
    indices_in_slice = distance_to_slice < point_radius_pixels
    return points[:, indices_in_slice]
