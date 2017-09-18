import numpy as np

from process.reports import roi_shape, roi_bounds, roi_images, error_table_data


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


def test_error_table_simple():
    distances = np.array([0, 2.5, 5, 12])
    error_mags = np.array([0, 1, 0.5, 2.5])
    error_table = error_table_data(distances, error_mags, 5)
    assert error_table == [
        (5, 1.0, 0.5, 2),
        (10, 0.5, 0.5, 1),
        (15, 2.5, 2.5, 1),
    ]


def test_error_table_empty_bands():
    distances = np.array([1, 12])
    error_mags = np.array([1, 12])
    error_table = error_table_data(distances, error_mags, 5)
    assert error_table == [
        (5, 1.0, 1.0, 1),
        (10, "", "", 0),
        (15, 12, 12, 1),
    ]


def test_error_table_long_range():
    distances = np.arange(150)
    error_mags = np.ones(150)
    error_table = error_table_data(distances, error_mags, 5)
    assert len(error_table) == 150/5
    assert [r for r, _, _, _ in error_table] == list(range(0 + 5, 150 + 5, 5))
    assert all([max_value == 1 for _, max_value, _, _ in error_table])
    assert all([mean_value == 1 for _, _, mean_value, _ in error_table])
    assert all([num_values == 5 for _, _, _, num_values in error_table])
