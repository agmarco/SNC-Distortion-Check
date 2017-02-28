'''
Make a mocked PET overlay from the 1540 phantom
'''
import argparse
import os
import numpy as np
import dicom
from dicom.UID import generate_uid

def distance_from(shape, center):
    x_grid, y_grid = np.mgrid[0:shape[0], 0:shape[1]]
    x_grid = x_grid - center[0]
    y_grid = y_grid - center[1]
    d_grid = np.sqrt(x_grid**2 + y_grid**2)
    return d_grid

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dicoms', nargs='*')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    new_series_uid = generate_uid()

    for dcm in args.input_dicoms:
        try:
            ds = dicom.read_file(dcm)
        except Exception as e:
            print(e)
            pass

        ds.SOPInstanceUID = generate_uid()
        ds.SeriesInstanceUID = new_series_uid
        shape = (ds.Rows, ds.Columns)
        pixels = np.zeros(shape, dtype=np.uint16)
        if ds.InstanceNumber <= 114 and ds.InstanceNumber >=22:
            d_grid = distance_from(shape, (257, 301))
            distort_grid = np.fmax(0, (d_grid - 50) * 2)
            start = slice(135,375)
            stop = slice(148,410)
            slice_from_mid = abs(ds.InstanceNumber - 68)
            dist_scale = (slice_from_mid+5) / 50
            distort_grid *= dist_scale
            pixels[start, stop] = distort_grid[start, stop].astype(np.uint16)
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 1
        ds.PixelData = pixels.T.tobytes()
        ds.Modality = 'PT'
        dicom.write_file(os.path.join(args.output_dir, ds.SOPInstanceUID + '.dcm'), ds)


