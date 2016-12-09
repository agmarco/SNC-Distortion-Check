import numpy as np
from scipy.ndimage import filters


def invert(data):
    return 2*np.mean(data) - data


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
