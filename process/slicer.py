import copy

import scipy
import scipy.interpolate
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib.colors import NoNorm

from process import affine
from process.affine import apply_affine


class cyclic_iterator:
    def __init__(self, thelist):
        self.thelist = thelist
        self.index = 0

    def next(self):
        self.index += 1
        if self.index >= len(self.thelist):
            print('\a')
            self.index = 0
        return self.thelist[self.index]

    def prev(self):
        self.index -= 1
        if self.index < 0:
            print('\a')
            self.index = len(self.thelist)-1
        return self.thelist[self.index]


def show_slices(voxels, overlaid_voxels=None):
    """
    Shows voxels and translucent overlay as overlaid_voxels
    :param voxels:
    :param overlaid_voxels: binary voxels mask same shape as voxels. Will be
    labelled and can be iterated using n/N keys.
    :return:
    """
    slicer = Slicer(voxels)
    slicer.add_renderer(render_cursor)
    if overlaid_voxels is not None:
        old_on_key_press = slicer.on_key_press
        labeled, num_labels = scipy.ndimage.measurements.label(overlaid_voxels)
        slicer.num_labels = num_labels
        if num_labels > 100:
            print("Warning lots of labels {}".format(num_labels))
            num_labels = 100
        centroids = []
        for label in range(1, num_labels+1):
            coords_in_label = np.array(np.where(labeled == label))
            centroid = np.mean(coords_in_label, axis=1)
            centroids.append(centroid)

        centroid_iterator = cyclic_iterator(centroids)

        def next_roi():
            centroid = centroid_iterator.next()
            slicer.cursor = np.round(centroid).astype(int)
            slicer.draw()

        slicer.next_roi = next_roi

        def on_key_press(event):
            old_on_key_press(event)
            if event.key == 'n':
                slicer.next_roi()
            elif event.key == 'N':
                centroid = centroid_iterator.prev()
                slicer.cursor = np.round(centroid).astype(int)
                slicer.draw()

        slicer.on_key_press = on_key_press
        cmap = matplotlib.colors.ListedColormap([(0,0,0,0), (0,1,0,1), (1,1,0,1), (1,0,0,1)])
        slicer.add_renderer(render_overlay(overlaid_voxels, alpha=0.5, norm=NoNorm(), cmap=cmap))

    slicer.draw()
    plt.show()
    return slicer


