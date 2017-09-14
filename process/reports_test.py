import numpy as np

from process.reports import generate_equidistant_sphere, roi_shape, roi_bounds, roi_images, error_table_data


def test_evenly_sampled_sphere_equidistant():
    """
    Asserts the algorithm to evenly space points on a sphere appears to work as expected.
    """

    n = 256
    points = generate_equidistant_sphere(n)
    min_distances_squared = []
    for point in points:
        distances_squared = np.sum((points.T - point.reshape((3, 1)))**2, axis=0)
        min_distance = np.min(distances_squared[distances_squared>0])
        min_distances_squared.append(min_distance)
    distances = np.sqrt(np.array(min_distances_squared))
    std = np.std(distances)
    mean = np.mean(distances)
    cv = std / mean
    assert cv < 0.02


def test_roi_shape():
    """
    Asserts the dimension sizes are 8x the grid radius.
    """

    grid_radius = 1.5
    voxel_spacing = [0.25, 0.5, 0.75]
    shape = roi_shape(grid_radius, voxel_spacing)
    assert shape == (48, 24, 16)


def test_roi_shape_rounding():
    """
    Asserts the dimension sizes are rounded up if 8x the grid radius is not a multiple of the pixel spacing.
    """

    grid_radius = 1.51
    voxel_spacing = [0.5, 0.5, 0.5]
    shape = roi_shape(grid_radius, voxel_spacing)
    assert shape == (25, 25, 25)


def test_roi_images():
    """
    Asserts that the 3 images have the right shape and orientation.
    """

    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))
    shape = (9, 11, 13)

    B_ijk = (50, 50, 50)
    voxels[B_ijk[0] - 1, B_ijk[1] - 1, 50] = 0.11
    voxels[B_ijk[0] - 1, B_ijk[1] + 1, 50] = 0.21
    voxels[B_ijk[0] + 1, B_ijk[1] - 1, 50] = 0.31
    voxels[B_ijk[0] + 1, B_ijk[1] + 1, 50] = 0.41

    voxels[B_ijk[0] - 1, 50, B_ijk[2] - 1] = 0.12
    voxels[B_ijk[0] - 1, 50, B_ijk[2] + 1] = 0.22
    voxels[B_ijk[0] + 1, 50, B_ijk[2] - 1] = 0.32
    voxels[B_ijk[0] + 1, 50, B_ijk[2] + 1] = 0.42

    voxels[50, B_ijk[1] - 1, B_ijk[2] - 1] = 0.13
    voxels[50, B_ijk[1] - 1, B_ijk[2] + 1] = 0.23
    voxels[50, B_ijk[1] + 1, B_ijk[2] - 1] = 0.33
    voxels[50, B_ijk[1] + 1, B_ijk[2] + 1] = 0.43

    axial, sagittal, coronal = roi_images(B_ijk, voxels, roi_bounds(B_ijk, shape), 1)

    B_axial = (4, 5)
    B_sagittal = (4, 6)
    B_coronal = (5, 6)

    assert axial.shape == (9, 11)
    assert axial[B_axial[0] - 1, B_axial[1] - 1] == 0.11
    assert axial[B_axial[0] - 1, B_axial[1] + 1] == 0.21
    assert axial[B_axial[0] + 1, B_axial[1] - 1] == 0.31
    assert axial[B_axial[0] + 1, B_axial[1] + 1] == 0.41

    assert sagittal.shape == (9, 13)
    assert sagittal[B_sagittal[0] - 1, B_sagittal[1] - 1] == 0.12
    assert sagittal[B_sagittal[0] - 1, B_sagittal[1] + 1] == 0.22
    assert sagittal[B_sagittal[0] + 1, B_sagittal[1] - 1] == 0.32
    assert sagittal[B_sagittal[0] + 1, B_sagittal[1] + 1] == 0.42

    assert coronal.shape == (11, 13)
    assert coronal[B_coronal[0] - 1, B_coronal[1] - 1] == 0.13
    assert coronal[B_coronal[0] - 1, B_coronal[1] + 1] == 0.23
    assert coronal[B_coronal[0] + 1, B_coronal[1] - 1] == 0.33
    assert coronal[B_coronal[0] + 1, B_coronal[1] + 1] == 0.43


def test_roi_fiducial_near_x_start():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (0, 50, 50)
    bounds = ((-4, 5), (46, 55), (46, 55))

    axial, sagittal, coronal = roi_images(center, voxels, bounds, 1)

    assert axial.shape == (shape[0], shape[1])
    assert sagittal.shape == (shape[0], shape[2])
    assert coronal.shape == (shape[1], shape[2])

    assert (axial[0:4, :] == 1).all()
    assert (sagittal[0:4, :] == 1).all()
    assert (coronal == 0).all()


