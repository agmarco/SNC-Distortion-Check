#!/usr/bin/env python
import sys

import dicom
import scipy.io
import matplotlib.pylab as plt
import numpy as np

from dicom_import import combine_slices
from affine import apply_affine


def plot_voxels(voxels):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    current_slice = 0

    def draw():
        # clear existing stuff
        ax.images = []
        ax.collections = []
        ax.imshow(voxels[:, :, current_slice], origin='upper', cmap='Greys_r',  vmin=np.min(voxels), vmax=np.max(voxels))
        fig.canvas.draw()

    def onscroll(event):
        nonlocal current_slice
        if event.step < 0:
            current_slice = max(current_slice - 1, 0)
        elif event.step > 0:
            current_slice = min(current_slice + 1, voxels.shape[2] - 1)

        draw()

    fig.canvas.mpl_connect('scroll_event', onscroll)
    draw()
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Usage: slice_viewer VOXELS_MATFILE')
        sys.exit(1)

    input_data = scipy.io.loadmat(sys.argv[1])
    voxels = input_data['voxels']
    # ijk_to_patient_xyz_transform = input_data['ijk_to_patient_xyz_transform']
    plot_voxels(voxels)
