import itertools

import matplotlib.pyplot as plt
import ipywidgets as widgets
import numpy as np
from mpl_toolkits.mplot3d import Axes3D


def scatter3(label_to_points):
    colors = itertools.cycle(["r", "b", "g"])

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    for label, points in label_to_points.items():
        color = next(colors)
        ax.scatter(points[0, :], points[1, :], points[2, :], color=color, label=label)

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


def compare_volumes(a, b, z):
    '''
    Display Axial slices from two volumes.
    '''
    dpi = 100

    upsample = 2
    y_pixels = upsample*max(a.shape[0], b.shape[0])
    x_pixels = upsample*(a.shape[1] + b.shape[1])

    plt.figure(dpi=dpi, figsize=(x_pixels/dpi, y_pixels/dpi))

    plt.subplot(121)
    plt.imshow(a[:, :, z], cmap='Greys_r', interpolation="nearest")
    plt.axis('off')

    plt.subplot(122)
    plt.imshow(b[:, :, z], cmap='Greys_r', interpolation="nearest")
    plt.axis('off')

    plt.tight_layout(pad=0, h_pad=0, w_pad=0)


def compare_volumes_interactive(a, b):
    _, _, z_max = a.shape
    keywords = {
        'a': widgets.fixed(a),
        'b': widgets.fixed(b),
        'z': slider(z_max),
    }
    widgets.interact(compare_volumes, **keywords)


def slices_interactive(data, cmap='Greys_r'):
    x_max, y_max, z_max = data.shape
    keywords = {
        'data': widgets.fixed(data),
        'x': slider(x_max),
        'y': slider(y_max),
        'z': slider(z_max),
        'cmap': widgets.fixed(cmap),
    }
    widgets.interact(slices, **keywords)


def slider(maximum):
    return widgets.IntSlider(min=0, max=maximum - 1, step=1, value=round(maximum/2), continuous_update=False)


def turn_off_labels():
    plt.tick_params(
        left='off',
        right='off',
        bottom='off',
        top='off',
        labelbottom='off',
        labelleft='off'
    )
