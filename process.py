import math

import numpy


def combine_dicom_slices(slice_datasets):
    '''
    Given a list of pydicom datasets for an image series, stitch them together into a
    three-dimensional numpy array that is oriented with the "patient coordinate
    system".  That is, the numpy array's dimensions will be oriented so that
    the first index is along the x-dimension, the second along they
    y-dimension, and the third along the z-dimension.

    The numpy array will be cast to floating point values.

    This function requires that the datasets fulfill these properties:

    - Are all part of the same series (0020,000E)
    - The set of slices provided has no internal "gaps"; note that missing
      slices on the ends of the dataset are not detected
    - The direction cosines for the rows and columns (0028,0037) are oriented
      along the axes of the patient coordinate system
    - The size of each slice and the spacing between the pixels in the slice
      must be the same (0020,0032)
    '''
    if len(slice_datasets) == 0:
        raise ValueError("Must provide at least one dataset")

    _ensure_slices_form_a_uniform_grid(slice_datasets)

    image_orientation = slice_datasets[0].ImageOrientationPatient
    (row_axis, column_axis, slice_axis), (row_flip, column_flip) = _axes_mapping(image_orientation)

    shape = [0, 0, 0]
    shape[row_axis] = slice_datasets[0].Rows
    shape[column_axis] = slice_datasets[0].Columns
    shape[slice_axis] = len(slice_datasets)
    data = numpy.empty(shape)

    sorted_slice_datasets = sorted(slice_datasets, key=lambda d: d.ImagePositionPatient[slice_axis])
    for c, dataset in enumerate(sorted_slice_datasets):
        slices = [slice(None), slice(None), slice(None)]
        slices[slice_axis] = c

        slice_data = dataset.pixel_array[::row_flip, ::column_flip]

        if row_axis > column_axis:
            slice_data = slice_data.T

        data[slices] = slice_data

    # TODO: this should return pixel spacing as well; currently assuming all
    # pixel spacing is ~1mm
    return data


def _validate_image_orientation(image_orientation):
    '''
    Ensure that the image orientation is supported

    - The direction cosines have magnitudes of 1 (just in case)
    - The direction cosines are perpendicular
    - The direction cosines are oriented along the patient coordinate system's axes
    '''
    row_cosine, column_cosine = _extract_cosines(image_orientation)

    if not _almost_zero(numpy.dot(row_cosine, column_cosine)):
        raise ValueError("Non-orthogonal direction cosines: {}, {}".format(row_cosine, column_cosine))

    if not _almost_one(numpy.linalg.norm(row_cosine)):
        raise ValueError("The row direction cosine's magnitude is not 1: {}".format(row_cosine))

    if not _almost_one(numpy.linalg.norm(column_cosine)):
        raise ValueError("The column direction cosine's magnitude is not 1: {}".format(column_cosine))

    if not _almost_one(numpy.max(numpy.abs(row_cosine))) or not _almost_one(numpy.max(numpy.abs(column_cosine))):
        # TODO: fix this; make the code work with datasets that are not oriented along the patient's coordinate system
        message = "Currently we only support DICOM files where the images are oriented along the patient coordinate system."
        raise ValueError(message)


def _almost_zero(value):
    return math.isclose(value, 0.0, rel_tol=1e-7)


def _almost_one(value):
    return math.isclose(value, 1.0, rel_tol=1e-7)


def _axes_mapping(image_orientation):
    '''
    The DICOM pixel data can be oriented in a number of different ways.  We
    need to simplify all of the variations out, and a key part of doing this is
    mapping the pixel data axes into patient coordinate system axes.

    The return values are a 3-tuple representing the mapping for the row, column,
    and slice axis respectively, and a 2-tuple indicating if the row or column
    axis needs to be flipped (the slice axis will never need to be flipped
    because we sort it according to the ImagePositionPatient which is already
    inside the patient's coordinate system.

    Each value maps onto patient coordinate system axis.  A
    value of 0 maps to the x-axis, 1 the y-axis, and 2 the z-axis.

    NOTE we assume that the cosines are oriented along the main patient axes
    '''
    row_cosine, column_cosine = _extract_cosines(image_orientation)

    row_axis = numpy.argmax(numpy.abs(row_cosine))
    column_axis = numpy.argmax(numpy.abs(column_cosine))

    slice_axis_cosine = numpy.cross(row_cosine, column_cosine)
    slice_axis = numpy.argmax(numpy.abs(slice_axis_cosine))

    row_flip = int(numpy.sign(row_cosine[row_axis]))
    column_flip = int(numpy.sign(column_cosine[column_axis]))

    return (row_axis, column_axis, slice_axis), (row_flip, column_flip)


def _extract_cosines(image_orientation):
    row_cosine = numpy.array(image_orientation[:3])
    column_cosine = numpy.array(image_orientation[3:])
    return row_cosine, column_cosine


def _ensure_slices_form_a_uniform_grid(slice_datasets):
    '''
    Perform various data checks to ensure that the list of slices form a
    evenly-spaced grid of data.

    Some of these checks are probably not required if the data follows the
    DICOM specification, however it seems pertinent to check anyway.
    '''
    image_orientation = slice_datasets[0].ImageOrientationPatient
    _validate_image_orientation(image_orientation)

    (row_axis, column_axis, slice_axis), _ = _axes_mapping(image_orientation)

    sop_class_uid = slice_datasets[0].SOPClassUID
    series_instance_uid = slice_datasets[0].SeriesInstanceUID
    pixel_spacing = slice_datasets[0].PixelSpacing
    row_position = slice_datasets[0].ImagePositionPatient[row_axis]
    column_position = slice_datasets[0].ImagePositionPatient[column_axis]
    rows = slice_datasets[0].Rows
    columns = slice_datasets[0].Columns

    slice_positions = []

    for dataset in slice_datasets:
        # TODO: improve this
        if dataset.SOPClassUID != sop_class_uid:
            raise ValueError('All slices must have the same SOP Class UID: {} != {}'.format(dataset.SOPClassUID, sop_class_uid))
        if dataset.SeriesInstanceUID != series_instance_uid:
            raise ValueError('All slices must be from the same series: {} != {}'.format(dataset.SeriesInstanceUID, series_instance_uid))
        if dataset.PixelSpacing != pixel_spacing:
            raise ValueError('All slices must have the same pixel spacing: {} != {}'.format(dataset.PixelSpacing, pixel_spacing))
        if dataset.ImageOrientationPatient != image_orientation:
            raise ValueError('All slices must have the same image orientation: {} != {}'.format(dataset.ImageOrientationPatient, image_orientation))
        if dataset.ImagePositionPatient[row_axis] != row_position:
            raise ValueError('All slices must line up along the row axis: {} != {}'.format(dataset.ImagePositionPatient[row_axis], row_position))
        if dataset.ImagePositionPatient[column_axis] != column_position:
            raise ValueError('All slices must line up along the column axis')
        if dataset.Rows != rows or dataset.Columns != columns:
            raise ValueError('All slices must be the same size: ({}, {}) != ({}, {})'.format(dataset.Rows, dataset.Columns, rows, columns))
        slice_positions.append(dataset.ImagePositionPatient[slice_axis])

    _check_for_missing_slices(slice_positions)


def _check_for_missing_slices(slice_positions):
    slice_positions_diffs = numpy.diff(sorted(slice_positions))
    if not numpy.allclose(slice_positions_diffs, slice_positions_diffs[0]):
        # TODO: improve error reporting
        raise ValueError("It seems there are missing slices. Slice spacings: {}".format(slice_positions_diffs))
