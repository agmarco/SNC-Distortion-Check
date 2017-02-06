
from tensorflow.python.client import device_lib

from affine import apply_affine


def get_available_gpus():
    local_device_protos = device_lib.list_local_devices()
    return [x.name for x in local_device_protos]

print(get_available_gpus())

import random

import math
import numpy as np
import datetime
import itertools

from scipy.ndimage.interpolation import geometric_transform
from scipy.signal import fftconvolve, gaussian
from tensorflow.contrib.layers.python.layers.layers import one_hot_encoding

import file_io
from keras.layers.convolutional import Convolution3D
from keras.layers.core import SpatialDropout3D
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling3D
from keras.preprocessing.text import one_hot
from kernels import cylindrical_grid_intersection, sphere
from slicer import show_slices
from testing.distort_voxel import affine_transform_func, chain_transformers, deform_func, affine_point
from utils import decimate

np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution2D, MaxPooling2D
from keras.utils import np_utils
from keras import backend as K
cube_size = 13
cube_size_half = math.floor(cube_size / 2)
input_shape = (cube_size,cube_size,cube_size,1)
num_filters = 24
kernel_shape = (3,3,3)
maxpool_size = pool_size=(2, 2, 2)
nb_classes = 2
batch_size = None

def real_intersection_generator():
    voxel_data = file_io.load_voxels('tmp/xxx_ct_1540_ST075-120kVp-25mA-voxels.mat')
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
    xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
    golden_points = file_io.load_points('data/points/012_ct_1540_ST075-120kVp-25mA-golden.mat')['points']
    point_xyz = random.choice(golden_points.T)
    point_ijk = affine_point(xyz_to_ijk, point_xyz.T)
    point_ijk = np.round(point_ijk)
    i, j, k = point_ijk.astype(int)
    voxel_window = voxels[i-cube_size_half:i+cube_size_half+1, j-cube_size_half:j+cube_size_half+1, k-cube_size_half:k+cube_size_half+1]
    return np.expand_dims(voxel_window, axis=3)

def real_confusion_generator():
    voxel_data = file_io.load_voxels('tmp/xxx_ct_1540_ST075-120kVp-25mA-voxels.mat')
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
    xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
    golden_points = file_io.load_points('data/points/012_ct_1540_ST075-120kVp-25mA-golden.mat')['points']
    point_xyz = random.choice(golden_points.T)
    point_ijk = affine_point(xyz_to_ijk, point_xyz.T)
    point_ijk = point_ijk + random.choice([1, -1]) * (np.random.sample(3)*10 + 1)
    point_ijk = np.round(point_ijk)
    i, j, k = point_ijk.astype(int)
    voxel_window = voxels[i-cube_size_half:i+cube_size_half+1, j-cube_size_half:j+cube_size_half+1, k-cube_size_half:k+cube_size_half+1]
    return np.expand_dims(voxel_window, axis=3)


def distort_voxels(voxels, distortion_factor):
    to_pad = 5 # so that transforms will be valid on edges.
    center = math.floor((cube_size+2*to_pad)/2)
    voxels = voxels.squeeze()
    voxels = np.pad(voxels, ((to_pad, to_pad), (to_pad, to_pad), (to_pad, to_pad)), 'edge')
    to_xyz_func, from_xyz_func = affine_transform_func(-center, -center, -center, 0, 0, 0)
    distort_func, undistort_func = deform_func(distortion_factor)
    distort_func = chain_transformers([to_xyz_func, undistort_func, from_xyz_func])
    voxels_distorted = geometric_transform(voxels, distort_func)
    output = np.expand_dims(voxels_distorted[to_pad:-to_pad, to_pad:-to_pad, to_pad:-to_pad], axis=3)
    assert output.shape == input_shape
    return output


def generate_kernel(radius=3, spacing=cube_size):
    kernel = cylindrical_grid_intersection(
            pixel_spacing=(1, 1, 1),
            radius=radius,
            spacing=spacing
    )
    kernel = np.expand_dims(kernel, axis=3)
    assert kernel.shape == input_shape
    return kernel

intersection_bank = [generate_kernel(radius=i) for i in np.linspace(1, 2.5, 10)]
# intersection_bank.extend([distort_voxels(voxels, 3e-2) for voxels in intersection_bank])



def generate_sphere():
    return np.expand_dims(sphere(pixel_spacing=(1,1,1), radius=cube_size_half), axis=3)

def generate_cylinder():
    intersection = random.choice(intersection_bank)
    return np.stack([intersection[0, :, :, :]]*cube_size, axis=random.randint(0,2))

def generate_shifted_intersection():
    intersection = random.choice(intersection_bank)
    return np.roll(intersection, random.randint(1,3), axis=random.randint(0,2))

def generate_shifted_cylinder():
    cylinder = generate_cylinder()
    return np.roll(cylinder, random.randint(1,2), axis=random.randint(0,2))

