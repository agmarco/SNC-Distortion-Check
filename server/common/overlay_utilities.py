import numpy as np
from PIL import Image, ImageDraw

def add_colorbar(slices_array, units='mm'):
    max_val = np.round(np.max(slices_array))
    colorbar = np.zeros((100, 60))
    gradient = np.linspace(max_val, 0, 60) * np.ones((10, 60))
    colorbar[5:65, :10] = gradient.T
    colorbar_img = Image.fromarray(colorbar)
    colorbar_canvas = ImageDraw.Draw(colorbar_img)
    colorbar_canvas.text((10, 0), str(max_val)+units, fill=max_val)
    colorbar_canvas.text((10, 55), "0"+units, fill=max_val)
    colorbar = np.array(colorbar_img) * np.ones((len(slices_array), 100, 60))
    colorbar_area = slices_array[:, :100, :60]
    colorbar_area[colorbar != 0] = colorbar[colorbar != 0]
    return slices_array
