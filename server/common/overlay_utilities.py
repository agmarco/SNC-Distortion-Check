import numpy as np
from PIL import Image, ImageDraw

GRADIENT_WIDTH = 10
GRADIENT_LENGTH = 90
GRADIENT_TOP_IDX = 5
GRADIENT_BOTTOM_IDX = 95

def add_colorbar_to_slice(voxel_slice, max_distortion, units='mm'):
    max_val = np.round(np.max(voxel_slice), decimals=1)
    colorbar = np.zeros((100, 60))
    gradient = np.linspace(max_val, 0, GRADIENT_LENGTH) * np.ones((GRADIENT_WIDTH, GRADIENT_LENGTH))
    colorbar[5:(GRADIENT_LENGTH+5), 10:(GRADIENT_WIDTH+10)] = gradient.T

    colorbar_img = Image.fromarray(colorbar)
    colorbar_canvas = ImageDraw.Draw(colorbar_img)
    add_unit_labels(colorbar_canvas, max_val, max_distortion, units)
    add_gradient_ticks(colorbar_canvas, max_val)

    colorbar = np.array(colorbar_img) * np.ones((100, 60))
    colorbar_area = voxel_slice[:100, :60]
    colorbar_area[colorbar != 0] = colorbar[colorbar != 0]
    colorbar_area[GRADIENT_BOTTOM_IDX-1, 10:(GRADIENT_WIDTH+10)] = np.zeros(GRADIENT_WIDTH)
    return voxel_slice

def add_unit_labels(canvas, max_val, max_distortion, units='mm'):
    canvas.text((21, 0), str(max_distortion)+units, fill=max_val)
    canvas.text((21, 85), "0"+units, fill=max_val)
    return canvas

def add_gradient_ticks(canvas, max_val):
    tick_indices = np.linspace(GRADIENT_TOP_IDX, GRADIENT_BOTTOM_IDX-1, 7)
    for idx, coord in enumerate(tick_indices):
        if idx == 0 or idx == len(tick_indices)-1:
            tick_coords = (1, coord, 7, coord)
        else:
            tick_coords = (3, coord, 7, coord)
        canvas.line(tick_coords, fill=max_val)
    canvas.line((7, tick_indices[0], 7, tick_indices[-1]), fill=max_val)
    return canvas
