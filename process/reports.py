import os
import zipfile
import math
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from django.conf import settings
from matplotlib import colors
from matplotlib.backends.backend_pdf import PdfPages
from scipy.interpolate.interpnd import LinearNDInterpolator
from scipy.interpolate.ndgriddata import griddata

from process import affine, phantoms
from process.affine import apply_affine, voxel_spacing
from process.visualization import scatter3
from process.utils import chunks
from process import dicom_import

GRID_DENSITY_mm = 0.5
SPHERE_STEP_mm = 1
SPHERE_POINTS_PER_AREA = 1
CONTOUR_SERIES_STEP_mm = 2


def surface_area(r):
    return 4*np.pi*r*r


def generate_equidistant_sphere(n=256):
    """
    Evenly samples a unit sphere with n points. Based on the fibonacci lattice
    http://blog.marmakoide.org/?p=1.
    """

    golden_angle = np.pi * (3 - np.sqrt(5))
    theta = golden_angle * np.arange(n)
    z = np.linspace(1 - 1.0 / n, 1.0 / n - 1, n)
    radius = np.sqrt(1 - z * z)
     
    points = np.zeros((n, 3))
    points[:, 0] = radius * np.cos(theta)
    points[:, 1] = radius * np.sin(theta)
    points[:, 2] = z
    return points


def roi_shape(grid_radius, voxel_spacing):
    return tuple(math.ceil(grid_radius / dim * 8) for dim in voxel_spacing)


def roi_bounds(B, shape):
    return tuple((
        int(math.ceil(a)) - int(math.floor(b / 2)),
        int(math.ceil(a)) + int(math.ceil(b / 2)),
    ) for a, b in zip(B, shape))


def roi_image(voxels, bounds_list):
    adjusted_bounds_list = tuple((max(start, 0), min(end, voxels.shape[i])) for i, (start, end) in enumerate(bounds_list))
    slices = tuple(slice(*bounds) for bounds in adjusted_bounds_list)
    image = voxels[slices].squeeze()

    v_bounds, h_bounds = [bounds for bounds in bounds_list if bounds[1] - bounds[0] > 1]

    if v_bounds[0] < 0:
        zeros = np.zeros((0 - v_bounds[0], image.shape[1]), dtype=float)
        image = np.vstack((zeros, image))
    if v_bounds[1] > voxels.shape[0]:
        zeros = np.zeros((v_bounds[1] - voxels.shape[0], image.shape[1]), dtype=float)
        image = np.vstack((image, zeros))
    if h_bounds[0] < 0:
        zeros = np.zeros((image.shape[0], 0 - h_bounds[0]), dtype=float)
        image = np.hstack((zeros, image))
    if h_bounds[1] > voxels.shape[1]:
        zeros = np.zeros((image.shape[0], h_bounds[1] - voxels.shape[1]), dtype=float)
        image = np.hstack((image, zeros))

    return image


def roi_images(B, voxels, bounds_list):
    return (
        roi_image(voxels, (bounds_list[0], bounds_list[1], (int(round(B[2])), int(round(B[2])) + 1))),
        roi_image(voxels, (bounds_list[0], (int(round(B[1])), int(round(B[1])) + 1), bounds_list[2])),
        roi_image(voxels, ((int(round(B[0])), int(round(B[0])) + 1), bounds_list[1], bounds_list[2])),
    )


