import itertools

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # import has needed side effect


def scatter3(label_to_points, ax):
    colors = itertools.cycle(["c", "r", "g", "y", "k"])

    for label, points in label_to_points.items():
        color = next(colors)
        ax.scatter(points[0, :], points[1, :], points[2, :], color=color, label=label, s=2)

    ax.set_xlabel('x [mm]')
    ax.set_ylabel('y [mm]')
    ax.set_zlabel('z [mm]')
    plt.legend()


def slices(data, x, y, z, cmap='Greys_r'):
    plt.figure(figsize=(8, 15))

    vmax = np.max(data)
    vmin = min(np.min(data), 0)

    plt.subplot(311)
    plt.imshow(data[x, :, :], cmap=cmap, interpolation="none", vmin=vmin, vmax=vmax)
    plt.title('Coronal')
    turn_off_labels()

    plt.subplot(312)
    plt.imshow(data[:, y, :], cmap=cmap, interpolation="none", vmin=vmin, vmax=vmax)
    plt.title('Saggital')
    turn_off_labels()

    plt.subplot(313)
    plt.imshow(data[:, :, z], cmap=cmap, interpolation="none", vmin=vmin, vmax=vmax)
    plt.title('Axial')
    turn_off_labels()

    plt.tight_layout()
