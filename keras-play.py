import keras
import random

import math
import numpy as np
import itertools


import file_io
from keras.layers.convolutional import Convolution3D
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling3D

from affine import apply_affine
from slicer import show_slices
from testing.distort_voxel import affine_transform_func, chain_transformers, deform_func, affine_point

from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Activation, Flatten
cube_size = 15
cube_size_half = math.floor(cube_size / 2)
input_shape = (cube_size,cube_size,cube_size,1)
num_filters = 32
kernel_shape = (3,3,3)
maxpool_size = pool_size=(2, 2, 2)
nb_classes = 2
batch_size = None
train_to_validation_ratio = 2

cases = {
    '006': {
        'voxels': 'tmp/006_mri_603A_UVA_Axial_2ME2SRS5-voxels.mat',
        'points': 'data/points/006_mri_603A_UVA_Axial_2ME2SRS5-golden.mat',
    },
    '010': {
        'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
        'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
    },
    '011': {
        'voxels': 'tmp/011_mri_603A_arterial_TOF_3d_motsa_ND-voxels.mat',
        'points': 'data/points/011_mri_630A_arterial_TOF_3d_motsa_ND-golden.mat',
    },
    '001': {
        'voxels': 'tmp/001_ct_603A_E3148_ST1.25-voxels.mat',
        'points': 'data/points/001_ct_603A_E3148_ST1.25-golden.mat',
    },
    '012': {
        'voxels': 'tmp/xxx_ct_1540_ST075-120kVp-25mA-voxels.mat',
        'points': 'data/points/012_ct_1540_ST075-120kVp-25mA-golden.mat',
    },
}


def real_intersection_generator(train_or_validation, min_offset, offset_mag):
    start_offset = 0 if train_or_validation == "train" else 1
    while True:
        case = random.choice(list(cases.values()))
        voxel_data = file_io.load_voxels(case['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        golden_points = file_io.load_points(case['points'])['points']
        point_ijk = apply_affine(xyz_to_ijk, golden_points)
        for point_ijk in point_ijk.T[start_offset::2, :]:
            point_ijk = point_ijk + random.choice([1, -1]) * (np.random.sample(3) * offset_mag + min_offset)
            point_ijk = np.round(point_ijk)
            i, j, k = point_ijk.astype(int)
            voxel_window = voxels[i-cube_size_half:i+cube_size_half+1, j-cube_size_half:j+cube_size_half+1, k-cube_size_half:k+cube_size_half+1]
            if voxel_window.shape == (cube_size,cube_size,cube_size):
                yield np.expand_dims(voxel_window, axis=3)

def non_intersection_generator(min_dist_from_annoted=5, num_samples=1000):
    while True:
        case = random.choice(list(cases.values()))
        voxel_data = file_io.load_voxels(case['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        golden_points = file_io.load_points(case['points'])['points']
        points_ijk = apply_affine(xyz_to_ijk, golden_points)
        random_points = np.array([   np.random.randint(cube_size_half, voxels.shape[0]-cube_size_half, num_samples),
                            np.random.randint(cube_size_half, voxels.shape[1]-cube_size_half, num_samples),
                            np.random.randint(cube_size_half, voxels.shape[2]-cube_size_half, num_samples)])
        for point_ijk in random_points.T:
            distances = np.sum(np.abs(points_ijk.T - point_ijk), axis=1)
            if np.min(distances) > min_dist_from_annoted:
                i, j, k = point_ijk
                voxel_window = voxels[i-cube_size_half:i+cube_size_half+1, j-cube_size_half:j+cube_size_half+1, k-cube_size_half:k+cube_size_half+1]
                if voxel_window.shape == (cube_size,cube_size,cube_size):
                    yield np.expand_dims(voxel_window, axis=3)


intersection_augmenters = [
    lambda X: X*np.random.random_sample() + np.random.random_sample()*np.mean(X),
    # lambda X: X*np.random.normal(0, np.random.sample()*0.1, X.shape),
    lambda X: np.max(X) - X,
    # rotation_augmentor,
    lambda X: X,
    lambda X: np.flip(X, random.randint(0,2)),
    lambda X: np.swapaxes(X, random.randint(0,2), random.randint(0,2))
]
def augmented(gen):
    while True:
        augmenter = random.choice(intersection_augmenters)
        yield augmenter(next(gen))

def training_generator(train_or_validation):
    intersection_generator = augmented(real_intersection_generator(train_or_validation, 0, 2))
    shifted_intersection_generator = augmented(real_intersection_generator(train_or_validation, 3, 5))
    random_window_generator = augmented(non_intersection_generator())
    while True:
        yield next(intersection_generator), [0,1]
        yield next(shifted_intersection_generator), [1,0]
        yield next(random_window_generator), [1,0]


def show_me_some_stuff(gen):
    while True:
        kernel = next(gen)
        show_slices(np.squeeze(kernel))

# show_me_some_stuff(intersection_generator("train"))
# show_me_some_stuff(real_intersection_generator("train", 0, 2))
# show_me_some_stuff(real_intersection_generator("train", 3, 5))
# show_me_some_stuff(non_intersection_generator())


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


feature_layers = conv_unit(num_filters, 2) + conv_unit(num_filters*2, 3) + conv_unit(num_filters*4, 3)
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
    Dropout(0.2),
    Dense(nb_classes),
    Activation('softmax')
]

# create complete model
model = Sequential(feature_layers + classification_layers)
model.summary()

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
batch_gen_train = batch_generator(512, training_generator("train"))
batch_gen_validation = batch_generator(512, training_generator("validation"))

# model = load_model('weights/weights.1599.h5')
save_model_callback = keras.callbacks.ModelCheckpoint('weights/weights.{epoch:02d}.h5', monitor='accuracy', verbose=3, save_best_only=False, save_weights_only=False, mode='auto', period=10)
model.fit_generator(batch_gen_train, validation_data=batch_gen_validation, nb_val_samples=512, samples_per_epoch=64000, nb_epoch=10000, verbose=1, callbacks=[save_model_callback], pickle_safe=True, nb_worker=8)
# import pydevd;pydevd.settrace('localhost', port=63421, stdoutToServer=True, stderrToServer=True)
