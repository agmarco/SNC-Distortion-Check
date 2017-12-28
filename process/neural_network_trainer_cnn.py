import argparse
import itertools
import math
import random
import os

import keras
import numpy as np
import scipy
from keras.callbacks import ReduceLROnPlateau
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution3D
from keras.layers.core import SpatialDropout3D
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling3D, GlobalAveragePooling3D
from keras.models import Sequential

from process import file_io, affine
from process.affine import apply_affine
from process.fp_rejector import window_from_ijk
from process.slicer import show_slices

cube_size = 15
cube_size_half = math.floor(cube_size / 2)
input_shape = (cube_size,cube_size,cube_size,1)
num_filters = 16
kernel_shape = (3,3,3)
maxpool_size = pool_size=(2, 2, 2)
nb_classes = 2
batch_size = None
train_to_validation_ratio = 2
phantomName2Datasets = {
    '603':{
        '001': {
            'voxels': 'tmp/001_ct_603A_E3148_ST1.25-voxels.mat',
            'points': 'data/points/001_ct_603A_E3148_ST1.25-golden.mat',
        },
        '006': {
            'voxels': 'tmp/006_mri_603A_UVA_Axial_2ME2SRS5-voxels.mat',
            'points': 'data/points/006_mri_603A_UVA_Axial_2ME2SRS5-golden.mat',
        },
        '011': {
            'voxels': 'tmp/011_mri_603A_arterial_TOF_3d_motsa_ND-voxels.mat',
            'points': 'data/points/011_mri_630A_arterial_TOF_3d_motsa_ND-golden.mat',
        },
    },
    '604':{
        '010': {
            'voxels': 'tmp/010_mri_604_LFV-Phantom_E2632-1-voxels.mat',
            'points': 'data/points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
            'rejected': 'data/rejected_points/010_mri_604_LFV-Phantom_E2632-1-golden.mat',
        },
    },
}
phantomName2Datasets['604 and 603'] = {**phantomName2Datasets['604'], **phantomName2Datasets['603']}


