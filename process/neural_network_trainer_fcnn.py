"""
This module is to train a fully convolutional image segmentation model based on the u-net architecture. Though this
has yielded some promising results it requires too much cpu time to run predictions and hence cannot be deployed
unless a gpu is present on the server.
"""


import argparse
import itertools
import math
import random
from functools import partial, lru_cache
import os
import glob
import keras
import numpy as np
import scipy
from keras.engine.topology import Input, merge
from keras.engine.training import Model
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution3D, UpSampling3D
from keras.layers.core import SpatialDropout3D
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling3D
from keras.models import Sequential
from keras.optimizers import Adam
from keras import backend as K

from process import file_io, affine
from process.affine import apply_affine

from process.kernels import sphere
from process.slicer import show_slices

window_shape = np.array((128, 128, 32))
cube_size_half = window_shape // 2
intersection_radius = 3
input_shape = (*window_shape, 1)
num_filters = 32
kernel_shape = (3,3,3)
maxpool_size = pool_size=(2, 2, 2)
nb_classes = 2
batch_size = None

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
    # '012': {
    #     'voxels': 'tmp/xxx_ct_1540_ST075-120kVp-25mA-voxels.mat',
    #     'points': 'data/points/012_ct_1540_ST075-120kVp-25mA-golden.mat',
    # },
}
test_cases = {
    'tmp/yyy_mri_603A_t2_ci3d_tra_iso_0.8mm_ND-voxels.mat',
    'tmp/yyy_mri_603A_t2_ci3d_tra_iso_0.8mm-voxels.mat'
}
def annotation_from_points_mask(voxels, ijk_to_xyz, points_ijk):
    '''
    Returns a binary mask with spheres overlaid over grid intersection points
    '''
    voxel_spacing = affine.voxel_spacing(ijk_to_xyz)
    sphere_kernel = sphere(voxel_spacing, radius=intersection_radius, upsample=1)
    sphere_kernel = sphere_kernel > 0
    sphere_kernel_shape = np.array(sphere_kernel.shape)
    sphere_kernel_shape_half = sphere_kernel_shape // 2
    annotations_mask = np.zeros_like(voxels)
    points_ijk = np.round(points_ijk).astype(int)
    for point_ijk in points_ijk.T:
        try:
            annotations_mask[
                point_ijk[0]-sphere_kernel_shape_half[0]:point_ijk[0]+sphere_kernel_shape_half[0]+1,
                point_ijk[1]-sphere_kernel_shape_half[1]:point_ijk[1]+sphere_kernel_shape_half[1]+1,
                point_ijk[2]-sphere_kernel_shape_half[2]:point_ijk[2]+sphere_kernel_shape_half[2]+1,
            ] = sphere_kernel
        except ValueError:
            print("Warning, could not broadcast, point {} with original voxel shape {}".format(point_ijk, voxels.shape))
    return annotations_mask

@lru_cache(maxsize=10)
def load_case(case_voxels, case_points):
    print("loading {}".format(case_voxels))
    voxel_data = file_io.load_voxels(case_voxels)
    voxels = voxel_data['voxels']
    ijk_to_xyz = voxel_data['ijk_to_patient_xyz_transform']
    xyz_to_ijk = np.linalg.inv(ijk_to_xyz)
    golden_points = file_io.load_points(case_points)['points']
    points_ijk = apply_affine(xyz_to_ijk, golden_points)
    points_ijk = np.round(points_ijk).astype(int)
    annotations_mask = annotation_from_points_mask(voxels, ijk_to_xyz, points_ijk)
    return voxels, annotations_mask, points_ijk