def generate_reports(TP_A_S, TP_B, datasets, voxels, ijk_to_xyz, phantom_model_number, threshold, institution, full_report_path, executive_report_path):
    """
    Given the set of matched and registered points, generate a NEMA report.

    Assumes that each column of TP_A_S is matched with the cooresponding column
    of TP_B.
    """

    assert TP_A_S.shape == TP_B.shape

    error_vecs = TP_A_S - TP_B
    error_mags = np.linalg.norm(error_vecs, axis=0)

    x_min, y_min, z_min = np.min(TP_A_S, axis=1)
    x_max, y_max, z_max = np.max(TP_A_S, axis=1)

    grid_radius = phantoms.paramaters[phantom_model_number]['grid_radius']
    figsize = (8.5, 11)

    # TODO: use the correct isocenter (it is not at the geometric origin)
    isocenter = (np.mean([x_min, x_max]), np.mean([y_min, y_max]), np.mean([z_min, z_max]))

    def add_header():
        # plt.text(0.5, 0.5, "CIRS Distortion Check")
        pass

    def generate_cover_page():
        fig = plt.figure(figsize=figsize)
        add_header()
        plt.axis('off')
        im = mpimg.imread(os.path.join(settings.BASE_DIR, 'client/src/login/logo.png'))
        plt.imshow(im)
        return fig

    # TODO address row should be taller
    def generate_institution_table():
        table_fig = plt.figure(figsize=figsize)
        add_header()
        rows = [
            ('Name', institution.name),
            ('Number of Licenses', institution.number_of_licenses),
            ('Address', institution.address),
            ('Phone Number', institution.phone_number),
        ]
        plt.table(cellText=rows, loc='center')
        plt.axis('off')
        plt.title('Institution Table')
        return table_fig

    # TODO add missing rows
    def generate_data_acquisition_table():
        table_fig = plt.figure(figsize=figsize)
        add_header()
        dataset = datasets[0]
        voxel_dims = voxel_spacing(ijk_to_xyz)
        rows = [
            (r'Phantom filler T$_1$', ''),
            (r'Phantom filler T$_2$', ''),
            ('Phantom filler composition', ''),
            ('Sequence type', dataset.ScanningSequence),
            ('Pixel bandwidth', str(dataset.PixelBandwidth) + r' $\frac{Hz}{px}$'),
            ('Voxel dimensions', ' x '.join(f'{str(round(x, 3))} mm' for x in voxel_dims)),
            ('Sequence repetition time (TR)', f'{dataset.RepetitionTime} ms'),
            ('Echo delay time (TE)', f'{dataset.EchoTime} ms'),
            ('Number of signals averaged (NSA)', dataset.NumberOfAverages),
            ('Data acquisition matrix size', ', '.join([str(i) for i in dataset.AcquisitionMatrix])),
            ('Image matrix size', ''),
            ('Field of view size', ''),
            ('Type of acquisition', dataset.MRAcquisitionType),
            ('Number of slices', len(datasets)),
            ('Slice orientation', ', '.join([str(i) for i in dataset.ImageOrientationPatient])),
            ('Slice position', ', '.join([str(round(i, 3)) for i in dataset.ImagePositionPatient])),
            ('Slice thickness', f'{str(round(voxel_dims[2], 3))} mm'),
            ('Direction of phase encoding', dataset.InPlanePhaseEncodingDirection),
        ]
        plt.table(cellText=rows, loc='center')
        plt.axis('off')
        plt.title('Data Acquisition Table')
        return table_fig

    def generate_scatter_plot():
        scatter_fig = plt.figure(figsize=figsize)
        add_header()
        origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
        distances = np.linalg.norm(TP_A_S.T - origins, axis=1)

        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        plt.plot([0, distances.max()], [threshold, threshold], c='red', linestyle='dashed')
        plt.scatter(distances, error_mags, c=error_mags, cmap=cmap, norm=norm, s=12)
        plt.xlabel('Distance from Isocenter [mm]')
        plt.ylabel('Distortion Magnitude [mm]')
        plt.title('Scatter Plot of Geometric Distortion vs. Distance from Isocenter')
        return scatter_fig

    def generate_spacial_mapping(grid_x, grid_y, gridded):
        contour_fig = plt.figure(figsize=figsize)
        add_header()

        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        contour = plt.contour(grid_x.squeeze(), grid_y.squeeze(), gridded.squeeze(), cmap=cmap, norm=norm)
        plt.clabel(contour, inline=True, fontsize=10)
        return contour_fig

    # TODO .3 mm spacing
    def generate_axial_spacial_mapping():
        # interpolate onto plane at the isocenter to generate contour
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                             np.arange(y_min, y_max, GRID_DENSITY_mm),
                                             [isocenter[2]])
        gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        contour_fig = generate_spacial_mapping(grid_x, grid_y, gridded)
        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')
        plt.title('Axial Contour Plot')
        return contour_fig

    def generate_sagittal_spacial_mapping():
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                             [isocenter[1]],
                                             np.arange(z_min, z_max, GRID_DENSITY_mm), )
        gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        contour_fig = generate_spacial_mapping(grid_x, grid_z, gridded)
        plt.xlabel('x [mm]')
        plt.ylabel('z [mm]')
        plt.title('Sagittal Contour Plot')
        return contour_fig

    def generate_coronal_spacial_mapping():
        grid_x, grid_y, grid_z = np.meshgrid([isocenter[0]],
                                             np.arange(y_min, y_max, GRID_DENSITY_mm),
                                             np.arange(z_min, z_max, GRID_DENSITY_mm))
        gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        contour_fig = generate_spacial_mapping(grid_y, grid_z, gridded)
        plt.xlabel('y [mm]')
        plt.ylabel('z [mm]')
        plt.title('Coronal Contour Plot')
        return contour_fig

    def generate_axial_spacial_mapping_series():
        figs = []

        for z in np.arange(z_min, z_max, CONTOUR_SERIES_STEP_mm):
            grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                                 np.arange(y_min, y_max, GRID_DENSITY_mm),
                                                 np.array([z]))
            gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')

            try:
                contour_fig = generate_spacial_mapping(grid_x, grid_y, gridded)
                plt.xlabel('x [mm]')
                plt.ylabel('y [mm]')
                plt.title(f'Axial Contour Plot Series (z = {round(z, 3)} mm)')
                figs.append(contour_fig)
            except ValueError:
                pass
        return figs

    def generate_error_table():
        table_fig = plt.figure(figsize=figsize)
        add_header()
        rows = []

        # interpolate onto spheres of increasing size to calculate average and max error table
        interpolator = LinearNDInterpolator(TP_A_S.T, error_mags.T)
        radius2max_mean_error = OrderedDict()

        origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
        distances = np.linalg.norm(TP_A_S.T - origins, axis=1)
        step = max(distances.max() // 20, SPHERE_STEP_mm)

        r = step
        while True:
            num_points = int(round(surface_area(r) / SPHERE_POINTS_PER_AREA))
            equidistant_sphere_points = generate_equidistant_sphere(num_points) * r + np.array(isocenter)
            values = interpolator(equidistant_sphere_points)
            values = values[~np.isnan(values)]
            if values.size == 0:
                break
            else:
                max_value, mean_value = np.max(values), np.mean(values)
                radius2max_mean_error[r] = (max_value, mean_value)
                r += step

        for r, (max_value, mean_value) in radius2max_mean_error.items():
            rows.append((r, np.round(max_value, 3), np.round(mean_value, 3)))

        plt.table(cellText=rows, colLabels=['Distance from Isocenter [mm]', 'Maximum Error [mm]', 'Average Error [mm]'],
                  loc='center')
        plt.axis('off')
        plt.title('Error Table')
        return table_fig

    def generate_roi_view(plt, im, x_bounds, y_bounds, A_S_2D, B_2D):
        plt.imshow(im, cmap='Greys', extent=[*x_bounds, *y_bounds], aspect='auto')
        plt.scatter([A_S_2D[0]], [A_S_2D[1]], c='gold')
        plt.scatter([B_2D[0]], [B_2D[1]], c='C0')
        plt.set_xticks([])
        plt.set_yticks([])
        plt.set_xlim(x_bounds)
        plt.set_ylim(y_bounds)

    def generate_roi_table(plt, A_S, B, error_vec, error_mag):
        rows = (
            ('A_S [mm]', f'({str(round(A_S[0], 3))}, {str(round(A_S[1], 3))}, {str(round(A_S[2], 3))})'),
            ('B [mm]', f'({str(round(B[0], 3))}, {str(round(B[1], 3))}, {str(round(B[2], 3))})'),
            ('x [mm]', f'{str(round(error_vec[0], 3))}'),
            ('y [mm]', f'{str(round(error_vec[1], 3))}'),
            ('z [mm]', f'{str(round(error_vec[2], 3))}'),
            ('magnitude [mm]', f'{str(round(error_mag, 3))}'),
        )
        colors = (
            ('gold', 'w'),
            ('C0', 'w'),
            ('w', 'w'),
            ('w', 'w'),
            ('w', 'w'),
            ('w', 'w'),
        )
        plt.table(cellText=rows, cellColours=colors, loc='center')
        plt.axis('off')

    def generate_fiducial_rois():
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        sort_indices = np.argsort(error_mags.T)[::-1]
        rois = zip(TP_A_S.T[sort_indices], TP_B.T[sort_indices], error_vecs.T[sort_indices], error_mags.T[sort_indices])

        figs = []
        for chunk in chunks(list(rois), 6):
            roi_fig = plt.figure(figsize=figsize)
            add_header()
            subplot_dim = (6, 5)
            plt.suptitle('Fiducial ROIs')
            plt.axis('off')

            # TODO (x, y, z) coordinates should be in the center of the pixels
            for i, (A_S, B, error_vec, error_mag) in enumerate(chunk):
                B_ijk = apply_affine(xyz_to_ijk, np.array([B]).T).T.squeeze()
                shape = roi_shape(grid_radius, voxel_spacing(ijk_to_xyz))
                bounds = roi_bounds(B, shape)
                bounds_ijk = roi_bounds(B_ijk, shape)
                axial, sagittal, coronal = roi_images(B_ijk, voxels, bounds_ijk)

                # plt.rcParams['xtick.labelsize'] = 4
                # plt.rcParams['ytick.labelsize'] = 4

                plt1 = plt.subplot2grid(subplot_dim, (i, 0))
                generate_roi_view(plt1, axial, bounds[0], bounds[1], (A_S[0], A_S[1]), (B[0], B[1]))

                plt2 = plt.subplot2grid(subplot_dim, (i, 1))
                generate_roi_view(plt2, sagittal, bounds[0], bounds[2], (A_S[0], A_S[2]), (B[0], B[2]))

                plt3 = plt.subplot2grid(subplot_dim, (i, 2))
                generate_roi_view(plt3, coronal, bounds[1], bounds[2], (A_S[1], A_S[2]), (B[1], B[2]))

                plt4 = plt.subplot2grid(subplot_dim, (i, 3), colspan=2)
                generate_roi_table(plt4, A_S, B, error_vec, error_mag)

            figs.append(roi_fig)
        return figs

    def generate_points():
        points_fig = scatter3({'A_S': TP_A_S, 'B': TP_B}, figsize=figsize)
        add_header()
        return points_fig

    def generate_quiver():
        quiver_fig = plt.figure(figsize=figsize)
        add_header()
        ax = quiver_fig.add_subplot(111, projection='3d')
        ax.quiver(*TP_A_S, *error_vecs)
        return quiver_fig

    cover_page = generate_cover_page()
    institution_table = generate_institution_table()
    data_acquisition_table = generate_data_acquisition_table()
    scatter_plot = generate_scatter_plot()
    axial_spacial_mapping = generate_axial_spacial_mapping()
    sagittal_spacial_mapping = generate_sagittal_spacial_mapping()
    coronal_spacial_mapping = generate_coronal_spacial_mapping()
    axial_spacial_mapping_series = generate_axial_spacial_mapping_series()
    error_table = generate_error_table()
    fiducial_rois = generate_fiducial_rois()
    points = generate_points()

    # TODO write PDF in memory
    with PdfPages(full_report_path) as pdf:
        save_then_close_figure(pdf, cover_page)
        save_then_close_figure(pdf, institution_table)
        save_then_close_figure(pdf, data_acquisition_table)

        save_then_close_figure(pdf, scatter_plot)

        save_then_close_figure(pdf, axial_spacial_mapping)
        save_then_close_figure(pdf, sagittal_spacial_mapping)
        save_then_close_figure(pdf, coronal_spacial_mapping)
        for fig in axial_spacial_mapping_series:
            save_then_close_figure(pdf, fig)

        save_then_close_figure(pdf, error_table)

        for fig in fiducial_rois:
            save_then_close_figure(pdf, fig)

        save_then_close_figure(pdf, points)

    with PdfPages(executive_report_path) as pdf:
        save_then_close_figure(pdf, cover_page)
        save_then_close_figure(pdf, institution_table)
        save_then_close_figure(pdf, data_acquisition_table)

        save_then_close_figure(pdf, scatter_plot)

        save_then_close_figure(pdf, axial_spacial_mapping)
        save_then_close_figure(pdf, sagittal_spacial_mapping)
        save_then_close_figure(pdf, coronal_spacial_mapping)

        save_then_close_figure(pdf, error_table)

        save_then_close_figure(pdf, points)


def save_then_close_figure(pdf, figure):
    pdf.savefig(figure)
    plt.close(figure)


def generate_cube(size, spacing=1, x0=0):
    points = []
    for x in range(-size, size):
        for y in range(-size, size):
            for z in range(-size, size):
                points.append((float(x) * spacing, float(y) * spacing, float(z) * spacing))
    return np.array(points).T


if __name__ == '__main__':
    A = generate_cube(2, 4)
    B = generate_cube(2, 4)
    affine_matrix = affine.translation_rotation(0, 0, 0, np.pi / 180 * 10, np.pi / 180 * 10, np.pi / 180 * 10)

    A = apply_affine(affine_matrix, A)

    with zipfile.ZipFile('data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip') as zip_file:
        datasets = dicom_import.dicom_datasets_from_zip(zip_file)

    voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)

    class Institution:
        name = "Johns Hopkins"
        number_of_licenses = 12
        address = "3101 Wyman Park Dr.\nBaltimore, MD 21211"
        phone_number = "555-555-5555"

    generate_reports(A, B, datasets, voxels, ijk_to_xyz, '603A', 2.5, Institution, 'tmp/full_report.pdf', 'tmp/executive_report.pdf')
