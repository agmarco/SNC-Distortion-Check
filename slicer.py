import matplotlib.pyplot as plt
import matplotlib
import numpy as np


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
        self.draw()

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
