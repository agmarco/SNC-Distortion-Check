from copy import copy

import numpy as np

from ..overlay_utilities import add_colorbar

COLORBAR_TOP_IDX = 5
COLORBAR_BOTTOM_IDX = 64
COLORBAR_WIDTH = 10
COLORBAR_LENGTH = 60

def test_dicom_overlay():
    test_volume = np.zeros((512,512,700))
    max_value = 20
    test_volume[300,300,300] = max_value
    voxels_with_colorbar = add_colorbar(test_volume)
    new_colorbar_top = voxels_with_colorbar[:, COLORBAR_TOP_IDX, :COLORBAR_WIDTH]
    new_colorbar_bottom = voxels_with_colorbar[:, COLORBAR_BOTTOM_IDX, :COLORBAR_WIDTH]
    assert False not in np.equal(new_colorbar_top, max_value)
    assert False not in np.equal(new_colorbar_bottom, 0)