def transform_voxels(voxels, x, y, z, theta, pi, xhi):
    to_pad = 5 # so that transforms will be valid on edges.
    center = math.floor((cube_size+2*to_pad)/2)
    voxels = voxels.squeeze()
    voxels = np.pad(voxels, ((to_pad, to_pad), (to_pad, to_pad), (to_pad, to_pad)), 'edge')
    to_xyz_func, from_xyz_func = affine_transform_func(-center, -center, -center, 0, 0, 0)
    theta, pi, xhi = np.deg2rad(theta), np.deg2rad(pi), np.deg2rad(xhi)
    distort_func, undistort_func = affine_transform_func(x, y, z, theta, pi, xhi)
    distort_func = chain_transformers([to_xyz_func, distort_func, from_xyz_func])
    voxels_distorted = geometric_transform(voxels, distort_func)
    output = np.expand_dims(voxels_distorted[to_pad:-to_pad, to_pad:-to_pad, to_pad:-to_pad], axis=3)
    assert output.shape == input_shape
    return output

# def gaussian_blurrer(voxels):
#     kernel = np.outer(gaussian(3, 1), gaussian(3, 1), gaussian(3, 1))
#     import pydevd;pydevd.settrace('localhost', port=63421, stdoutToServer=True, stderrToServer=True)
#     return fftconvolve(voxels, kernel, mode='same')
#
# show_slices(gaussian_blurrer(intersection_bank[0]).squeeze())
#

def rotation_augmentor(voxels):
    '''rotates the voxels by a random amount in all 3 axis.'''
    max_rot = 8
    return transform_voxels(voxels, 0, 0, 0, np.random.sample() * max_rot,  np.random.sample() * max_rot,  np.random.sample() * max_rot,)

def rotation_translation_augmentor(voxels):
    '''rotates the voxels by a random amount in all 3 axis.'''
    max_rot = 4
    min_trans = 0.5
    max_trans = 5
    trans_mag = max_trans-min_trans
    return transform_voxels(voxels, np.random.sample()*trans_mag+min_trans,  np.random.sample()*trans_mag+min_trans,  np.random.sample()*trans_mag+min_trans,
                            np.random.sample() * max_rot,  np.random.sample() * max_rot,  np.random.sample() * max_rot)


def generate_shifted_rotated_intersection():
    intersection = random.choice(intersection_bank)
    return rotation_translation_augmentor(intersection)

intersection_augmenters = [
    lambda X: X*np.random.random_sample(),
    lambda X: X+np.random.random_sample(),
    lambda X: X*np.random.normal(0, np.random.sample()*0.1, X.shape),
    lambda X: np.max(X) - X,
    rotation_augmentor,
    lambda X: X
]

confusion_generators = [
    # # lambda: np.random.uniform(0, 1, input_shape),
    #  lambda: np.random.normal(0, np.random.sample(), input_shape),
    # # lambda: np.ones(input_shape) * np.random.sample(),
    # generate_sphere,
    # generate_cylinder,
    # generate_shifted_intersection,
    # generate_shifted_rotated_intersection,
    # generate_shifted_cylinder,
    real_confusion_generator
]

def training_generator():
    rand = random.Random(0)
    kern_gen = intersection_generator()
    confusion_gen = confusion_generator()

    while True:
        if rand.randint(0,1) == 0:
            yield next(kern_gen), [0,1]
        else:
            yield next(confusion_gen), [1,0]

def intersection_generator():
    while True:
        kernel = real_intersection_generator()
        augmenter = random.choice(intersection_augmenters)
        kernel = augmenter(kernel)
        yield kernel

def confusion_generator():
    while True:
        yield random.choice(confusion_generators)()

def show_me_some_stuff(gen):
    for i in range(10):
        kernel = next(gen)
        show_slices(np.squeeze(kernel))

# show_me_some_stuff(confusion_generator())
# show_me_some_stuff(intersection_generator())


def batch_generator(batch_size, gen):
    while True:
        X, y = zip(*[next(gen) for _ in range(batch_size)])
        yield (np.array(X), np.array(y))


def conv_unit(num_filters, num_convs):
    return list(itertools.chain(*([
        Convolution3D(num_filters, *kernel_shape, border_mode='same'),
        Activation('relu'),
        BatchNormalization(),
        Dropout(0.2)
    ] for _ in range(num_convs)), [MaxPooling3D(pool_size)]))


feature_layers = conv_unit(num_filters, 2) + conv_unit(num_filters*2, 3) + conv_unit(num_filters*4, 3) + conv_unit(num_filters*4, 3)
feature_layers[0] = Convolution3D(num_filters, *kernel_shape, border_mode='same', input_shape=input_shape)
# remove that last maxpool
feature_layers = feature_layers[:-1]


classification_layers = [
    Flatten(),
    Dense(256),
    Activation('relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(256),
    Activation('relu'),
    BatchNormalization(),
    Dense(nb_classes),
    Activation('softmax')
]

# create complete model
model = Sequential(feature_layers + classification_layers)
model.summary()

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
batch_gen = batch_generator(32, training_generator())
model.fit_generator(batch_gen, samples_per_epoch=320, nb_epoch=1000, verbose=1)
model.save('keras-test.h5')
# import pydevd;pydevd.settrace('localhost', port=63421, stdoutToServer=True, stderrToServer=True)