def real_intersection_generator(train_or_validation, ranodm_offset_mag):
    start_offset = 0 if train_or_validation == "train" else 1
    while True:
        case = random.choice(list(cases.values()))
        voxels, annotations_mask, points_ijk = load_case(case['voxels'], case['points'])
        point_ijk = random.choice(points_ijk.T)
        point_ijk = point_ijk + (np.random.sample(3) * ranodm_offset_mag*2 - ranodm_offset_mag)
        i, j, k = np.round(point_ijk).astype(int)
        window_slice_tup = (
            slice(i-cube_size_half[0], i+cube_size_half[0]),
            slice(j-cube_size_half[1], j+cube_size_half[1]),
            slice(k-cube_size_half[2], k+cube_size_half[2])
        )
        voxel_window = voxels[window_slice_tup]
        if all(voxel_window.shape == window_shape):
            annotations_window = annotations_mask[window_slice_tup]
            assert voxel_window.shape == annotations_window.shape
            yield np.expand_dims(voxel_window, axis=3), np.expand_dims(annotations_window, axis=3)

def augment_data(voxels, annotated_voxels):
    '''
    axis flips, shifts,
    :param voxels:
    :param annotated_voxels:
    :return:
    '''
    assert voxels.shape == annotated_voxels.shape
    def noise(voxels, annotations):
        noise_mag = random.randint(0, 40)
        return voxels + np.random.normal(0, noise_mag, size=voxels.shape), annotations

    def slight_contrast_variation(voxels, annotations):
        magnitude = random.randint(-20, 20)
        return voxels + magnitude, annotations

    def axis_flip(voxels, annotations):
        axis_to_flip = random.randint(0, 1)
        return np.flip(voxels, axis_to_flip), np.flip(annotations, axis_to_flip)

    def roll(voxels, annotations):
        axis_to_roll = 0
        magnitude = random.randint(-5, 5)
        voxels, annotations = np.roll(voxels, magnitude, axis=axis_to_roll), np.roll(annotations, magnitude, axis=axis_to_roll)
        return voxels, annotations

    def rotate(voxels, annotations):
        angle = (random.random()*2-1)/8
        voxels = scipy.ndimage.interpolation.rotate(voxels, angle,  mode='reflect', reshape=False)
        annotations = scipy.ndimage.interpolation.rotate(annotations, angle, mode='reflect', reshape=False)
        return voxels, annotations

    augmentors_list = [noise, slight_contrast_variation, axis_flip, roll, rotate]

    for augmentor in augmentors_list:
        if random.randint(0,1):
            voxels, annotated_voxels = augmentor(voxels, annotated_voxels)

    return voxels, annotated_voxels

def augmented(gen):
    while True:
        yield augment_data(*next(gen))

def training_generator(train_or_validation):
    intersection_generator = augmented(real_intersection_generator(train_or_validation, 5))
    while True:
        yield next(intersection_generator)

def batch_generator(batch_size, gen):
    while True:
        X, y = zip(*[next(gen) for _ in range(batch_size)])
        yield (np.array(X), np.array(y))

def w_binary_crossentropy(y_true, y_pred, true_weight=50, false_weight=1):
    b_entropy = K.binary_crossentropy(y_pred, y_true)
    y_false = 1-y_true
    return K.mean(b_entropy * y_true * true_weight + b_entropy * y_false * false_weight, axis=-1)

