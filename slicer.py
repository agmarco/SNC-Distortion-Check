import copy

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import affine


def show_slices(voxels):
    slicer = Slicer(voxels)
    slicer.add_renderer(render_cursor)
    slicer.draw()
    plt.show()


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
        self.f.canvas.mpl_connect('key_press_event', lambda e: self.on_key_press(e))
        self._renderers = []
        self._renderers_hidden = []
        self.add_renderer(self._render_voxels)

        self.f.tight_layout()

        # move slicer to foreground
        self.f.canvas.manager.window.raise_()

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
            return 2, 1, 0
        elif axes == self.j_ax:
            return 2, 0, 1
        elif axes == self.k_ax:
            return 1, 0, 2
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
        try:
            x_dimension, y_dimension, _ = self.axes_dimensions(event.inaxes)
        except ValueError:
            return  # scroll occured off-axis

        self.cursor[x_dimension] = int(event.xdata)
        self.cursor[y_dimension] = int(event.ydata)
        self.ensure_cursor_in_bounds()
        self.draw()

    def on_key_press(self, event):
        print(event.key)
        number_keys = [str(i) for i in range(10)]
        if event.key in number_keys:
            index = int(event.key)
            if index < len(self._renderers_hidden):
                print(index)
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

    def draw(self):
        self.clear_axes()
        for renderer, hidden in zip(self._renderers, self._renderers_hidden):
            if not hidden:
                renderer(self)
        plt.draw()


def render_overlay(overlay, **additional_imshow_kwargs):
    vmin = np.min(overlay)
    vmax = np.max(overlay)

    base_kwargs = {
        'vmin': vmin,
        'vmax': vmax,
        'origin': 'upper',
        'interpolation': 'nearest',
        'cmap': 'Greys_r',
    }

    imshow_kwargs = {**base_kwargs, **additional_imshow_kwargs}

    def renderer(slicer):
        assert slicer.voxels.shape == overlay.shape
        _imshow(slicer, overlay, imshow_kwargs)

    return renderer


def render_translucent_overlay(overlay, color, **additional_imshow_kwargs):
    transparent = [0, 0, 0, 0]
    opaque_color = list(color) + [1]
    colormap = matplotlib.colors.ListedColormap([transparent, opaque_color])

    color_imshow_kwargs = {
        'cmap': colormap,
        'alpha': 0.4,
    }

    imshow_kwargs = {**color_imshow_kwargs, **additional_imshow_kwargs}
    return render_overlay(overlay, **imshow_kwargs)


def _imshow(slicer, voxels, imshow_kwargs):
    i, j, k = slicer.cursor
    slicer.i_ax.imshow(voxels[i, :, :], **imshow_kwargs)
    slicer.j_ax.imshow(voxels[:, j, :], **imshow_kwargs)
    slicer.k_ax.imshow(voxels[:, :, k], **imshow_kwargs)



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
        _scatter_in_slice(slicer, slicer.i_ax, descriptor)
        _scatter_in_slice(slicer, slicer.j_ax, descriptor)
        _scatter_in_slice(slicer, slicer.k_ax, descriptor)


def _scatter_in_slice(slicer, ax, descriptor):
    points = descriptor['points_ijk']
    x_dimension, y_dimension, slice_dimension = slicer.axes_dimensions(ax)
    slice_location = slicer.cursor[slice_dimension]

    point_radius_mm = descriptor.get('point_radius_mm', 5)
    point_radius_pixels = point_radius_mm/slicer.pixel_spacing[slice_dimension]
    distance_to_slice = np.abs(points[slice_dimension, :] - slice_location)
    indices_in_slice = distance_to_slice < point_radius_pixels

    x = points[x_dimension, indices_in_slice]
    y = points[y_dimension, indices_in_slice]
    r = 6.0*(point_radius_pixels - distance_to_slice[indices_in_slice])

    ax.scatter(x, y, s=r, edgecolors='face', alpha=0.6, **descriptor.get('scatter_kwargs', {}))


def render_legend(slicer):
    slicer.k_ax.legend()


def render_cursor(slicer):
    _render_cursor_location(slicer, slicer.i_ax)
    _render_cursor_location(slicer, slicer.j_ax)
    _render_cursor_location(slicer, slicer.k_ax)


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
