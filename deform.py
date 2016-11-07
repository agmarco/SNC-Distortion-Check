import numpy as np
from scipy.interpolate import griddata
from scipy.interpolate.interpolate import RegularGridInterpolator


def deform(X_d, Y_d, Z_d, V_d, X, Y, Z, V):
    '''

    :param X_d: X coordinates of distortion grid produced by meshgrid
    :param Y_d: Y coordinates of distortion grid produced by meshgrid
    :param Z_d: Z coordinates of distortion grid produced by meshgrid
    :param V_d: distortion vectors of same shape of X_d, Y_d, Z_d representing the distortion vector
    :param X: X coordinates of image grid produced by meshgrid
    :param Y: Y coordinates of image grid produced by meshgrid
    :param Z: Z coordinates of image grid produced by meshgrid
    :param V: image value of same shape as X, Y, and Z
    '''
    XYZ = np.array([X.ravel(), Y.ravel(), Z.ravel()]).T
    # interpolate the image coordinates onto the distortion map
    interpolator = RegularGridInterpolator((x, y, z,), V_d)
    V_d_in = interpolator(XYZ)
    # apply the distortion
    displaced_XYZ = XYZ + V_d_in
    # regrid the distorted image on a new grid
    x_min, y_min, z_min = np.min(displaced_XYZ, axis=0)
    x_max, y_max, z_max = np.max(displaced_XYZ, axis=0)
    # TODO: figure out best way to calculate the best grid resolution
    grid_resolution = 0.1
    v_reshape = V.reshape(len(XYZ), -1)
    t = tuple(np.meshgrid(np.arange(x_min, x_max, grid_resolution), np.arange(y_min, y_max, grid_resolution), np.arange(z_min, z_max, grid_resolution)))
    gridded = griddata(displaced_XYZ, v_reshape, t, method='nearest')
    return gridded

if __name__ == '__main__':
    def generate_cube(size, x0=0):
        points = []
        for x in range(-size, size):
            for y in range(-size, size):
                for z in range(-size, size):
                    points.append((x, y, z))
        return np.array(points).T

    # generate dilation distortion
    x, y, z = np.arange(-1, 1, 0.1), np.arange(-1, 1, 0.1), np.arange(-1, 1, 0.1)
    X_d, Y_d, Z_d = np.meshgrid(x, y, z, indexing='ij')
    V_d = np.stack([X_d*np.abs(X_d), Y_d*np.abs(Y_d), Z_d*np.abs(Z_d)], axis=3)

    X, Y, Z = np.meshgrid(np.arange(-2, 2, 0.2), np.arange(-2, 2, 0.2), np.arange(-2, 2, 0.2))

    V = np.stack([X, Y, Z], axis=3)
    print(deform(X_d, Y_d, Z_d, V_d, X, Y, Z, V).shape)

