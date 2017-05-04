#!/usr/bin/env python
import argparse
import logging

import matplotlib.pylab as plt
import numpy as np

from process import file_io
from process.points_utils import closest
from process.affine import apply_affine
from process.slicer import PointsSlicer, render_cursor, render_points

log = logging.getLogger(__name__)


class AnnotateSlicer(PointsSlicer):
    def __init__(self, voxels, ijk_to_xyz, points_xyz):
        points_descriptors = [{'points_xyz': points_xyz, 'scatter_kwargs': {'color': 'g'}}]
        super().__init__(voxels, ijk_to_xyz, points_descriptors)
        self.selected_indice = None
        self.f.canvas.mpl_connect('key_press_event', lambda e: self.on_key_press(e))

    def on_button_press(self, event):
        if event.button == 3:  # right click
            points = self.points_descriptors[0]['points_ijk']
            num_points = points.shape[1]

            x_dimension, y_dimension, slice_dimension = slicer.axes_dimensions(event.inaxes)
            new_point = np.empty((3, 1), dtype=float)
            new_point[x_dimension] = event.xdata
            new_point[y_dimension] = event.ydata
            new_point[slice_dimension] = slicer.cursor[slice_dimension]

            if num_points > 0:
                closest_indice, _, distance = closest(points, new_point)
            else:
                distance = float('inf')

            if distance < 5:
                log.info("Selecting point {}".format(closest_indice))
                self.selected_indice = closest_indice
                self.cursor = points[:, self.selected_indice].astype(int)
                self.draw()
            else:
                self.points_descriptors[0]['points_ijk'] = np.append(points, new_point, axis=1)
                self.draw()
        else:
            super().on_button_press(event)

    def on_key_press(self, event):
        points = self.points_descriptors[0]['points_ijk']
        num_points = points.shape[1]

        if self.selected_indice is None:
            if event.key == 'tab' and num_points > 0:
                self.selected_indice = 1
            else:
                return

        nudge_size = 0.06
        nudge_lookup = {
            '1': [0, nudge_size, 0],
            '2': [0, -nudge_size, 0],
            '3': [-nudge_size, 0, 0],
            '4': [nudge_size, 0, 0],
            '5': [0, 0, nudge_size],
            '6': [0, 0, -nudge_size],
        }

        if event.key == 'esc':
            self.selected_indice = None
        elif event.key in ['d', 'e', 'delete']:
            points_without_selected = points[:, np.arange(num_points) != self.selected_indice]
            self.points_descriptors[0]['points_ijk'] = points_without_selected
            points = points_without_selected
            num_points = num_points - 1
            if num_points == 0 or event.key == 'e':
                self.selected_indice = None
            else:
                self.selected_indice = self.selected_indice % num_points
            print('deleting point')
        elif event.key == 'shift+tab':
            # TODO: shift+tab does not appear to be recognized
            self.selected_indice = (self.selected_indice - 1) % num_points
        elif event.key == 'tab':
            self.selected_indice = (self.selected_indice + 1) % num_points
        elif event.key in nudge_lookup:
            nudge_list = nudge_lookup[event.key]
            nudge = np.array(nudge_list, dtype=float)
            points[:, self.selected_indice] += nudge
        else:
            print(event.key)
            return super().on_key_press(event)

        if self.selected_indice is not None:
            self.cursor = points[:, self.selected_indice].astype(int)
            self.ensure_cursor_in_bounds()

        self.draw()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('voxels')
    parser.add_argument('points', help='if points file exists, append, else create new file')
    args = parser.parse_args()

    voxel_data = file_io.load_voxels(args.voxels)
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']

    try:
        points_xyz = file_io.load_points(args.points)['points']
        assert points_xyz.shape[1] > 0
        log.info('{} existing points found in {}'.format(points_xyz.shape[1], args.points))
    except:
        points_xyz = np.zeros((3, 0))
        log.info('No existing points found in {}'.format(args.points))

    slicer = AnnotateSlicer(voxels, ijk_to_xyz, points_xyz)
    slicer.add_renderer(render_points)
    slicer.add_renderer(render_cursor)
    slicer.draw()
    plt.show()

    points_ijk = slicer.points_descriptors[0]['points_ijk']
    points_xyz = apply_affine(ijk_to_xyz, points_ijk)
    file_io.save_points(args.points, {
        'points': points_xyz,
    })
    log.info('Wrote {} points to {}'.format(points_xyz.shape[1], args.points))
