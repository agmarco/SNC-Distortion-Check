import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imsave
from ..factories import DicomSeriesFactory

from ..overlay_utilities import add_colorbar
from ..overlay_utilities import (GRADIENT_WIDTH, GRADIENT_LENGTH,
                                 GRADIENT_TOP_IDX, GRADIENT_BOTTOM_IDX)

def test_dicom_overlay():
    max_value = 20
    test_volume = np.ones((700,512,512))*(max_value/2)
    test_volume[:,300,300] = max_value
    max_value_in_xz = np.max(test_volume, 1)
    max_value = np.max(max_value_in_xz, 1)
    voxels_with_colorbar = add_colorbar(test_volume)
    new_colorbar_top = voxels_with_colorbar[:, GRADIENT_TOP_IDX, 10:(GRADIENT_WIDTH+10)]
    expected_colorbar_top = max_value * np.ones((GRADIENT_WIDTH, len(max_value)))
    new_colorbar_bottom = voxels_with_colorbar[:, GRADIENT_BOTTOM_IDX-1, 10:(GRADIENT_WIDTH+10)]
    assert False not in np.equal(new_colorbar_top, expected_colorbar_top.T)
    print(new_colorbar_bottom[new_colorbar_bottom != 0])
    assert False not in np.equal(new_colorbar_bottom, 0)

def visualize_colorbar(slices_array):
    imsave('example_array.png', slices_array[192,:,:])
