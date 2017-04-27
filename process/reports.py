import zipfile
import math
from collections import OrderedDict

import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from scipy.interpolate.interpnd import LinearNDInterpolator
from scipy.interpolate.ndgriddata import griddata

from process import affine
from process.affine import apply_affine
from process.visualization import scatter3
from process import dicom_import

GRID_DENSITY_mm = 0.5
SPHERE_STEP_mm = 1
SPHERE_POINTS_PER_AREA = 1


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
    return tuple(math.ceil(grid_radius / dim * 4) for dim in pixel_spacing)


def roi_bounds(B, shape):
    return (
        (
            int(math.ceil(B[0])) - int(math.floor(shape[0] / 2)),
            int(math.ceil(B[0])) + int(math.ceil(shape[0] / 2)),
        ), (
            int(math.ceil(B[1])) - int(math.floor(shape[1] / 2)),
            int(math.ceil(B[1])) + int(math.ceil(shape[1] / 2)),
        ), (
            int(math.ceil(B[2])) - int(math.floor(shape[2] / 2)),
            int(math.ceil(B[2])) + int(math.ceil(shape[2] / 2)),
        ),
    )


def roi_image(voxels, bounds_list):
    adjusted_bounds_list = [(max(start, 0), min(end, voxels.shape[i])) for i, (start, end) in enumerate(bounds_list)]
    slices = [slice(*bounds) for bounds in adjusted_bounds_list]
    image = voxels[slices[0], slices[1], slices[2]].squeeze()

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


def generate_report(datasets, voxels, ijk_to_xyz, TP_A_S, TP_B, threshold, institution, pdf_path):
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

    # assume that the isocenter is the geometric origin
    isocenter = ((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2)

    # interpolate onto spheres of increasing size to calculate average and max error table
    interpolator = LinearNDInterpolator(TP_A_S.T, error_mags.T)
    max_sphere_radius = np.min(np.abs([x_min, y_min, z_min, x_max, y_max, z_max]))
    radius2max_mean_error = OrderedDict()

    for r in np.arange(SPHERE_STEP_mm, max_sphere_radius, SPHERE_STEP_mm):
        num_points = int(round(surface_area(r)/SPHERE_POINTS_PER_AREA))
        equidistant_sphere_points = generate_equidistant_sphere(num_points) * r
        values = interpolator(equidistant_sphere_points)
        max_value, mean_value = np.max(values), np.mean(values)
        radius2max_mean_error[r] = (max_value, mean_value,)

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
        rows = [
            (r'Phantom filler T$_1$', ''),
            (r'Phantom filler T$_2$', ''),
            ('Phantom filler composition', ''),
            ('Sequence type', dataset.ScanningSequence),
            ('Pixel bandwidth', str(dataset.PixelBandwidth) + r' $\frac{Hz}{px}$'),
            ('Voxel dimensions', ' x '.join([f'{str(round(x, 3))} mm' for x in [*dataset.PixelSpacing, dataset.SliceThickness]])), # TODO
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
            ('Slice thickness', f'{dataset.SliceThickness} mm'),
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
        for z in np.arange(z_min, z_max, 2):
            grid_x, grid_y, grid_z = np.meshgrid(np.arange(x_min, x_max, GRID_DENSITY_mm),
                                                 np.arange(y_min, y_max, GRID_DENSITY_mm),
                                                 [z])
            gridded = griddata(TP_A_S.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')

            # TODO why does this happen when z = z_min?
            if not np.isnan(gridded).all():
                contour_fig = generate_spacial_mapping(grid_x, grid_y, gridded)
                plt.xlabel('x [mm]')
                plt.ylabel('y [mm]')
                plt.title(f'Axial Contour Plot Series (z = {z} mm)')
                figs.append(contour_fig)
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
        rois = zip(apply_affine(xyz_to_ijk, TP_A_S).T, apply_affine(xyz_to_ijk, TP_B).T)
        size = 12

        figs = []
        for (A, B) in list(rois)[:1]:  # TODO
            roi_fig = plt.figure()

            x_slice = slice(int(B[0]) - size, int(B[0]) + size)
            y_slice = slice(int(B[1]) - size, int(B[1]) + size)
            z_slice = slice(int(B[2]) - size, int(B[2]) + size)

            axial_slice = voxels[x_slice, y_slice, int(B[2])]
            sagittal_slice = voxels[x_slice, int(B[1]), z_slice]
            coronal_slice = voxels[int(B[0]), y_slice, z_slice]

            axial_plt = roi_fig.add_subplot(111)
            axial_plt.imshow(axial_slice, cmap='Greys_r')

            sagittal_plt = roi_fig.add_subplot(111)
            sagittal_plt.imshow(sagittal_slice, cmap='Greys_r')

            coronal_plt = roi_fig.add_subplot(111)
            coronal_plt.imshow(coronal_slice, cmap='Greys_r')

            plt.axis('off')
            plt.title('Fiducial ROIs')
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
        for fig in (generate_roi_table()):
            pdf.savefig(fig)

        pdf.savefig(generate_institution_table())
        pdf.savefig(generate_data_acquisition_table())

        pdf.savefig(generate_axial_spacial_mapping())
        pdf.savefig(generate_sagittal_spacial_mapping())
        pdf.savefig(generate_coronal_spacial_mapping())
        for fig in (generate_axial_spacial_mapping_series()):
            pdf.savefig(fig)

        pdf.savefig(generate_scatter_plot())
        pdf.savefig(generate_error_table())

        pdf.savefig(generate_points())
        pdf.savefig(generate_quiver())


def generate_cube(size, x0=0):
    points = []
    for x in range(-size, size):
        for y in range(-size, size):
            for z in range(-size, size):
                points.append((float(x), float(y), float(z)))
    return np.array(points).T


if __name__ == '__main__':
    A = generate_cube(8)
    B = generate_cube(8)
    affine_matrix = affine.translation_rotation(0, 0, 0, np.pi / 180 * 2, np.pi / 180 * 2, np.pi / 180 * 2)

    A = apply_affine(affine_matrix, A)

    with zipfile.ZipFile('data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip') as zip_file:
        datasets = dicom_import.dicom_datasets_from_zip(zip_file)

    voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)

    class Institution:
        name = "Johns Hopkins"
        number_of_licenses = 12
        address = "3101 Wyman Park Dr.\nBaltimore, MD 21211"
        phone_number = "555-555-5555"

    generate_report(datasets, voxels, ijk_to_xyz, A, B, 0.4, Institution, 'report.pdf')
