import zipfile
import math
from collections import OrderedDict

import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from scipy.interpolate.interpnd import LinearNDInterpolator
from scipy.interpolate.ndgriddata import griddata

from process import affine, phantoms
from process.affine import apply_affine, pixel_spacing
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


def roi_shape(grid_radius, pixel_spacing):
    return tuple(math.ceil(grid_radius / dim * 8) for dim in pixel_spacing)


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


def generate_report(TP_A_S, TP_B, datasets, voxels, ijk_to_xyz, phantom_model_number, threshold, institution, pdf_path):
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

    # assume that the isocenter is the geometric origin
    isocenter = ((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2)

    # interpolate onto spheres of increasing size to calculate average and max error table
    interpolator = LinearNDInterpolator(TP_A_S.T, error_mags.T)

    radius2max_mean_error = OrderedDict()

    r = SPHERE_STEP_mm
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
            r += SPHERE_STEP_mm

    def generate_institution_table():
        table_fig = plt.figure()
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

    def generate_data_acquisition_table():
        table_fig = plt.figure()
        dataset = datasets[0]
        voxel_dims = pixel_spacing(ijk_to_xyz)
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
            ('Slice thickness', f'{voxel_dims[2]} mm'),
            ('Direction of phase encoding', dataset.InPlanePhaseEncodingDirection),
        ]
        plt.table(cellText=rows, loc='center')
        plt.axis('off')
        plt.title('Data Acquisition Table')
        return table_fig

    def generate_spacial_mapping(grid_x, grid_y, gridded):
        contour_fig = plt.figure()

        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        contour = plt.contour(grid_x.squeeze(), grid_y.squeeze(), gridded.squeeze(), cmap=cmap, norm=norm)
        plt.clabel(contour, inline=True, fontsize=10)
        return contour_fig

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

    def generate_scatter_plot():
        scatter_fig = plt.figure()
        origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
        distances = np.linalg.norm(TP_A_S.T - origins, axis=1)

        cmap = colors.ListedColormap(['green', 'red'])
        bounds = [0, threshold, math.inf]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        plt.plot([0, distances.max()], [threshold, threshold], c='red', linestyle='dashed')
        plt.scatter(distances, error_mags, c=error_mags, cmap=cmap, norm=norm)
        plt.xlabel('Distance from Isocenter [mm]')
        plt.ylabel('Distortion Magnitude [mm]')
        plt.title('Scatter Plot of Geometric Distortion vs. Distance from Isocenter')
        return scatter_fig

    def generate_error_table():
        table_fig = plt.figure()
        rows = []
        for r, (max_value, mean_value) in radius2max_mean_error.items():
            rows.append((r, np.round(max_value, 3), np.round(mean_value, 3)))
        plt.table(cellText=rows, colLabels=['Distance from Isocenter [mm]', 'Maximum Error [mm]', 'Average Error [mm]'],
                  loc='center')
        plt.axis('off')
        plt.title('Error Table')
        return table_fig

    def generate_roi_table():
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        rois = zip(TP_A_S.T, TP_B.T, error_vecs.T, error_mags.T)

        figs = []
        for chunk in chunks(list(rois), 3):
            roi_fig = plt.figure()
            subplot_dim = (3, 4)
            plt.suptitle('Fiducial ROIs')
            plt.axis('off')

            for i, (A, B, error_vec, error_mag) in enumerate(chunk):
                B_ijk = apply_affine(xyz_to_ijk, np.array([B]).T).T.squeeze()
                shape = roi_shape(grid_radius, pixel_spacing(ijk_to_xyz))
                bounds = roi_bounds(B, shape)
                bounds_ijk = roi_bounds(B_ijk, shape)
                axial, sagittal, coronal = roi_images(B_ijk, voxels, bounds_ijk)

                plt1 = plt.subplot2grid(subplot_dim, (i, 0))
                plt1.imshow(axial, cmap='Greys', extent=[*bounds[0], *bounds[1]], aspect='auto')
                plt1.scatter([A[0]], [A[1]], c='gold')
                plt1.scatter([B[0]], [B[1]])
                plt1.set_xticks([])
                plt1.set_yticks([])
                plt1.set_xlim(bounds[0])
                plt1.set_ylim(bounds[1])

                plt2 = plt.subplot2grid(subplot_dim, (i, 1))
                plt2.imshow(sagittal, cmap='Greys', extent=[*bounds[0], *bounds[2]], aspect='auto')
                plt2.scatter([A[0]], [A[2]], c='gold')
                plt2.scatter([B[0]], [B[2]])
                plt2.set_xticks([])
                plt2.set_yticks([])
                plt2.set_xlim(bounds[0])
                plt2.set_ylim(bounds[2])

                plt3 = plt.subplot2grid(subplot_dim, (i, 2))
                plt3.imshow(coronal, cmap='Greys', extent=[*bounds[1], *bounds[2]], aspect='auto')
                plt3.scatter([A[1]], [A[2]], c='gold')
                plt3.scatter([B[1]], [B[2]])
                plt3.set_xticks([])
                plt3.set_yticks([])
                plt3.set_xlim(bounds[1])
                plt3.set_ylim(bounds[2])

                plt4 = plt.subplot2grid(subplot_dim, (i, 3))
                rows = [
                    ('x', f'{str(round(error_vec[0], 3))} mm'),
                    ('y', f'{str(round(error_vec[1], 3))} mm'),
                    ('z', f'{str(round(error_vec[2], 3))} mm'),
                    ('magnitude', f'{str(round(error_mag, 3))} mm'),
                ]
                plt4.table(cellText=rows, loc='center')
                plt4.set_title('Distortion')
                plt4.axis('off')

            figs.append(roi_fig)
        return figs

    def generate_points():
        points_fig = scatter3({'A_S': TP_A_S, 'B': TP_B})
        return points_fig

    def generate_quiver():
        quiver_fig = plt.figure()
        ax = quiver_fig.add_subplot(111, projection='3d')
        ax.quiver(*TP_A_S, *error_vecs)
        return quiver_fig

    with PdfPages(pdf_path) as pdf:
        pdf.savefig(generate_institution_table())
        pdf.savefig(generate_data_acquisition_table())

        pdf.savefig(generate_axial_spacial_mapping())
        pdf.savefig(generate_sagittal_spacial_mapping())
        pdf.savefig(generate_coronal_spacial_mapping())
        for fig in (generate_axial_spacial_mapping_series()):
            pdf.savefig(fig)

        pdf.savefig(generate_scatter_plot())
        pdf.savefig(generate_error_table())

        for fig in (generate_roi_table()):
            pdf.savefig(fig)

        pdf.savefig(generate_points())
        pdf.savefig(generate_quiver())


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

    generate_report(A, B, datasets, voxels, ijk_to_xyz, '603A', 2.5, Institution, 'tmp/report.pdf')