def intersection_generator(cases, train_or_validation, min_offset, offset_mag):
    start_offset = 0 if train_or_validation == "train" else 1
    while True:
        case = random.choice(list(cases.values()))
        voxel_data = file_io.load_voxels(case['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_xyz']
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
        # introduces slight scale invariance
        random_voxel_spacing_augmentation = (np.random.sample(3) * 0.2 - 0.1) + 1
        voxel_spacing *= random_voxel_spacing_augmentation
        golden_points = file_io.load_points(case['points'])['points']

        if 'rejected' in case:
            rejected_points = file_io.load_points(case['rejected'])['points']
            golden_points_set = set([tuple(x) for x in golden_points.T])
            rejected_points_set = set([tuple(x) for x in rejected_points.T])
            golden_points_set -= rejected_points_set
            golden_points = np.array(list(golden_points_set)).T

        point_ijk = apply_affine(xyz_to_ijk, golden_points)
        for point_ijk in point_ijk.T[start_offset::2, :]:
            random_signs = np.array([random.choice([-1,1]), random.choice([-1,1]), random.choice([-1,1])])
            # introduces shift invariance
            point_ijk += random_signs * (np.random.sample(3) * offset_mag + min_offset)
            voxel_window = window_from_ijk(point_ijk, voxels, voxel_spacing)
            if voxel_window is not None:
                assert voxel_window.shape == (cube_size,cube_size,cube_size)
                #zero mean, unit std
                voxel_window = (voxel_window - voxel_window.mean())/(voxel_window.std()+0.00001)
                yield np.expand_dims(voxel_window, axis=3)


def non_intersection_generator(cases, min_dist_from_annotated=5, num_samples=1000):
    while True:
        case = random.choice(list(cases.values()))
        voxel_data = file_io.load_voxels(case['voxels'])
        voxels = voxel_data['voxels']
        ijk_to_xyz = voxel_data['ijk_to_xyz']
        voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
        # introduces slight scale invariance
        random_voxel_spacing_augmentation = (np.random.sample(3) * 0.2 - 0.1) + 1
        voxel_spacing *= random_voxel_spacing_augmentation
        xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
        golden_points = file_io.load_points(case['points'])['points']
        points_ijk = apply_affine(xyz_to_ijk, golden_points)
        random_points = np.array([np.random.randint(cube_size_half, voxels.shape[0]-cube_size_half, num_samples),
                            np.random.randint(cube_size_half, voxels.shape[1]-cube_size_half, num_samples),
                            np.random.randint(cube_size_half, voxels.shape[2]-cube_size_half, num_samples)])
        for point_ijk in random_points.T:
            distances = np.sum(np.abs(points_ijk.T - point_ijk), axis=1)
            if np.min(distances) > min_dist_from_annotated:
                voxel_window = window_from_ijk(point_ijk, voxels, voxel_spacing)
                if voxel_window is not None:
                    assert voxel_window.shape == (cube_size,cube_size,cube_size)
                    #zero mean, unit std
                    voxel_window = (voxel_window - voxel_window.mean())/(voxel_window.std()+0.00001)
                    yield np.expand_dims(voxel_window, axis=3)


def augment_voxels(voxels):
    '''
    axis flips, shifts,
    :param voxels:
    :param annotated_voxels:
    :return:
    '''
    def noise(voxels):
        noise_mag = np.random.sample()
        return voxels + np.random.normal(0, noise_mag, size=voxels.shape)

    def axis_flip(voxels):
        axis_to_flip = random.randint(0, 1)
        return np.flip(voxels, axis_to_flip)

    def rotate(voxels):
        angle = (random.random()*2-1)/8
        voxels = scipy.ndimage.interpolation.rotate(voxels, angle,  mode='reflect', reshape=False)
        return voxels

    def invert(voxels):
        return - voxels

    augmentors_list = [noise, axis_flip, rotate, invert]

    for augmentor in augmentors_list:
        if random.randint(0,1):
            voxels = augmentor(voxels)

    return voxels


def augmented(gen):
    while True:
        yield augment_voxels(next(gen))


def training_generator(cases, train_or_validation):
    centered_intersection_generator = augmented(intersection_generator(cases, train_or_validation, 0, 2))
    shifted_intersection_generator = augmented(intersection_generator(cases, train_or_validation, 3, 5))
    random_window_generator = augmented(non_intersection_generator(cases))
    while True:
        yield next(centered_intersection_generator), [0,1]
        yield next(shifted_intersection_generator), [1,0]
        yield next(random_window_generator), [1,0]


def batch_generator(batch_size, gen):
    while True:
        X, y = zip(*[next(gen) for _ in range(batch_size)])
        yield (np.array(X), np.array(y))


def conv_unit(num_filters, num_convs):
    return list(itertools.chain(*([
        Convolution3D(num_filters, *kernel_shape, border_mode='same'),
        Activation('relu'),
        BatchNormalization(),
        SpatialDropout3D(0.5)
    ] for _ in range(num_convs)), [MaxPooling3D(pool_size)]))


feature_layers = conv_unit(num_filters, 1) + conv_unit(num_filters*2, 1) + conv_unit(num_filters*4, 1)
feature_layers[0] = Convolution3D(num_filters, *kernel_shape, border_mode='same', input_shape=input_shape)
# remove that last maxpool
feature_layers = feature_layers[:-1]
feature_layers = [BatchNormalization(input_shape=input_shape)] + feature_layers

classification_layers = [
    GlobalAveragePooling3D(),
    Dense(128),
    Activation('relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(nb_classes),
    Activation('softmax')
]


def visualize_samples(gen):
    while True:
        voxels_window, answer = next(gen)
        print(answer)
        show_slices(np.squeeze(voxels_window))


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, mode=0o777)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phantom')
    args = parser.parse_args()
    assert args.phantom in phantomName2Datasets
    cases = phantomName2Datasets[args.phantom]
    #visualize_samples(training_generator(cases, "train"))

    # create complete model
    model = Sequential(feature_layers + classification_layers)
    model.summary()

    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    batch_gen_train = batch_generator(512, training_generator(cases, "train"))
    batch_gen_validation = batch_generator(512, training_generator(cases, "validation"))

    weights_dir = os.path.join('weights', args.phantom)
    ensure_dir(weights_dir)
    weights_path = os.path.join(weights_dir, 'weights.{epoch:02d}.h5')
    tensorboard_path = os.path.join('tensorboard', args.phantom)
    ensure_dir(tensorboard_path)

    save_model_callback = keras.callbacks.ModelCheckpoint(weights_path, monitor='val_loss', verbose=3, save_best_only=False, save_weights_only=False, mode='auto', period=5)
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=tensorboard_path, histogram_freq=0, write_graph=False, write_images=False)

    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6)
    model.fit_generator(batch_gen_train, validation_data=batch_gen_validation, nb_val_samples=512, samples_per_epoch=64000, nb_epoch=10000, verbose=1, callbacks=[save_model_callback, tensorboard_callback, reduce_lr], pickle_safe=True, nb_worker=16)
