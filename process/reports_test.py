import numpy as np

from process.reports import generate_equidistant_sphere, roi_shape, roi_bounds, roi_image


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
    Asserts the dimension sizes are 4x the grid radius.
    """

    grid_radius = 1.5
    pixel_spacing = [0.25, 0.5, 0.75]
    shape = roi_shape(grid_radius, pixel_spacing)
    assert shape == (96, 48, 32)


def test_roi_shape_rounding():
    """
    Asserts the dimension sizes are rounded up if 4x the grid radius is not a multiple of the pixel spacing.
    """

    grid_radius = 1.51
    pixel_spacing = [0.5, 0.5, 0.5]
    shape = roi_shape(grid_radius, pixel_spacing)
    assert shape == (49, 49, 49)


def test_roi_fiducial_near_top_left_corner_size():
    """
    Asserts the ROI image generated from a fiducial near (0, 0, 0) is the right size.
    """

    voxels_size = 100
    voxels = np.ones((voxels_size, voxels_size, voxels_size))
    shape = (9, 9, 9)

    bounds = ((-4, 5), (-4, 5), (-4, 5))

    axial_image = roi_image(voxels, (bounds[0], bounds[1], (0, 1)))
    sagittal_image = roi_image(voxels, (bounds[0], (0, 1), bounds[2]))
    coronal_image = roi_image(voxels, ((0, 1), bounds[1], bounds[2]))

    assert axial_image.shape == (shape[0], shape[1])
    assert sagittal_image.shape == (shape[0], shape[2])
    assert coronal_image.shape == (shape[1], shape[2])


def test_roi_fiducial_near_top_left_corner_overflow():
    """
    Asserts the ROI image generated from a fiducial near (0, 0, 0) fills the extra space with black.
    """

    voxels_size = 100
    voxels = np.ones((voxels_size, voxels_size, voxels_size))

    bounds = ((-4, 5), (-4, 5), (-4, 5))

    axial_image = roi_image(voxels, (bounds[0], bounds[1], (0, 1)))
    sagittal_image = roi_image(voxels, (bounds[0], (0, 1), bounds[2]))
    coronal_image = roi_image(voxels, ((0, 1), bounds[1], bounds[2]))

    assert (axial_image[0:4, :] == 0).all() and (axial_image[:, 0:4] == 0).all()
    assert (sagittal_image[0:4, :] == 0).all() and (sagittal_image[:, 0:4] == 0).all()
    assert (coronal_image[0:4, :] == 0).all() and (coronal_image[:, 0:4] == 0).all()


def test_roi_fiducial_near_bottom_right_corner_size():
    """
    Asserts the ROI image generated from a fiducial near (n, m, l) is the right size.
    """

    voxels_size = 100
    voxels = np.ones((voxels_size, voxels_size, voxels_size))
    shape = (9, 9, 9)

    bounds = ((95, 104), (95, 104), (95, 104))

    axial_image = roi_image(voxels, (bounds[0], bounds[1], (0, 1)))
    sagittal_image = roi_image(voxels, (bounds[0], (0, 1), bounds[2]))
    coronal_image = roi_image(voxels, ((0, 1), bounds[1], bounds[2]))

    assert axial_image.shape == (shape[0], shape[1])
    assert sagittal_image.shape == (shape[0], shape[2])
    assert coronal_image.shape == (shape[1], shape[2])


def test_roi_fiducial_near_bottom_right_corner_overflow():
    """
    Asserts the ROI image generated from a fiducial near (n, m, l) fills the extra space with black.
    """

    voxels_size = 100
    voxels = np.ones((voxels_size, voxels_size, voxels_size))

    bounds = ((95, 104), (95, 104), (95, 104))

    axial_image = roi_image(voxels, (bounds[0], bounds[1], (0, 1)))
    sagittal_image = roi_image(voxels, (bounds[0], (0, 1), bounds[2]))
    coronal_image = roi_image(voxels, ((0, 1), bounds[1], bounds[2]))

    assert (axial_image[95:, :] == 0).all() and (axial_image[:, 95:] == 0).all()
    assert (sagittal_image[95:, :] == 0).all() and (sagittal_image[:, 95:] == 0).all()
    assert (coronal_image[95:, :] == 0).all() and (coronal_image[:, 95:] == 0).all()


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
    Asserts the detected fiducial coordinates are rounded up.
    """

    shape = (9, 9, 9)
    B = (49.1, 49.1, 49.1)
    bounds_list = roi_bounds(B, shape)
    assert all(bounds == (46, 55) for bounds in bounds_list)
