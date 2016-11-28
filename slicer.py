import copy

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

import affine


class Slicer:
    def __init__(self, voxels):
        self.f = plt.figure()
        self.voxels = voxels
        self._vmin = np.min(voxels)
        self._vmax = np.max(voxels)
        self.cursor = np.array([0, 0, 0], dtype=int)
        self.i_ax = self.f.add_subplot(224)
        self.j_ax = self.f.add_subplot(223)
        self.k_ax = self.f.add_subplot(221)
        self.f.canvas.mpl_connect('scroll_event', lambda e: self.onscroll(e))

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
        self.draw_slices()
        plt.draw()

    def draw_slices(self):
        imshow_kwargs = {
            'origin': 'upper',
            'cmap': 'Greys_r',
            'vmin': self._vmin,
            'vmax': self._vmax,
        }

        i, j, k = self.cursor
        self.i_ax.imshow(self.voxels[i, :, :], **imshow_kwargs)
        self.j_ax.imshow(self.voxels[:, j, :], **imshow_kwargs)
        self.k_ax.imshow(self.voxels[:, :, k], **imshow_kwargs)


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

    def draw(self):
        self.clear_axes()
        self.draw_slices()
        self.draw_points()
        plt.draw()

    def draw_points(self):
        for descriptor in self.points_descriptors:
            self.scatter_in_slice(0, descriptor)
            self.scatter_in_slice(1, descriptor)
            self.scatter_in_slice(2, descriptor)

    def scatter_in_slice(self, slice_dimension, descriptor):
        if slice_dimension == 0:
            x_dimension, y_dimension, ax = 2, 1, self.i_ax
        elif slice_dimension == 1:
            x_dimension, y_dimension, ax = 2, 0, self.j_ax
        elif slice_dimension == 2:
            x_dimension, y_dimension, ax = 1, 0, self.k_ax
        else:
            raise ValueError()

        points = self.points_in_slice(slice_dimension, descriptor)
        x = points[x_dimension, :]
        y = points[y_dimension, :]

        slice_location = self.cursor[slice_dimension]
        r = 4.0*np.abs(points[slice_dimension, :] - slice_location)

        ax.scatter(x, y, s=r, edgecolors='face', **descriptor['scatter_kwargs'])

    def points_in_slice(self, slice_dimension, descriptor):
        points = descriptor['points_ijk']
        slice_location = self.cursor[slice_dimension]
        point_radius_mm = descriptor.get('point_radius_mm', 4)
        point_radius_pixels = point_radius_mm/self.pixel_spacing[slice_dimension]
        distance_to_slice = np.abs(points[slice_dimension, :] - slice_location)
        indices_in_slice = distance_to_slice < point_radius_pixels
        return points[:, indices_in_slice]
