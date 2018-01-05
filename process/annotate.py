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
    def __init__(self, voxels, ijk_to_xyz, points_descriptors):
        super().__init__(voxels, ijk_to_xyz, points_descriptors)
        self.selected_descriptor = None
        self.selected_indice = None
        self.f.canvas.mpl_connect('key_press_event', lambda e: self.on_key_press(e))
        reclassify_lookup_inv = {
            0: '!',
            1: '@',
            2: '#',
            3: '$',
            4: '%',
            5: '^',
            6: '&',
            7: '*',
            8: '(',
        }
        reclassify_indices = range(min(len(self.points_descriptors), 9))
        self.reclassify_lookup = {v: k for k, v in reclassify_lookup_inv.items() if k in reclassify_indices}

    def on_button_press(self, event):
        if event.button == 3:  # right click
            x_dimension, y_dimension, slice_dimension = self.axes_dimensions(event.inaxes)
            new_point = np.empty((3, 1), dtype=float)
            new_point[x_dimension] = event.xdata
            new_point[y_dimension] = event.ydata
            new_point[slice_dimension] = self.cursor[slice_dimension]

            closest_indices = []
            distances = []
            for descriptor in self.points_descriptors:
                points = descriptor['points_ijk']
                num_points = points.shape[1]
                if num_points > 0:
                    closest_indice, _, distance = closest(points, new_point)
                    closest_indices.append(closest_indice)
                    distances.append(distance)
                else:
                    closest_indices.append(-1)
                    distances.append(float('inf'))

            closest_distance = min(distances)

            if closest_distance < 5:
                points_descriptor_indice = distances.index(closest_distance)
                descriptor = self.points_descriptors[points_descriptor_indice]
                points = descriptor['points_ijk']
                closest_indice, distance = list(zip(closest_indices, distances))[points_descriptor_indice]

                if 'label' in descriptor['scatter_kwargs']:
                    descriptor_label = descriptor['scatter_kwargs']['label']
                else:
                    descriptor_label = points_descriptor_indice
                log.info(f"Selecting point {descriptor_label}: {closest_indice}")
                self.selected_descriptor = points_descriptor_indice
                self.selected_indice = closest_indice
                self.cursor = points[:, self.selected_indice].astype(int)
                self.draw()
            else:
                points = self.points_descriptors[0]['points_ijk']
                self.points_descriptors[0]['points_ijk'] = np.append(points, new_point, axis=1)
                self.draw()
        else:
            super().on_button_press(event)

    def on_key_press(self, event):
        if self.selected_descriptor is None:
            if event.key == 'tab':
                self.selected_descriptor = 0
            else:
                return

        points = self.points_descriptors[self.selected_descriptor]['points_ijk']
        num_points = points.shape[1]

        if self.selected_indice is None:
            if event.key == 'tab' and num_points > 0:
                self.selected_indice = 0
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
            self.selected_descriptor = None
            self.selected_indice = None
        elif event.key in ['d', 'e', 'delete']:
            points_without_selected = points[:, np.arange(num_points) != self.selected_indice]
            self.points_descriptors[self.selected_descriptor]['points_ijk'] = points_without_selected
            points = points_without_selected
            num_points = num_points - 1
            if num_points == 0 or event.key == 'e':
                self.selected_descriptor = None
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
        elif event.key in self.reclassify_lookup.keys():
            new_descriptor_index = self.reclassify_lookup[event.key]
            self.reclassify_point(new_descriptor_index)
            points = self.points_descriptors[self.selected_descriptor]['points_ijk']
        else:
            print(event.key)
            return super().on_key_press(event)

        if self.selected_indice is not None:
            self.cursor = points[:, self.selected_indice].astype(int)
            self.ensure_cursor_in_bounds()

        self.draw()

    def reclassify_point(self, new_descriptor_index):
        if self.selected_descriptor != new_descriptor_index:
            old_points = self.points_descriptors[self.selected_descriptor]['points_ijk']
            new_points = self.points_descriptors[new_descriptor_index]['points_ijk']
            num_old_points = old_points.shape[1]
            selected_point = old_points[:, self.selected_indice]
            old_points = old_points[:, np.arange(num_old_points) != self.selected_indice]
            self.points_descriptors[self.selected_descriptor]['points_ijk'] = old_points
            new_points = np.append(new_points, np.array([selected_point]).T, axis=1)
            self.points_descriptors[new_descriptor_index]['points_ijk'] = new_points
            self.selected_descriptor = new_descriptor_index
            self.selected_indice = new_points.shape[1] - 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('voxels')
    parser.add_argument('points', help='if points file exists, append, else create new file')
    args = parser.parse_args()

    voxel_data = file_io.load_voxels(args.voxels)
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_xyz']

    try:
        points_xyz = file_io.load_points(args.points)['points']
        assert points_xyz.shape[1] > 0
        log.info('{} existing points found in {}'.format(points_xyz.shape[1], args.points))
    except:
        points_xyz = np.zeros((3, 0))
        log.info('No existing points found in {}'.format(args.points))

    points_descriptors = [{'points_xyz': points_xyz, 'scatter_kwargs': {'color': 'g'}}]
    slicer = AnnotateSlicer(voxels, ijk_to_xyz, points_descriptors)
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
