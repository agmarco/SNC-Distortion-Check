import numpy as np

from process.reports import generate_equidistant_sphere, roi_shape, roi_bounds, roi_images


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
    Asserts the dimension sizes are rounded up if 8x the grid radius is not a multiple of the voxel spacing.
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

    ij, ik, jk = roi_images(B_ijk, voxels, roi_bounds(B_ijk, shape))

    B_ij = (4, 5)
    B_ik = (4, 6)
    B_jk = (5, 6)

    assert ij.shape == (9, 11)
    assert ij[B_ij[0] - 1, B_ij[1] - 1] == 0.11
    assert ij[B_ij[0] - 1, B_ij[1] + 1] == 0.21
    assert ij[B_ij[0] + 1, B_ij[1] - 1] == 0.31
    assert ij[B_ij[0] + 1, B_ij[1] + 1] == 0.41

    assert ik.shape == (9, 13)
    assert ik[B_ik[0] - 1, B_ik[1] - 1] == 0.12
    assert ik[B_ik[0] - 1, B_ik[1] + 1] == 0.22
    assert ik[B_ik[0] + 1, B_ik[1] - 1] == 0.32
    assert ik[B_ik[0] + 1, B_ik[1] + 1] == 0.42

    assert jk.shape == (11, 13)
    assert jk[B_jk[0] - 1, B_jk[1] - 1] == 0.13
    assert jk[B_jk[0] - 1, B_jk[1] + 1] == 0.23
    assert jk[B_jk[0] + 1, B_jk[1] - 1] == 0.33
    assert jk[B_jk[0] + 1, B_jk[1] + 1] == 0.43


def test_roi_fiducial_near_x_start():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (0, 50, 50)
    bounds = ((-4, 5), (46, 55), (46, 55))

    ij, ik, jk = roi_images(center, voxels, bounds)

    assert ij.shape == (shape[0], shape[1])
    assert ik.shape == (shape[0], shape[2])
    assert jk.shape == (shape[1], shape[2])

    assert np.isnan(ij[0:4, :]).all()
    assert np.isnan(ik[0:4, :]).all()
    assert (jk == 0).all()


def test_roi_fiducial_near_x_end():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (99, 50, 50)
    bounds = ((95, 104), (46, 55), (46, 55))

    ij, ik, jk = roi_images(center, voxels, bounds)

    assert ij.shape == (shape[0], shape[1])
    assert ik.shape == (shape[0], shape[2])
    assert jk.shape == (shape[1], shape[2])

    assert np.isnan(ij[5:, :]).all()
    assert np.isnan(ik[5:, :]).all()
    assert (jk == 0).all()


def test_roi_fiducial_near_y_start():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 0, 50)
    bounds = ((46, 55), (-4, 5), (46, 55))

    ij, ik, jk = roi_images(center, voxels, bounds)

    assert ij.shape == (shape[0], shape[1])
    assert ik.shape == (shape[0], shape[2])
    assert jk.shape == (shape[1], shape[2])

    assert np.isnan(ij[:, 0:4]).all()
    assert (ik == 0).all()
    assert np.isnan(jk[0:4, :]).all()


def test_roi_fiducial_near_y_end():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 99, 50)
    bounds = ((46, 55), (95, 104), (46, 55))

    ij, ik, jk = roi_images(center, voxels, bounds)

    assert ij.shape == (shape[0], shape[1])
    assert ik.shape == (shape[0], shape[2])
    assert jk.shape == (shape[1], shape[2])

    assert np.isnan(ij[:, 5:]).all()
    assert (ik == 0).all()
    assert np.isnan(jk[5:, :]).all()


def test_roi_fiducial_near_z_start():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 50, 0)
    bounds = ((46, 55), (46, 55), (-4, 5))

    ij, ik, jk = roi_images(center, voxels, bounds)

    assert ij.shape == (shape[0], shape[1])
    assert ik.shape == (shape[0], shape[2])
    assert jk.shape == (shape[1], shape[2])

    assert (ij == 0).all()
    assert np.isnan(ik[:, 0:4]).all()
    assert np.isnan(jk[:, 0:4]).all()


def test_roi_fiducial_near_z_end():
    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))

    shape = (9, 9, 9)
    center = (50, 50, 99)
    bounds = ((46, 55), (46, 55), (95, 104))

    ij, ik, jk = roi_images(center, voxels, bounds)

    assert ij.shape == (shape[0], shape[1])
    assert ik.shape == (shape[0], shape[2])
    assert jk.shape == (shape[1], shape[2])

    assert (ij == 0).all()
    assert np.isnan(ik[:, 5:]).all()
    assert np.isnan(jk[:, 5:]).all()


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
