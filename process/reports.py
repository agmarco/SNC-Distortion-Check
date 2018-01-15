import os
import zipfile
import math
from collections import OrderedDict
from datetime import datetime
import logging
from textwrap import wrap
from functools import partial
import itertools
import numbers

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from django.conf import settings
from matplotlib import colors
from matplotlib import gridspec
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from scipy.interpolate.interpnd import LinearNDInterpolator
from scipy.interpolate.ndgriddata import griddata
from mpl_toolkits.mplot3d import Axes3D  # import has needed side effect
import scipy.ndimage.filters

from process import affine, phantoms
from process.affine import apply_affine, voxel_spacing, apply_affine_1
from process.visualization import scatter3
from process.utils import chunks, fov_center_xyz
from process import dicom_import


logger = logging.getLogger(__name__)


GRID_DENSITY_mm = 2.0
ROI_UPSCALE_FACTOR = 8


def surface_area(r):
    return 4*np.pi*r*r


def roi_shape(grid_radius, voxel_spacing):
    return tuple(math.ceil(grid_radius / dim * ROI_UPSCALE_FACTOR) for dim in voxel_spacing)


def roi_bounds(center, shape):
    return tuple((
        int(math.ceil(a - b / 2)),
        int(math.ceil(a + b / 2)),
    ) for a, b in zip(center, shape))


def fill_image(image, voxels_shape, bounds_list):
    """Fill the image with black borders if necessary."""

    bounds_a, bounds_b = [bounds for bounds in bounds_list if type(bounds) != int]
    max_a, max_b = tuple(n for i, n in enumerate(voxels_shape) if type(bounds_list[i]) != int)

    if bounds_a[0] < 0:
        border = np.full((0 - bounds_a[0], image.shape[1]), np.nan, dtype=float)
        image = np.vstack((border, image))

    if bounds_a[1] > max_a:
        border = np.full((bounds_a[1] - max_a, image.shape[1]), np.nan, dtype=float)
        image = np.vstack((image, border))

    if bounds_b[0] < 0:
        border = np.full((image.shape[0], 0 - bounds_b[0]), np.nan, dtype=float)
        image = np.hstack((border, image))

    if bounds_b[1] > max_b:
        border = np.full((image.shape[0], bounds_b[1] - max_b), np.nan, dtype=float)
        image = np.hstack((image, border))

    return image


def roi_image(voxels, bounds_list):
    adjusted_bounds_list = []
    for i, bounds in enumerate(bounds_list):
        if type(bounds) == int:
            adjusted_bounds_list.append(bounds)
        else:
            start, end = bounds
            adjusted_bounds_list.append((max(start, 0), min(end, voxels.shape[i])))

    slices = tuple(bounds if type(bounds) == int else slice(*bounds) for bounds in adjusted_bounds_list)
    image = voxels[slices]
    return fill_image(image, voxels.shape, bounds_list)


def roi_images(b, voxels, bounds_list):
    return (
        roi_image(voxels, (bounds_list[0], bounds_list[1], int(round(b[2])))),
        roi_image(voxels, (bounds_list[0], int(round(b[1])), bounds_list[2])),
        roi_image(voxels, (int(round(b[0])), bounds_list[1], bounds_list[2])),
    )


def error_table_data(distances, error_mags, step):
    assert len(distances) == len(error_mags)
    assert not any(np.isnan(error_mags))

    rows = []

    band_outer_radius = step
    num_total_points = len(distances)
    num_reported_points = 0
    while num_reported_points < num_total_points:
        band_inner_radius = band_outer_radius - step
        band_indices = np.where(
                (band_inner_radius <= distances) & \
                (distances < band_outer_radius))

        band_values = error_mags[band_indices]
        num_points_in_band = len(band_values)

        rows.append((
            str(band_outer_radius),
            "{:.3f}".format(np.max(band_values)) if num_points_in_band else "-",
            "{:.3f}".format(np.mean(band_values)) if num_points_in_band else "-",
            str(num_points_in_band),
        ))

        band_outer_radius += step
        num_reported_points += num_points_in_band
    return rows


