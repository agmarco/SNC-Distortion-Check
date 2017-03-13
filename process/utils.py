import logging
import math

import numpy as np
from scipy.ndimage import filters


logger = logging.getLogger(__name__)
import sys; logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# TODO: handle this in a "ConsoleApp" class


def invert(data):
    return np.max(data) - data


def unsharp_mask(image, sigma, weight=0.25):
    '''
    There are many ways to define an "unsharp" mask,
    however this is a pretty standard one.

    NOTE: there is no "threshold" here.  It would be
    easy to add, however.  See:

        http://www.damiensymonds.net/tut_usm.html

    for details on how it is typically implemented.
    '''
    blurred = filters.gaussian_filter(image, sigma)
    return image - weight*blurred


def decimate(image, factor):
    '''
    Decrease the size of an image by the specified factor along each dimension.

    Requires that each dimension of the image be divisible by said factors.

    A simple "averaging" is performed when performing the down sampling.
    '''
    assert all(d % factor == 0 for d in image.shape)

    new_shape = [d//factor for d in image.shape]
    decimated = np.zeros(new_shape, dtype=image.dtype)
    ni, nj, nk = new_shape
    for i in range(ni):
        for j in range(nj):
            for k in range(nk):
                decimated[i, j, k] = np.mean(image[
                    i*factor:(i + 1)*factor,
                    j*factor:(j + 1)*factor,
                    k*factor:(k + 1)*factor
                ])

    return decimated


def split_file_variable_arg(arg, default_variable):
    '''
    Some commandline tools have arguments that specify a file and a variable
    from that file to read.  This utility splits the arguments into their
    component parts.
    '''
    parts = arg.split(':')
    if len(parts) == 1:
        return parts[0], default_variable
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        raise ValueError("Invalid 'file:variable' argument.")


def print_optimization_result(result):
    logger.info('Optimization completed in {} iterations'.format(result.nit))
    logger.info('Objective function evaluated {} times'.format(result.nfev))
    logger.info('Cause of termination: {}'.format(result.message))


def print_xyztpx(xyztpx):
    x, y, z, theta, phi, xi = xyztpx
    r = math.sqrt(x*x + y*y + z*z)

    translation_msg = 'Translation of {:06.4f}mm ({:06.4f}mm, {:06.4f}mm, {:06.4f}mm)'
    logger.info(translation_msg.format(r, x, y, z))

    rotation_msg = 'Rotation of {:06.4f}°, {:06.4f}°, {:06.4f}°'
    logger.info(rotation_msg.format(
        math.degrees(theta),
        math.degrees(phi),
        math.degrees(xi)
    ))