import numpy as np

from process.reports import generate_equidistant_sphere, roi_size, roi_slices, roi_image


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


def test_roi_size():
    """
    Asserts the size is the max of the max distortion error and 4 x the grid radius.
    """

    grid_radius = 1.5
    pixel_spacing = [0.5, 0.5]

    A = np.array([[0], [0], [0]])
    B = np.array([[0], [0], [0]])
    size = roi_size(A, B, grid_radius, pixel_spacing)
    assert size == 12

    A = np.array([[0], [0], [0]])
    B = np.array([[13], [0], [0]])
    size = roi_size(A, B, grid_radius, pixel_spacing)
    assert size > 13


def test_roi_fiducial_near_edge():
    """
    Asserts the ROI image generated from a fiducial near an edge is the right size.
    """

    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))
    size = 12

    A = B = (0, 0, 0)
    slices = roi_slices(A, B, voxels, size)
    axial_image = roi_image(voxels, (slices[0], slices[1], 0))
    sagittal_image = roi_image(voxels, (slices[0], 0, slices[2]))
    coronal_image = roi_image(voxels, (0, slices[1], slices[2]))

    assert axial_image.shape == (size, size, size)
    assert sagittal_image.shape == (size, size, size)
    assert coronal_image.shape == (size, size, size)

    A = B = (99, 99, 99)
    slices = roi_slices(A, B, voxels, size)
    axial_image = roi_image(voxels, (slices[0], slices[1], 0))
    sagittal_image = roi_image(voxels, (slices[0], 0, slices[2]))
    coronal_image = roi_image(voxels, (0, slices[1], slices[2]))

    assert axial_image.shape == (size, size, size)
    assert sagittal_image.shape == (size, size, size)
    assert coronal_image.shape == (size, size, size)


def test_roi_center():
    """
    Asserts the ROI image is centered at the detected fiducial.
    """

    voxels_size = 100
    voxels = np.zeros((voxels_size, voxels_size, voxels_size))
    size = 12

    A = (50, 50, 50)
    B = (60, 60, 60)
    slices = roi_slices(A, B, voxels, size)
    indices_list = [roi_slice.indices(voxels_size) for roi_slice in slices]
    assert all(int(sum(indices) / 2) in (59, 60, 61) for indices in indices_list)
