import os
import zipfile
import math
from collections import OrderedDict
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from django.conf import settings
from matplotlib import colors
from matplotlib import gridspec
from matplotlib import rc
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from scipy.interpolate.interpnd import LinearNDInterpolator
from scipy.interpolate.ndgriddata import griddata
from mpl_toolkits.mplot3d import Axes3D  # import has needed side effect

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


def generate_reports(TP_A_S, TP_B, datasets, voxels, ijk_to_xyz, phantom_model_number, threshold, institution, machine_name, sequence_name, phantom_name, acquisition_date, full_report_path, executive_report_path):
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

    def generate_page(content, report_text, get_page):
        fig = plt.figure(figsize=figsize)
        plt.axis('off')

        gs = gridspec.GridSpec(3, 1, height_ratios=[1, 20, 1])

        ax0 = plt.subplot(gs[0])
        plt.axis('off')
        ax0.add_patch(patches.Rectangle((0, 0), 1, 1))
        im = mpimg.imread(os.path.join(settings.BASE_DIR, 'client/src/base/logo_header.png'))
        im_width = 0.1
        im_height = im_width * 210 / 807
        x_bounds = [0, im_width]
        y_bounds = [0, im_height]
        # ax0.imshow(im, extent=[*x_bounds, *y_bounds])
        ax0.text(0.02, 0.46, "CIRS Distortion Check", weight='bold', color='w', va='center', size=18)
        ax0.text(0.98, 0.46, report_text, weight='bold', color='w', va='center', ha='right', size=18)

        # TODO figure out better way to add padding
        gs_inner = gridspec.GridSpecFromSubplotSpec(3, 3, width_ratios=[1, 20, 1], height_ratios=[1, 20, 1], subplot_spec=gs[1])
        ax_inner = plt.subplot(gs_inner[1, 1])
        content(ax_inner, gs_inner[1, 1])

        ax2 = plt.subplot(gs[2])
        plt.axis('off')
        ax2.add_patch(patches.Rectangle((0, 0), 1, 1))
        ax2.text(0.02, 0.46, f"{machine_name} / {sequence_name} / {acquisition_date.strftime('%B %-d, %Y')}", weight='bold', color='w', va='center', size=14)
        ax2.text(0.98, 0.46, f"Page {next(get_page)}", weight='bold', color='w', va='center', ha='right', size=14)

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        return fig

    def generate_cover_page(report_text):
        fig = plt.figure(figsize=figsize)
        plt.axis('off')

        gs = gridspec.GridSpec(3, 1, height_ratios=[1, 10, 11])

        ax0 = plt.subplot(gs[0])
        plt.axis('off')
        ax0.add_patch(patches.Rectangle((0, 0), 1, 1))

        ax1 = plt.subplot(gs[1])
        ax1.set_xlim([0, 1])
        ax1.set_ylim([0, 1])
        plt.axis('off')
        im = mpimg.imread(os.path.join(settings.BASE_DIR, 'client/src/login/logo.png'))
        im_width = 0.7
        im_height = im_width * 499 / 1275
        center = (0.5, 0.7)
        x_bounds = [center[0] - im_width / 2, center[0] + im_width / 2]
        y_bounds = [center[1] - im_height / 2, center[1] + im_height / 2]
        ax1.imshow(im, extent=[*x_bounds, *y_bounds])
        color = (0, 95, 152)
        color = tuple(c / 255 for c in color)
        ax1.text(0.5, 0.2, report_text, size=24, ha='center', weight='bold', color=color)

        ax2 = plt.subplot(gs[2])
        plt.axis('off')
        ax2.add_patch(patches.Rectangle((0, 0), 1, 1))
        # rc('text', usetex=True)
        ax2.text(0.1, 0.2, r"Machine: " + machine_name +
                 "\n" + r"Sequence: " + sequence_name +
                 "\n" + r"Phantom: " + f"{phantom_name} - {phantom_model_number}" +
                 "\n" + r"Scan Acquired On: " + acquisition_date.strftime("%B %-d, %Y"), size=16, color='w')

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        return fig

    def generate_institution_table(ax, cell):
        rows = [
            ('Name', institution.name),
            ('Number of Licenses', institution.number_of_licenses),
            ('Address', institution.address),
            ('Phone Number', institution.phone_number),
        ]
        table = ax.table(cellText=rows, loc='center')
        table_props = table.properties()
        table_cells = table_props['child_artists']

        # TODO auto-determine height based on text height?
        for i, cell in enumerate(table_cells):
            if i in (4, 5):
                cell.set_height(0.075)
            else:
                cell.set_height(0.05)

        ax.axis('off')
        ax.set_title('Institution Table')

    # TODO add missing rows
    def generate_data_acquisition_table(ax, cell):
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
        table = ax.table(cellText=rows, loc='center')
        table_props = table.properties()
        table_cells = table_props['child_artists']
        for i, cell in enumerate(table_cells):
            cell.set_height(0.05)
        ax.axis('off')
        ax.set_title('Data Acquisition Table')

    def generate_scatter_plot(ax, cell):
        origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
        distances = np.linalg.norm(TP_A_S.T - origins, axis=1)

        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        ax.plot([0, distances.max()], [threshold, threshold], c='red', linestyle='dashed')
        ax.scatter(distances, error_mags, c=error_mags, cmap=cmap, norm=norm, s=12)
        ax.set_xlabel('Distance from Isocenter [mm]')
        ax.set_ylabel('Distortion Magnitude [mm]')
        ax.set_title('Scatter Plot of Geometric Distortion vs. Distance from Isocenter')

    def generate_spacial_mapping(ax, grid_x, grid_y, gridded):
        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        levels = np.arange(0, error_mags.T.max() + 0.3, 0.3)
        contour = plt.contour(grid_x.squeeze(), grid_y.squeeze(), gridded.squeeze(), cmap=cmap, norm=norm, levels=levels)
        ax.clabel(contour, inline=True, fontsize=10)

    def generate_axial_spacial_mapping(ax, cell):
        # interpolate onto plane at the isocenter to generate contour
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                             np.arange(y_min, y_max, GRID_DENSITY_mm),
                                             [isocenter[2]])
        gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        generate_spacial_mapping(ax, grid_x, grid_y, gridded)
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')
        ax.set_title('Axial Contour Plot')

    def generate_sagittal_spacial_mapping(ax, cell):
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                             [isocenter[1]],
                                             np.arange(z_min, z_max, GRID_DENSITY_mm), )
        gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        generate_spacial_mapping(ax, grid_x, grid_z, gridded)
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('z [mm]')
        ax.set_title('Sagittal Contour Plot')

    def generate_coronal_spacial_mapping(ax, cell):
        grid_x, grid_y, grid_z = np.meshgrid([isocenter[0]],
                                             np.arange(y_min, y_max, GRID_DENSITY_mm),
                                             np.arange(z_min, z_max, GRID_DENSITY_mm))
        gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        generate_spacial_mapping(ax, grid_y, grid_z, gridded)
        ax.set_xlabel('y [mm]')
        ax.set_ylabel('z [mm]')
        ax.set_title('Coronal Contour Plot')

    def generate_axial_spacial_mapping_series(report_text, get_page):
        pages = []

        for z in np.arange(z_min, z_max, CONTOUR_SERIES_STEP_mm):
            grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                                 np.arange(y_min, y_max, GRID_DENSITY_mm),
                                                 np.array([z]))
            gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')

            try:
                def generate_axial_spacial_mapping_slice(ax, cell):
                    generate_spacial_mapping(ax, grid_x, grid_y, gridded)
                    ax.set_xlabel('x [mm]')
                    ax.set_ylabel('y [mm]')
                    ax.set_title(f'Axial Contour Plot Series (z = {round(z, 3)} mm)')
                pages.append(generate_page(generate_axial_spacial_mapping_slice, report_text, get_page))
            except ValueError:
                pass
        return pages

    def generate_error_table(ax, cell):
        rows = []

        # interpolate onto spheres of increasing size to calculate average and max error table
        interpolator = LinearNDInterpolator(TP_A_S.T, error_mags.T)
        radius2max_mean_error = OrderedDict()

        origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
        distances = np.linalg.norm(TP_A_S.T - origins, axis=1)
        step = max(math.ceil(distances.max() / 20), SPHERE_STEP_mm)

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

        table = ax.table(
            cellText=rows,
            colLabels=['Distance from Isocenter [mm]', 'Maximum Error [mm]', 'Average Error [mm]'],
            loc='center',
        )
        table_props = table.properties()
        table_cells = table_props['child_artists']
        for i, cell in enumerate(table_cells):
            cell.set_height(0.05)
        ax.axis('off')
        ax.set_title('Error Table')

    def generate_roi_view(ax, im, x_bounds, y_bounds, A_S_2D, B_2D):
        x_bounds = tuple(b - 0.5 for b in x_bounds)
        y_bounds = tuple(b - 0.5 for b in y_bounds)
        ax.imshow(im.T, cmap='Greys', extent=[*x_bounds, *y_bounds], aspect='auto', origin='lower')
        ax.scatter([A_S_2D[0]], [A_S_2D[1]], c='coral')
        ax.scatter([B_2D[0]], [B_2D[1]], c='skyblue')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(x_bounds)
        ax.set_ylim(y_bounds)

    def generate_roi_table(ax, A_S, B, error_vec, error_mag):
        rows = (
            ('actual [mm]', f'({str(round(A_S[0], 3))}, {str(round(A_S[1], 3))}, {str(round(A_S[2], 3))})'),
            ('detected [mm]', f'({str(round(B[0], 3))}, {str(round(B[1], 3))}, {str(round(B[2], 3))})'),
            ('x [mm]', f'{str(round(error_vec[0], 3))}'),
            ('y [mm]', f'{str(round(error_vec[1], 3))}'),
            ('z [mm]', f'{str(round(error_vec[2], 3))}'),
            ('magnitude [mm]', f'{str(round(error_mag, 3))}'),
        )
        colors = (
            ('coral', 'w'),
            ('skyblue', 'w'),
            ('w', 'w'),
            ('w', 'w'),
            ('w', 'w'),
            ('w', 'w'),
        )
        ax.table(cellText=rows, cellColours=colors, loc='center')
        ax.axis('off')

    def generate_fiducial_rois(report_text, get_page):
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        sort_indices = np.argsort(error_mags.T)[::-1]
        rois = zip(TP_A_S.T[sort_indices], TP_B.T[sort_indices], error_vecs.T[sort_indices], error_mags.T[sort_indices])

        pages = []
        for chunk in chunks(list(rois), 5):
            def generate_fiducial_roi_page(ax, cell):
                ax.set_title('Fiducial ROIs')
                ax.axis('off')

                gs = gridspec.GridSpecFromSubplotSpec(5, 4, width_ratios=[1, 1, 1, 2], subplot_spec=cell)

                for i, (A_S, B, error_vec, error_mag) in enumerate(chunk):
                    B_ijk = apply_affine(xyz_to_ijk, np.array([B]).T).T.squeeze()
                    shape = roi_shape(grid_radius, voxel_spacing(ijk_to_xyz))
                    bounds = roi_bounds(B, shape)
                    bounds_ijk = roi_bounds(B_ijk, shape)
                    axial, sagittal, coronal = roi_images(B_ijk, voxels, bounds_ijk)

                    ax0 = plt.subplot(gs[i, 0])
                    generate_roi_view(ax0, axial, bounds[0], bounds[1], (A_S[0], A_S[1]), (B[0], B[1]))

                    ax1 = plt.subplot(gs[i, 1])
                    generate_roi_view(ax1, sagittal, bounds[0], bounds[2], (A_S[0], A_S[2]), (B[0], B[2]))

                    ax2 = plt.subplot(gs[i, 2])
                    generate_roi_view(ax2, coronal, bounds[1], bounds[2], (A_S[1], A_S[2]), (B[1], B[2]))

                    ax3 = plt.subplot(gs[i, 3])
                    generate_roi_table(ax3, A_S, B, error_vec, error_mag)

            pages.append(generate_page(generate_fiducial_roi_page, report_text, get_page))
        return pages

    def generate_points(ax, cell):
        gs = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=cell)
        ax_inner = plt.subplot(gs[0], projection='3d')
        points_fig = scatter3({'Actual': TP_A_S, 'Detected': TP_B}, ax_inner)
        return points_fig

    def generate_quiver():
        quiver_fig = plt.figure()
        ax = quiver_fig.add_subplot(111, projection='3d')
        ax.quiver(*TP_A_S, *error_vecs)
        return quiver_fig

    def page_generator():
        i = 0
        while True:
            i += 1
            yield i

    # TODO write PDF in memory
    with PdfPages(full_report_path) as pdf:
        report_text = "Full Report"
        get_page = page_generator()
        save_then_close_figure(pdf, generate_cover_page("FULL REPORT"))
        save_then_close_figure(pdf, generate_page(generate_institution_table, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_data_acquisition_table, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_scatter_plot, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_axial_spacial_mapping, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_sagittal_spacial_mapping, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_coronal_spacial_mapping, report_text, get_page))
        for fig in generate_axial_spacial_mapping_series(report_text, get_page):
            save_then_close_figure(pdf, fig)
        save_then_close_figure(pdf, generate_page(generate_error_table, report_text, get_page))
        for fig in generate_fiducial_rois(report_text, get_page):
            save_then_close_figure(pdf, fig)
        save_then_close_figure(pdf, generate_page(generate_points, report_text, get_page))

    with PdfPages(executive_report_path) as pdf:
        report_text = "Executive Report"
        get_page = page_generator()
        save_then_close_figure(pdf, generate_cover_page("EXECUTIVE REPORT"))
        save_then_close_figure(pdf, generate_page(generate_institution_table, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_data_acquisition_table, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_scatter_plot, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_axial_spacial_mapping, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_sagittal_spacial_mapping, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_coronal_spacial_mapping, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_error_table, report_text, get_page))
        save_then_close_figure(pdf, generate_page(generate_points, report_text, get_page))


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

    generate_reports(A, B, datasets, voxels, ijk_to_xyz, '603A', 2.5, Institution, 'Machine A', 'Sequence A', 'Phantom A', datetime.now(), 'tmp/full_report.pdf', 'tmp/executive_report.pdf')