def TPF(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return intersection / (K.sum(y_true_f)+0.0001)

def NumPositives(y_true, y_pred):
    return K.sum(K.flatten(y_true))

def NumNegatives(y_true, y_pred):
    return K.sum(K.flatten(1-y_true))

def PositiveRatio(y_true, y_pred):
    return NumPositives(y_true, y_pred) / NumNegatives(y_true, y_pred)

def TNF(y_true, y_pred):
    y_true_f = K.flatten(1-y_true)
    y_pred_f = K.flatten(1-y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return intersection / K.sum(y_true_f)

def dice_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + 1) / (K.sum(y_true_f) + K.sum(y_pred_f) + 1)


def add_norm_drop(conv, batch_norm=True, spatial_dropout=0.5):
    if batch_norm:
        conv = BatchNormalization()(conv)
    if spatial_dropout:
        conv = SpatialDropout3D(spatial_dropout)(conv)
    return conv

def convolution_pair(num_filters, num_convs, conv_size, pool_size, inputs, batch_norm=True, spatial_dropout=0.5):
    """"""
    add_norm_drop_func = partial(add_norm_drop, batch_norm=batch_norm, spatial_dropout=spatial_dropout)
    contraction_conv = inputs
    for _ in range(num_convs):
        contraction_conv = Convolution3D(num_filters, conv_size,conv_size,conv_size, activation='relu', border_mode='same')(contraction_conv)
        contraction_conv = add_norm_drop_func(contraction_conv)

    pool = Convolution3D(num_filters, conv_size,conv_size,conv_size, subsample=pool_size, activation='relu', border_mode='same')(contraction_conv)
    pool = add_norm_drop_func(pool)

    def expansion_layers(expansion_input, unpool_size=pool_size):
        upsample = UpSampling3D(size=unpool_size)(expansion_input)
        upsample = merge([upsample, contraction_conv], mode='concat', concat_axis=4)
        expansion_conv = upsample
        for _ in range(num_convs):
            expansion_conv = Convolution3D(num_filters, conv_size,conv_size,conv_size, activation='relu', border_mode='same')(expansion_conv)
            expansion_conv = add_norm_drop_func(expansion_conv)
        return expansion_conv

    return pool, expansion_layers


def unet1(input_shape=input_shape, base_size=8):
    inputs = Input(input_shape)
    contraction, expansion1 = convolution_pair(base_size * 1, num_convs=2, conv_size=5, pool_size=(2, 2, 2), inputs=inputs, spatial_dropout=0.1)
    contraction, expansion2 = convolution_pair(base_size * 2, num_convs=2, conv_size=5, pool_size=(2, 2, 2), inputs=contraction, spatial_dropout=0.2)
    contraction, expansion3 = convolution_pair(base_size * 4, num_convs=2, conv_size=5, pool_size=(2, 2, 2), inputs=contraction, spatial_dropout=0.3)
    contraction, expansion4 = convolution_pair(base_size * 8, num_convs=2, conv_size=5, pool_size=(2, 2, 2), inputs=contraction, spatial_dropout=0.4)

    mid_conv = add_norm_drop(Convolution3D(base_size*16, 5, 5, 5, activation='relu', border_mode='same')(contraction), spatial_dropout=0.5)
    mid_conv = add_norm_drop(Convolution3D(base_size*16, 5, 5, 5, activation='relu', border_mode='same')(mid_conv), spatial_dropout=0.5)

    expansion = expansion4(mid_conv)
    expansion = expansion3(expansion)
    expansion = expansion2(expansion)
    expansion = expansion1(expansion)
    conv10 = Convolution3D(1, 1, 1, 1, activation='sigmoid')(expansion)
    model = Model(input=inputs, output=conv10)
    model.compile(optimizer=Adam(lr=1e-3), loss=w_binary_crossentropy, metrics=[TPF, TNF, PositiveRatio])
    return model

def unet2(input_shape=input_shape, base_size=32):
    inputs = Input(input_shape)
    contraction, expansion1 = convolution_pair(base_size * 1, num_convs=1, conv_size=5, pool_size=(2, 2, 2), inputs=inputs, spatial_dropout=0)
    contraction, expansion2 = convolution_pair(base_size * 2, num_convs=2, conv_size=5, pool_size=(2, 2, 2), inputs=contraction, spatial_dropout=0)

    mid_conv = add_norm_drop(Convolution3D(base_size*4, 5, 5, 5, activation='relu', border_mode='same')(contraction), spatial_dropout=0)
    mid_conv = add_norm_drop(Convolution3D(base_size*4, 5, 5, 5, activation='relu', border_mode='same')(mid_conv), spatial_dropout=0)

    expansion = expansion2(mid_conv)
    expansion = expansion1(expansion)
    conv10 = Convolution3D(1, 1, 1, 1, activation='sigmoid')(expansion)
    model = Model(input=inputs, output=conv10)
    model.compile(optimizer=Adam(lr=1e-3), loss=w_binary_crossentropy, metrics=[TPF, TNF, PositiveRatio])
    return model

def unet3(input_shape=input_shape, base_size=32):
    inputs = Input(input_shape)
    contraction, expansion1 = convolution_pair(4, num_convs=1, conv_size=7, pool_size=(2, 2, 2), inputs=inputs, spatial_dropout=0)
    contraction, expansion2 = convolution_pair(8, num_convs=1, conv_size=5, pool_size=(2, 2, 2), inputs=contraction, spatial_dropout=0)
    contraction, expansion3 = convolution_pair(8, num_convs=1, conv_size=5, pool_size=(2, 2, 2), inputs=contraction, spatial_dropout=0)

    mid_conv = add_norm_drop(Convolution3D(8, 3, 3, 3, activation='relu', border_mode='same')(contraction), spatial_dropout=0)
    mid_conv = add_norm_drop(Convolution3D(8, 3, 3, 3, activation='relu', border_mode='same')(mid_conv), spatial_dropout=0)

    expansion = expansion3(mid_conv)
    expansion = expansion2(expansion)
    expansion = expansion1(expansion)
    conv10 = Convolution3D(1, 1, 1, 1, activation='sigmoid')(expansion)
    model = Model(input=inputs, output=conv10)
    model.compile(optimizer=Adam(lr=1e-3), loss=w_binary_crossentropy, metrics=[TPF, TNF, PositiveRatio])
    return model


def recent_weight(weights_dir):
    list_of_files = glob.glob(os.path.join(weights_dir, '*.h5'))
    latest_file = max(list_of_files, key=os.path.getctime)
    print('Resuming from {}'.format(latest_file))
    return latest_file

def weights_dir_for(trial):
    weights_dir = 'weights/{}'.format(trial)
    return weights_dir

def load_model(trial, input_shape, reload_weights=True):
    if trial == '1':
        model = unet1(input_shape)
    elif args.trial == '2':
        model = unet2(input_shape)
    elif args.trial == '3':
        model = unet3(input_shape)
    else:
        raise Exception('Choose valid trial')

    weights_dir = weights_dir_for(args.trial)
    if reload_weights:
        model.load_weights(recent_weight(weights_dir))
    return model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--num-gpus', type=int)
    parser.add_argument('--visualize', action='store_true')
    args = parser.parse_args()

    if args.visualize:
        # model = load_model(args.trial, prediction_shape, True)
        pass
    else:
        model = load_model(args.trial, args.resume)
        print(model.summary(line_length=120))

    if args.visualize:
        for case in test_cases:
            voxel_data = file_io.load_voxels(case)
            voxels = voxel_data['voxels']
            model = load_model(args.trial, (*voxels.shape, 1), True)
            voxels = np.expand_dims(voxels, axis=3)
            voxels = np.expand_dims(voxels, axis=0)
            prediction = model.predict(voxels)
            print("Prediction")
            prediction[prediction < 0.5] = 0
            prediction[prediction >= 0.5] = 1
            show_slices(voxels.squeeze(), overlaid_voxels=prediction.squeeze().astype(int), quantized=True)


    batch_gen_train = batch_generator(2, training_generator("train"))
    batch_gen_validation = batch_generator(2, training_generator("validation"))

    save_model_callback = keras.callbacks.ModelCheckpoint(os.path.join(weights_dir_for(args.trial), 'weights.{epoch:02d}.h5'), monitor='accuracy', verbose=3, save_best_only=False, save_weights_only=False, mode='auto', period=1)
    model.fit_generator(batch_gen_train, validation_data=batch_gen_validation, nb_val_samples=512, samples_per_epoch=640, nb_epoch=10000, verbose=1, callbacks=[save_model_callback], pickle_safe=True, nb_worker=4)
    # import pydevd;pydevd.settrace('localhost', port=63421, stdoutToServer=True, stderrToServer=True)

