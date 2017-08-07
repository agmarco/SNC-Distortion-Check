import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imsave

from ..overlay_utilities import add_colorbar
from ..overlay_utilities import (GRADIENT_WIDTH, GRADIENT_LENGTH,
                                 GRADIENT_TOP_IDX, GRADIENT_BOTTOM_IDX)

def test_dicom_overlay():
    test_volume = np.zeros((700,512,512))
    max_value = 20
    test_volume[:,300,300] = max_value
    voxels_with_colorbar = add_colorbar(test_volume)
    new_colorbar_top = voxels_with_colorbar[:, GRADIENT_TOP_IDX, 10:(GRADIENT_WIDTH+10)]
    new_colorbar_bottom = voxels_with_colorbar[:, GRADIENT_BOTTOM_IDX, 10:(GRADIENT_WIDTH+10)]
    assert False not in np.equal(new_colorbar_top, max_value)
    assert False not in np.equal(new_colorbar_bottom, 0)

def visualize_colorbar(slices_array):
    imsave('example_array.png', slices_array[150,:,:])