def test_roi_fiducial_near_x_end():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (99, 50, 50)
    bounds = ((95, 104), (46, 55), (46, 55))

    axial, sagittal, coronal = roi_images(center, voxels, bounds, 1)

    assert axial.shape == (shape[0], shape[1])
    assert sagittal.shape == (shape[0], shape[2])
    assert coronal.shape == (shape[1], shape[2])

    assert (axial[5:, :] == 1).all()
    assert (sagittal[5:, :] == 1).all()
    assert (coronal == 0).all()


def test_roi_fiducial_near_y_start():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 0, 50)
    bounds = ((46, 55), (-4, 5), (46, 55))

    axial, sagittal, coronal = roi_images(center, voxels, bounds, 1)

    assert axial.shape == (shape[0], shape[1])
    assert sagittal.shape == (shape[0], shape[2])
    assert coronal.shape == (shape[1], shape[2])

    assert (axial[:, 0:4] == 1).all()
    assert (sagittal == 0).all()
    assert (coronal[0:4, :] == 1).all()


def test_roi_fiducial_near_y_end():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 99, 50)
    bounds = ((46, 55), (95, 104), (46, 55))

    axial, sagittal, coronal = roi_images(center, voxels, bounds, 1)

    assert axial.shape == (shape[0], shape[1])
    assert sagittal.shape == (shape[0], shape[2])
    assert coronal.shape == (shape[1], shape[2])

    assert (axial[:, 5:] == 1).all()
    assert (sagittal == 0).all()
    assert (coronal[5:, :] == 1).all()


def test_roi_fiducial_near_z_start():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 50, 0)
    bounds = ((46, 55), (46, 55), (-4, 5))

    axial, sagittal, coronal = roi_images(center, voxels, bounds, 1)

    assert axial.shape == (shape[0], shape[1])
    assert sagittal.shape == (shape[0], shape[2])
    assert coronal.shape == (shape[1], shape[2])

    assert (axial == 0).all()
    assert (sagittal[:, 0:4] == 1).all()
    assert (coronal[:, 0:4] == 1).all()


def test_roi_fiducial_near_z_end():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 50, 99)
    bounds = ((46, 55), (46, 55), (95, 104))

    axial, sagittal, coronal = roi_images(center, voxels, bounds, 1)

    assert axial.shape == (shape[0], shape[1])
    assert sagittal.shape == (shape[0], shape[2])
    assert coronal.shape == (shape[1], shape[2])

    assert (axial == 0).all()
    assert (sagittal[:, 5:] == 1).all()
    assert (coronal[:, 5:] == 1).all()


def test_roi_center_odd_size():
    """
    Asserts the detected fiducial is at the center pixel of the ROI image when the size is odd.
    """

    shape = (9, 9, 9)
    B = (60, 60, 60)
    bounds_list = roi_bounds(B, shape)
    assert all(bounds == (56, 65) for bounds in bounds_list)


def test_roi_center_even_size():
    """
    Asserts the detected fiducial is at one of the four center pixels of the ROI image when the size is even.
    """

    shape = (10, 10, 10)
    B = (60, 60, 60)
    bounds_list = roi_bounds(B, shape)
    assert all(bounds in ((55, 65), (56, 66)) for bounds in bounds_list)


def test_roi_center_rounding():
    """
    Asserts the detected fiducial coordinates are rounded properly.
    """

    shape = (9, 9, 9)
    B = (49.5, 49.5, 49.5)
    bounds_list = roi_bounds(B, shape)
    assert all(bounds in ((45, 54), (46, 55)) for bounds in bounds_list)


def test_error_table():
    TP_A_S = np.array([
        [0, 0, 0, -12],
        [0, 2.5, 0, 0],
        [0, 0, 5, 0],
    ])
    isocenter = [0, 0, 0]
    origins = np.repeat([isocenter], TP_A_S.shape[1], axis=0)
    distances = np.linalg.norm(TP_A_S.T - origins, axis=1)
    error_mags = np.array([0, 1, 0.5, 2.5])
    error_table = error_table_data(TP_A_S, distances, error_mags)
    assert error_table == [
        (5, 1.0, 0.5, 2),
        (10, 1.0, 0.5, 3),
        (15, 2.5, 1.0, 4),
    ]
