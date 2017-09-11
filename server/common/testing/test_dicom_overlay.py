import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imsave
from ..factories import DicomSeriesFactory

from ..overlay_utilities import add_colorbar_to_slice
from ..overlay_utilities import (GRADIENT_WIDTH, GRADIENT_LENGTH,
                                 GRADIENT_TOP_IDX, GRADIENT_BOTTOM_IDX)

def test_dicom_overlay():
    max_value = 20
    test_volume = np.ones((700,512,512))*(max_value/2)
    test_volume[:,300,300] = max_value
    max_value_in_xz = np.max(test_volume, 1)
    max_value = np.max(max_value_in_xz, 1) 
    for slice_arr in test_volume:
        slice_arr = add_colorbar_to_slice(slice_arr, np.max(slice_arr))
    new_colorbar_top = test_volume[:, GRADIENT_TOP_IDX, 10:(GRADIENT_WIDTH+10)]
    expected_colorbar_top = max_value * np.ones((GRADIENT_WIDTH, len(max_value)))
    new_colorbar_bottom = test_volume[:, GRADIENT_BOTTOM_IDX-1, 10:(GRADIENT_WIDTH+10)]
    assert False not in np.equal(new_colorbar_top, expected_colorbar_top.T)
    assert False not in np.equal(new_colorbar_bottom, 0)

def test_dicom_overlay_ticks_aligned():
    max_value = 20
    test_volume = np.ones((700,512,512))*(max_value/2)
    test_volume[:,300,300] = max_value
    for slice_arr in test_volume:
        slice_arr = add_colorbar_to_slice(slice_arr, max_value)
    top_tick = test_volume[:, GRADIENT_TOP_IDX, 1:8]
    bottom_tick = test_volume[:, GRADIENT_BOTTOM_IDX-1, 1:8]
    assert False not in np.equal(top_tick, max_value)
    assert False not in np.equal(bottom_tick, max_value)

def test_dicom_overlay_not_added_when_slice_too_small():
    test_slice = np.random.rand(100, 140)
    original_slice = test_slice.copy()
    max_value = 20
    add_colorbar_to_slice(test_slice, max_value)

    assert np.array_equal(original_slice, test_slice)

def visualize_colorbar(slices_array):
    imsave('example_array.png', slices_array[192,:,:])