# TODO: refactor this somehow, so it doesn't require so many arguments
def generate_reports(TP_A_S, TP_B, datasets, voxels, ijk_to_xyz, phantom_model, threshold,
            institution, machine_name, sequence_name, phantom_name, acquisition_date,
            full_report_path, executive_report_path):
    """
    Given the set of matched and registered points, generate a NEMA report.

    Assumes that each column of TP_A_S is matched with the corresponding column
    of TP_B.
    """
    logger.info("begining report generation")

    assert TP_A_S.shape == TP_B.shape

    error_vecs = TP_A_S - TP_B
    error_mags = np.linalg.norm(error_vecs, axis=0).squeeze()

    x_min, y_min, z_min = np.min(TP_A_S, axis=1)
    x_max, y_max, z_max = np.max(TP_A_S, axis=1)

    grid_radius = phantoms.paramaters[phantom_model]['grid_radius']
    fig_width = 8.5
    fig_height = 11
    figsize = (fig_width, fig_height)

    isocenter = fov_center_xyz(voxels.shape, ijk_to_xyz)
    origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
    distances = np.linalg.norm(TP_A_S.T - origins, axis=1)

    brand_color = (0, 95, 152)
    brand_color = tuple(c / 255 for c in brand_color)

    num_roi_chunks = 4
    num_error_table_rows = 16

    def create_page(pdf, report_title, get_page, draw):
        fig = plt.figure(figsize=figsize)
        plt.axis('off')

        gs_ratios = [1, 20, 1]
        gs = gridspec.GridSpec(3, 1, height_ratios=gs_ratios)

        ax0_width = fig_width * (sum(gs_ratios) + 3) / fig_height

        ax0 = plt.subplot(gs[0])
        plt.axis('off')
        ax0.set_xlim([0, ax0_width])
        ax0.set_ylim([0, 1])
        ax0.add_patch(patches.Rectangle((0, 0), ax0_width, 1, color=brand_color, zorder=0))

        im = mpimg.imread(os.path.join(settings.BASE_DIR, 'client/src/base/logo_header.png'))
        im_height = 0.5
        im_width = im_height * 807 / 210
        margin = (1 - im_height) / 2
        x_bounds = [margin, im_width + margin]
        y_bounds = [margin, im_height + margin]
        ax0.imshow(im, extent=[*x_bounds, *y_bounds], zorder=1)

        # TODO swap out logo with SVG containing "CIRS Distortion Check"
        ax0.text(2.4, 0.46, "Distortion Check", weight='bold', color='w', va='center', size=18)
        ax0.text(0.98 * ax0_width, 0.46, report_title, weight='bold', color='w', va='center', ha='right', size=18)

        # TODO figure out better way to add padding
        gs_inner = gridspec.GridSpecFromSubplotSpec(3, 3,
                                                    width_ratios=[1, 20, 1],
                                                    height_ratios=[1, 20, 1],
                                                    subplot_spec=gs[1])
        ax_inner = plt.subplot(gs_inner[1, 1])
        draw(ax_inner, gs_inner[1, 1])

        ax2 = plt.subplot(gs[2])
        plt.axis('off')
        ax2.add_patch(patches.Rectangle((0, 0), 1, 1, color=brand_color))
        t = f"{machine_name} / {sequence_name} / {acquisition_date.strftime('%B %-d, %Y')}"
        ax2.text(0.02, 0.46, t, weight='bold', color='w', va='center', size=12)
        ax2.text(0.98, 0.46, f"Page {next(get_page)}", weight='bold', color='w', va='center', ha='right', size=12)

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        save_then_close_figure(pdf, fig)

    def create_cover_page(pdf, report_title):
        fig = plt.figure(figsize=figsize)
        plt.axis('off')

        gs = gridspec.GridSpec(3, 1, height_ratios=[1, 10, 11])

        ax0 = plt.subplot(gs[0])
        plt.axis('off')
        ax0.add_patch(patches.Rectangle((0, 0), 1, 1, color=brand_color))

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

        ax1.text(0.5, 0.2, report_title, size=24, ha='center', weight='bold', color=brand_color)

        ax2 = plt.subplot(gs[2])
        plt.axis('off')
        ax2.add_patch(patches.Rectangle((0, 0), 1, 1, color=brand_color))
        ax2.text(0.1, 0.2, r"Machine: " + machine_name +
                 "\n" + r"Sequence: " + sequence_name +
                 "\n" + r"Phantom: " + f"{phantom_name} - {phantom_model}" +
                 "\n" + r"Scan Acquired On: " + acquisition_date.strftime("%B %-d, %Y"), size=16, color='w')

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        save_then_close_figure(pdf, fig)

    def draw_institution_table(ax, cell):
        rows = [
            ('Name', institution.name),
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
    def draw_data_acquisition_table(ax, cell):
        dataset = datasets[0]
        voxel_dims = voxel_spacing(ijk_to_xyz)

        if hasattr(dataset, 'AcquisitionMatrix'):
            a, b = dataset.AcquisitionMatrix[:2], dataset.AcquisitionMatrix[2:]
            if all(x == 0 for x in a) or all(x != 0 for x in a):
                raise ValueError("The first 2 numbers in the AcquisitionMatrix must contain one zero and one non-zero value.")
            if all(x == 0 for x in b) or all(x != 0 for x in b):
                raise ValueError("The second 2 numbers in the AcquisitionMatrix must contain one zero and one non-zero value.")
            data_acquisition_matrix_size = f'{max(a)} x {max(b)}'
        else:
            data_acquisition_matrix_size = 'unknown'

        rows = [
            # TODO: add this back along with any necessary web-ui forms
            # (r'Phantom filler T$_1$', ''),
            # (r'Phantom filler T$_2$', ''),
            # ('Phantom filler composition', ''),
            ('Sequence type', getattr(dataset, 'ScanningSequence', 'unknown')),
            ('Pixel bandwidth', str(dataset.PixelBandwidth) + r' $\frac{Hz}{px}$' if hasattr(dataset, 'PixelBandwidth') else 'unknown'),
            ('Voxel dimensions', ' x '.join(f'{x:.3f} mm' for x in voxel_dims)),
            ('Sequence repetition time (TR)', f'{dataset.RepetitionTime} ms' if hasattr(dataset, 'RepetitionTime') else 'unknown'),
            ('Echo delay time (TE)', f'{dataset.EchoTime} ms' if hasattr(dataset, 'EchoTime') else 'unknown'),
            ('Number of signals averaged (NSA)', getattr(dataset, 'NumberOfAverages', 'unknown')),
            ('Data acquisition matrix size', data_acquisition_matrix_size),
            ('Image matrix size', ' x '.join([str(n) for n in voxels.shape[:2]])),
            ('Field of view size', ' x '.join([f'{n * x:.1f} mm' for n, x in zip(voxels.shape, voxel_dims)])),
            ('Type of acquisition', getattr(dataset, 'MRAcquisitionType', 'unknown')),
            ('Number of slices', len(datasets)),
            ('Slice orientation', ', '.join([f'{i:.3f}' for i in dataset.ImageOrientationPatient])),
            ('Slice position', ', '.join([f'{i:.3f} mm' for i in dataset.ImagePositionPatient])),
            ('Slice thickness', f'{voxel_dims[2]:.3f} mm'),
            ('Direction of phase encoding', getattr(dataset, 'InPlanePhaseEncodingDirection', 'unknown')),
        ]
        table = ax.table(cellText=rows, loc='center')
        table_props = table.properties()
        table_cells = table_props['child_artists']
        for i, cell in enumerate(table_cells):
            cell.set_height(0.05)
        ax.axis('off')
        ax.set_title('Data Acquisition Table')

    def draw_phantom_description(ax, cell):
        ax.set_title('Phantom Description')
        ax.axis('off')
        desc = phantoms.paramaters[phantom_model]['description']
        t = "\n\n".join("\n".join(wrap(p, 95)) for p in desc.split("\n"))
        ax.text(0, 0.5, t)

    def draw_scatter_plot(ax, cell):
        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        ax.plot([0, distances.max()], [threshold, threshold], c='red', linestyle='dashed')
        ax.scatter(distances, error_mags, c=error_mags, cmap=cmap, norm=norm, s=12)
        ax.set_xlabel('Distance from Isocenter [mm]')
        ax.set_ylabel('Distortion Magnitude [mm]')
        ax.set_title('Scatter Plot of Geometric Distortion vs. Distance from Isocenter')

    def draw_spacial_mapping(grid_a, grid_b, gridded, ax):
        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        levels = np.arange(0, error_mags.max() + 0.3, 0.3)
        contour = plt.contour(grid_a.squeeze(), grid_b.squeeze(), gridded.squeeze(), cmap=cmap, norm=norm, levels=levels)
        ax.clabel(contour, inline=True, fontsize=10)

    def axial_spatial_mapping_data():
        # interpolate onto plane at the isocenter to generate contour
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                             np.arange(y_min, y_max, GRID_DENSITY_mm),
                                             [isocenter[2]])
        gridded = griddata(TP_A_S.T, error_mags, (grid_x, grid_y, grid_z), method='linear')
        gridded = scipy.ndimage.filters.gaussian_filter(gridded, 2, truncate=2)
        return grid_x, grid_y, gridded

    def draw_axial_spatial_mapping(grid_a, grid_b, gridded, ax, cell):
        draw_spacial_mapping(grid_a, grid_b, gridded, ax)
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')
        ax.set_title('Axial Contour Plot')

    def sagittal_spatial_mapping_data():
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                             [isocenter[1]],
                                             np.arange(z_min, z_max, GRID_DENSITY_mm), )
        gridded = griddata(TP_A_S.T, error_mags, (grid_x, grid_y, grid_z), method='linear')
        gridded = scipy.ndimage.filters.gaussian_filter(gridded, 2, truncate=2)
        return grid_x, grid_z, gridded

    def draw_sagittal_spatial_mapping(grid_a, grid_b, gridded, ax, cell):
        draw_spacial_mapping(grid_a, grid_b, gridded, ax)
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('z [mm]')
        ax.set_title('Sagittal Contour Plot')

    def coronal_spatial_mapping_data():
        grid_x, grid_y, grid_z = np.meshgrid([isocenter[0]],
                                             np.arange(y_min, y_max, GRID_DENSITY_mm),
                                             np.arange(z_min, z_max, GRID_DENSITY_mm))
        gridded = griddata(TP_A_S.T, error_mags, (grid_x, grid_y, grid_z), method='linear')
        gridded = scipy.ndimage.filters.gaussian_filter(gridded, 2, truncate=2)
        return grid_y, grid_z, gridded

    def draw_coronal_spatial_mapping(grid_a, grid_b, gridded, ax, cell):
        draw_spacial_mapping(grid_a, grid_b, gridded, ax)
        ax.set_xlabel('y [mm]')
        ax.set_ylabel('z [mm]')
        ax.set_title('Coronal Contour Plot')

    def draw_error_table(rows, ax, cell):
        table = ax.table(
            cellText=rows,
            colLabels=[
                "Outer Radius of\nSpherical Band [mm]",
                "Maximum Error [mm]",
                "Average Error [mm]",
                "Number of Control\nPoints within Band",
            ],
            loc='center',
        )
        table_props = table.properties()
        table_cells = table_props['child_artists']
        for cell in table_cells:
            cell.set_height(0.05)
        ax.axis('off')
        ax.set_title('Error Table')

    def generate_roi_view(ax, im, x_bounds, y_bounds, a_S_2D, b_2D, vmin, vmax):
        x_bounds = tuple(b - 0.5 for b in x_bounds)
        y_bounds = tuple(b - 0.5 for b in y_bounds)
        ax.imshow(im.T, cmap='Greys', extent=[*x_bounds, *y_bounds], aspect='auto', origin='lower', vmin=vmin, vmax=vmax)
        ax.scatter([a_S_2D[0]], [a_S_2D[1]], c='coral')
        ax.scatter([b_2D[0]], [b_2D[1]], c='skyblue')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(x_bounds)
        ax.set_ylim(y_bounds)

    def generate_roi_table(ax, A_S, B, error_vec, error_mag):
        rows = (
            ('actual [mm]', ', '.join(str(round(a, 3)) for a in A_S)),
            ('detected [mm]', ', '.join(str(round(b, 3)) for b in B)),
            ('x [mm]', str(round(error_vec[0], 3))),
            ('y [mm]', str(round(error_vec[1], 3))),
            ('z [mm]', str(round(error_vec[2], 3))),
            ('magnitude [mm]', str(round(error_mag, 3))),
        )
        colors = (
            ('coral', 'w'),
            ('skyblue', 'w'),
            ('w', 'w'),
            ('w', 'w'),
            ('w', 'w'),
            ('w', 'w' if error_mag < threshold else 'tomato'),
        )
        ax.table(cellText=rows, cellColours=colors, loc='center')
        ax.axis('off')

    def draw_fiducial_rois(chunk, ax, cell):
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        vmin = voxels.min()
        vmax = voxels.max()

        gs_outer = gridspec.GridSpecFromSubplotSpec(2, 1, height_ratios=[1, 100], subplot_spec=cell)
        title_ax = plt.subplot(gs_outer[0, 0])
        title_ax.set_title('Top 100 Most Distorted Grid Intersections')
        title_ax.axis('off')

        gs_inner = gridspec.GridSpecFromSubplotSpec(num_roi_chunks, 4, width_ratios=[1, 1, 1, 2], subplot_spec=gs_outer[1, 0])

        for i, (a_S, b, error_vec, error_mag) in enumerate(chunk):
            b_ijk = apply_affine_1(xyz_to_ijk, b)
            a_S_ijk = apply_affine_1(xyz_to_ijk, a_S)
            shape = roi_shape(grid_radius, voxel_spacing(ijk_to_xyz))
            bounds = roi_bounds(b_ijk, shape)
            ij, ik, jk = roi_images(b_ijk, voxels, bounds)

            ax0 = plt.subplot(gs_inner[i, 0])
            ax0.set_xlabel('i')
            ax0.set_ylabel('j')
            generate_roi_view(ax0, ij, bounds[0], bounds[1], (a_S_ijk[0], a_S_ijk[1]), (b_ijk[0], b_ijk[1]), vmin, vmax)

            ax1 = plt.subplot(gs_inner[i, 1])
            ax1.set_xlabel('i')
            ax1.set_ylabel('k')
            generate_roi_view(ax1, ik, bounds[0], bounds[2], (a_S_ijk[0], a_S_ijk[2]), (b_ijk[0], b_ijk[2]), vmin, vmax)

            ax2 = plt.subplot(gs_inner[i, 2])
            ax2.set_xlabel('j')
            ax2.set_ylabel('k')
            generate_roi_view(ax2, jk, bounds[1], bounds[2], (a_S_ijk[1], a_S_ijk[2]), (b_ijk[1], b_ijk[2]), vmin, vmax)

            ax3 = plt.subplot(gs_inner[i, 3])
            generate_roi_table(ax3, a_S, b, error_vec, error_mag)

    def draw_points(ax, cell, looking_down_axis=None):
        gs = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=cell)
        ax_inner = plt.subplot(gs[0], projection='3d')
        points_fig = scatter3({'Actual': TP_A_S, 'Detected': TP_B}, ax_inner)

        axis2angles = {
            'x': (20, -5),
            'y': (20, 85),
            'z': (70, 5),
        }
        if looking_down_axis:
            ax_inner.view_init(*axis2angles[looking_down_axis])
        return points_fig

    draw_points_x_perspective = partial(draw_points, looking_down_axis='x')
    draw_points_y_perspective = partial(draw_points, looking_down_axis='y')
    draw_points_z_perspective = partial(draw_points, looking_down_axis='z')

    grid_a, grid_b, gridded = axial_spatial_mapping_data()
    draw_axial_spatial_mapping = partial(draw_axial_spatial_mapping, grid_a, grid_b, gridded)

    grid_a, grid_b, gridded = sagittal_spatial_mapping_data()
    draw_sagittal_spatial_mapping = partial(draw_sagittal_spatial_mapping, grid_a, grid_b, gridded)

    grid_a, grid_b, gridded = coronal_spatial_mapping_data()
    draw_coronal_spatial_mapping = partial(draw_coronal_spatial_mapping, grid_a, grid_b, gridded)

    error_table_rows = error_table_data(distances, error_mags, 5)

    # TODO write PDF in memory
    with PdfPages(full_report_path) as pdf:
        report_title = "Full Report"
        get_page = page_generator()
        create_page_full = partial(create_page, pdf, report_title, get_page)

        create_cover_page(pdf, report_title.upper())

        create_page_full(draw_institution_table)
        create_page_full(draw_data_acquisition_table)
        create_page_full(draw_phantom_description)
        create_page_full(draw_scatter_plot)
        create_page_full(draw_axial_spatial_mapping)
        create_page_full(draw_sagittal_spatial_mapping)
        create_page_full(draw_coronal_spatial_mapping)

        all_chunks = chunks(error_table_rows, num_error_table_rows)
        for chunk in all_chunks:
            draw_chunk = partial(draw_error_table, chunk)
            create_page_full(draw_chunk)

        sort_indices = np.argsort(error_mags)[::-1]
        rois = zip(TP_A_S.T[sort_indices], TP_B.T[sort_indices], error_vecs.T[sort_indices], error_mags[sort_indices])
        all_chunks = chunks(list(rois), num_roi_chunks)
        for chunk in itertools.islice(all_chunks, 100 // num_roi_chunks):
            draw_chunk = partial(draw_fiducial_rois, chunk)
            create_page_full(draw_chunk)

        create_page_full(draw_points_x_perspective)

    with PdfPages(executive_report_path) as pdf:
        report_title = "Executive Report"
        get_page = page_generator()
        create_page_executive = partial(create_page, pdf, report_title, get_page)

        create_cover_page(pdf, report_title.upper())

        create_page_executive(draw_institution_table)
        create_page_executive(draw_data_acquisition_table)
        create_page_executive(draw_phantom_description)
        create_page_executive(draw_scatter_plot)
        create_page_executive(draw_axial_spatial_mapping)
        create_page_executive(draw_sagittal_spatial_mapping)
        create_page_executive(draw_coronal_spatial_mapping)

        all_chunks = chunks(error_table_rows, num_error_table_rows)
        for chunk in all_chunks:
            draw_chunk = partial(draw_error_table, chunk)
            create_page_executive(draw_chunk)

        create_page_executive(draw_points_x_perspective)

    logger.info("finished report generation")


def page_generator():
    i = 1
    while True:
        yield i
        i += 1


def save_then_close_figure(pdf, figure):
    pdf.savefig(figure, dpi=350)
    plt.close('all')


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
    affine_matrix = affine.rotation_translation(0, 0, 0, np.pi / 180 * 10, np.pi / 180 * 10, np.pi / 180 * 10)

    A = apply_affine(affine_matrix, A)

    with zipfile.ZipFile('data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip') as zip_file:
        datasets = dicom_import.dicom_datasets_from_zip(zip_file)

    voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)

    class Institution:
        name = "Johns Hopkins"
        address = "3101 Wyman Park Dr.\nBaltimore, MD 21211"
        phone_number = "555-555-5555"

    generate_reports(A, B, datasets, voxels, ijk_to_xyz, '603A', 2.5, Institution, 'Machine A', 'Sequence A', 'Phantom A',
                     datetime.now(), 'tmp/full_report.pdf', 'tmp/executive_report.pdf')