class Slicer:
    def __init__(self, voxels):
        self.f = plt.figure()
        self.voxels = voxels
        self.vmin = np.min(voxels)
        self.vmax = np.max(voxels)
        self.cursor = np.array([d/2 for d in self.voxels.shape], dtype=int)
        self.i_ax = self.f.add_subplot(131)
        self.j_ax = self.f.add_subplot(132)
        self.k_ax = self.f.add_subplot(133)
        self.f.canvas.mpl_connect('scroll_event', lambda e: self.on_scroll(e))
        self.f.canvas.mpl_connect('button_press_event', lambda e: self.on_button_press(e))
        self.f.canvas.mpl_connect('motion_notify_event', lambda e: self.on_mouse_movement(e))
        self.f.canvas.mpl_connect('key_press_event', lambda e: self.on_key_press(e))
        self._renderers = []
        self._renderers_hidden = []
        self.add_renderer(self._render_voxels)

        self.f.tight_layout()

        # move slicer to foreground
        # TODO: fix this; it stopped working with matplotlib 2
        #self.f.canvas.manager.window.raise_()

    def add_renderer(self, renderer, hidden=False):
        self._renderers.append(renderer)
        self._renderers_hidden.append(hidden)

    @staticmethod
    def _render_voxels(slicer):
        imshow_kwargs = {
            'origin': 'upper',
            'cmap': 'Greys_r',
            'vmin': slicer.vmin,
            'vmax': slicer.vmax,
            'interpolation': 'nearest',
        }
        _imshow(slicer, slicer.voxels, imshow_kwargs)

    def axes_dimensions(self, axes):
        if axes == self.i_ax:
            return 0, 1, 2
        elif axes == self.j_ax:
            return 0, 2, 1
        elif axes == self.k_ax:
            return 1, 2, 0
        else:
            raise ValueError()

    def on_scroll(self, event):
        try:
            _, _, slice_dimension = self.axes_dimensions(event.inaxes)
        except ValueError:
            return  # scroll occured off-axis

        self.cursor[slice_dimension] += event.step
        self.ensure_cursor_in_bounds()
        self.draw()

    def on_button_press(self, event):
        self.update_cursor(event)

    def update_cursor(self, event):
        try:
            x_dimension, y_dimension, _ = self.axes_dimensions(event.inaxes)
        except ValueError:
            return  # scroll occured off-axis

        self.cursor[x_dimension] = round(event.xdata)
        self.cursor[y_dimension] = round(event.ydata)
        self.ensure_cursor_in_bounds()
        self.draw()

    def on_mouse_movement(self, event):
        if event.button == 1:
            self.update_cursor(event)

    def on_key_press(self, event):
        number_keys = [str(i) for i in range(10)]
        if event.key in number_keys:
            index = int(event.key)
            if index < len(self._renderers_hidden):
                self._renderers_hidden[index] = not self._renderers_hidden[index]
                self.draw()

    def ensure_cursor_in_bounds(self):
        maximums = np.array(self.voxels.shape, dtype=int) - 1
        minimums = np.array([0, 0, 0], dtype=int)
        self.cursor = np.minimum(maximums, np.maximum(minimums, self.cursor))

    def clear_axes(self):
        for ax in [self.i_ax, self.j_ax, self.k_ax]:
            ax.images = []
            ax.collections = []
            ax.lines = []
            ax.patches = []

    def draw(self):
        self.clear_axes()
        for renderer, hidden in zip(self._renderers, self._renderers_hidden):
            if not hidden:
                renderer(self)
        plt.draw()


def render_overlay(overlay, overlay_ijk_to_xyz, **additional_imshow_kwargs):
    vmin = np.min(overlay)
    vmax = np.max(overlay)

    base_kwargs = {
        'vmin': vmin,
        'vmax': vmax,
        'origin': 'lower',
        'interpolation': 'nearest',
        'cmap': 'Greys_r',
    }

    imshow_kwargs = {**base_kwargs, **additional_imshow_kwargs}
    firstrun = True

    def get_points_ijk(voxels):
        points = np.empty((voxels.size, 3), dtype=int)
        for i in range(0, voxels.shape[0]):
            for j in range(0, voxels.shape[1]):
                for k in range(0, voxels.shape[2]):
                    index = i * voxels.shape[1] * voxels.shape[2] + j * voxels.shape[2] + k
                    points[index, :] = np.array([i, j, k])
        return points.T

    # TODO: if this renderer is initially hidden, toggling it the first time will freeze the program until
    # the reinterpolation is complete
    def renderer(slicer):
        nonlocal firstrun
        nonlocal overlay
        if firstrun and (slicer.voxels.shape != overlay.shape or not np.allclose(slicer.ijk_to_xyz, overlay_ijk_to_xyz)):
            start = time.time()
            overlay_points_ijk = get_points_ijk(overlay)
            overlay_points_xyz = apply_affine(overlay_ijk_to_xyz, overlay_points_ijk.astype(np.double))

            values = np.empty((overlay.size,), dtype=np.double)
            for index, (i, j, k) in enumerate(overlay_points_ijk.T):
                values[index] = overlay[i, j, k]

            slicer_points_ijk = get_points_ijk(slicer.voxels)
            slicer_points_xyz = apply_affine(slicer.ijk_to_xyz, slicer_points_ijk.astype(np.double))

            overlay = scipy.interpolate.griddata(overlay_points_xyz.T, values, slicer_points_xyz.T, method='nearest')
            overlay = overlay.reshape(slicer.voxels.shape)
            end = time.time()
            print(end - start)
        firstrun = False

        assert slicer.voxels.shape == overlay.shape
        _imshow(slicer, overlay, imshow_kwargs)

    return renderer


