from collections import OrderedDict

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from numpy.lib.function_base import meshgrid
from scipy.interpolate.interpnd import LinearNDInterpolator
from scipy.interpolate.ndgriddata import griddata

import affine
from affine import apply_affine
from visualization import scatter3
import matplotlib.pyplot as plt

GRID_DENSITY_mm = 0.5
SPHERE_STEP_mm = 1
SPHERE_POINTS_PER_AREA = 1


def surface_area(r):
    return 4*np.pi*r*r


def generate_equidistant_sphere(n=256):
    '''
    Evenly samples a unit sphere with n points. Based on the fibonacci lattice
    http://blog.marmakoide.org/?p=1.
    '''
    golden_angle = np.pi * (3 - np.sqrt(5))
    theta = golden_angle * np.arange(n)
    z = np.linspace(1 - 1.0 / n, 1.0 / n - 1, n)
    radius = np.sqrt(1 - z * z)
     
    points = np.zeros((n, 3))
    points[:,0] = radius * np.cos(theta)
    points[:,1] = radius * np.sin(theta)
    points[:,2] = z
    return points


def generate_report(TP_A_S, TP_B, pdf_path):
    '''
    Given the set of matched and registered points, generate a NEMA report.

    Assumes that each column of TP_A_S is matched with the cooresponding column
    of TP_B.
    '''
    assert TP_A_S.shape == TP_B.shape

    error_vecs = TP_A_S - TP_B
    error_mags = np.linalg.norm(error_vecs, axis=0)

    all_points = np.concatenate([TP_A_S, TP_B], axis=1)
    x_max, y_max, z_max = np.max(all_points, axis=1)
    x_min, y_min, z_min = np.min(all_points, axis=1)

    # interpolate onto plane at the isocenter to generate contour
    grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm), np.arange(y_min, y_max, GRID_DENSITY_mm), [0])
    gridded = griddata(TP_B.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')

    # interpolate onto spheres of increasing size to calculate average and max error table
    interpolator = LinearNDInterpolator(TP_B.T, error_mags.T)
    max_sphere_radius = np.min(np.abs([x_min, y_min, z_min, x_max, y_max, z_max]))
    radius2MaxMeanError = OrderedDict()
    for r in np.arange(SPHERE_STEP_mm, max_sphere_radius, SPHERE_STEP_mm):
        num_points = int(round(surface_area(r)/SPHERE_POINTS_PER_AREA))
        equidistant_sphere_points = generate_equidistant_sphere(num_points) * r
        values = interpolator(equidistant_sphere_points)
        max_value, mean_value = np.max(values), np.mean(values)
        radius2MaxMeanError[r] = (max_value, mean_value,)

    quiver_fig = plt.figure()
    ax = quiver_fig.add_subplot(111, projection='3d')
    ax.quiver(*TP_B, *error_vecs)

    points_fig = scatter3({'A_S': TP_A_S, 'B': TP_B})

    contour_fig = plt.figure()
    contour = plt.contour(grid_x.squeeze(), grid_y.squeeze(), gridded.squeeze(), colors='black')
    plt.clabel(contour, inline=True, fontsize=10)
    plt.xlabel('x [mm]')
    plt.ylabel('y [mm]')

    scatter_fig = plt.figure()
    # distances = np.linalg.norm(A, axis=1)
    plt.scatter(list(radius2MaxMeanError.keys()), np.array(list(radius2MaxMeanError.values()))[:, 1])
    plt.xlabel('Distance from Isocenter [mm]')
    plt.ylabel('Distortion Magnitude [mm]')

    table_fig = plt.figure()
    rows = []
    for r, (max_value, mean_value) in radius2MaxMeanError.items():
        rows.append((r, np.round(max_value, 3), np.round(mean_value, 3),))
    plt.table(cellText=rows, colLabels=['Distance from Isocenter [mm]','Maximum Error [mm]', 'Average Error [mm]'], loc='center')
    plt.axis('off')

    with PdfPages(pdf_path) as pdf:
        pdf.savefig(contour_fig)
        pdf.savefig(scatter_fig)
        pdf.savefig(table_fig)
        pdf.savefig(points_fig)
        pdf.savefig(quiver_fig)


if __name__ == '__main__':
    def generate_cube(size, x0=0):
        points = []
        for x in range(-size, size):
            for y in range(-size, size):
                for z in range(-size, size):
                    points.append((float(x), float(y), float(z)))
        return np.array(points).T

    A = generate_cube(8)
    B = generate_cube(8)
    affine_matrix = affine.translation_rotation(0, 0, 0, np.pi/180*2, np.pi/180*2, np.pi/180*2)

    A = apply_affine(affine_matrix, A)
    generate_report(A, B, 'report.pdf')
