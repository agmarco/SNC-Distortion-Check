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