def render_translucent_overlay(overlay, color, ijk_to_xyz, **additional_imshow_kwargs):
    transparent = [0, 0, 0, 0]
    opaque_color = list(color) + [1]
    colormap = matplotlib.colors.ListedColormap([transparent, opaque_color])

    color_imshow_kwargs = {
        'cmap': colormap,
        'alpha': 0.4,
    }

    imshow_kwargs = {**color_imshow_kwargs, **additional_imshow_kwargs}
    return render_overlay(overlay, ijk_to_xyz, **imshow_kwargs)


def format_point(point):
    x, y, z = point
    return f'({x:.2f},{y:.2f},{z:.2f})'


def _imshow(slicer, voxels, imshow_kwargs):
    i, j, k = slicer.cursor
    slicer.i_ax.imshow(voxels[:, :, k].T, **imshow_kwargs)
    slicer.j_ax.imshow(voxels[:, j, :].T, **imshow_kwargs)
    slicer.k_ax.imshow(voxels[i, :, :].T, **imshow_kwargs)


class PointsSlicer(Slicer):
    def __init__(self, voxels, ijk_to_xyz, points_descriptors):
        super().__init__(voxels)
        self.ijk_to_xyz = ijk_to_xyz
        self.xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        self.voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
        self.points_descriptors = self._transform_points_descriptors(points_descriptors)

    def _transform_points_descriptors(self, points_descriptors):
        points_descriptors = copy.deepcopy(points_descriptors)
        for descriptor in points_descriptors:
            descriptor['points_ijk'] = affine.apply_affine(self.xyz_to_ijk, descriptor['points_xyz'])
            del descriptor['points_xyz']
        return points_descriptors


def render_points(slicer):
    for descriptor in slicer.points_descriptors:
        _scatter_in_slice(slicer, slicer.i_ax, descriptor)
        _scatter_in_slice(slicer, slicer.j_ax, descriptor)
        _scatter_in_slice(slicer, slicer.k_ax, descriptor)


def _scatter_in_slice(slicer, ax, descriptor):
    points = descriptor['points_ijk']
    x_dimension, y_dimension, slice_dimension = slicer.axes_dimensions(ax)
    slice_location = slicer.cursor[slice_dimension]

    point_radius_mm = descriptor.get('point_radius_mm', 5)
    point_radius_pixels = point_radius_mm
    distance_to_slice = np.abs(points[slice_dimension, :] - slice_location)
    indices_in_slice = distance_to_slice < point_radius_pixels

    x = points[x_dimension, indices_in_slice]
    y = points[y_dimension, indices_in_slice]
    r = 6.0*(point_radius_pixels - distance_to_slice[indices_in_slice])

    ylim = ax.get_ylim()
    xlim = ax.get_xlim()
    ax.scatter(x, y, s=r, edgecolors='face', alpha=0.6, **descriptor.get('scatter_kwargs', {}))

    ax.set_ylim(ylim)
    ax.set_xlim(xlim)


def render_legend(slicer):
    slicer.k_ax.legend()


def render_cursor(slicer):
    _render_cursor_location(slicer, slicer.i_ax)
    _render_cursor_location(slicer, slicer.j_ax)
    _render_cursor_location(slicer, slicer.k_ax)

    cursor_xyz = affine.apply_affine(slicer.ijk_to_xyz, slicer.cursor.astype(float).reshape(3,1)).squeeze()
    slicer.f.suptitle('cursor: ' + format_point(cursor_xyz))


def _render_cursor_location(slicer, ax):
    cursor = slicer.cursor
    x_dimension, y_dimension, slice_dimension = slicer.axes_dimensions(ax)
    dimension_to_color_map = {
        0: 'red',
        1: 'green',
        2: 'blue',
    }
    ax.axvline(cursor[x_dimension], color=dimension_to_color_map[x_dimension])
    ax.axhline(cursor[y_dimension], color=dimension_to_color_map[y_dimension])
    set_spine_color(ax, dimension_to_color_map[slice_dimension])


def set_spine_color(ax, color):
    ax.spines['bottom'].set_color(color)
    ax.spines['top'].set_color(color)
    ax.spines['right'].set_color(color)
    ax.spines['left'].set_color(color)
