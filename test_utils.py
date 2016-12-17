import os
import logging
from collections import OrderedDict

import scipy.io
import matplotlib.pyplot as plt

import points_utils
from slicer import PointsSlicer, render_slices, render_points, render_cursor


logger = logging.getLogger(__name__)


data_directory = 'data'
output_directory = 'tmp'
dicom_dir = os.path.join(data_directory, 'dicom')
data_prefixes = os.listdir(dicom_dir)


class MakeRule:
    def __init__(self, targets, dependencies, cmds):
        self.targets = targets
        self.dependencies = dependencies
        self.cmds = cmds

    def __str__(self):
        rule = ' '.join(self.targets) + ': ' + ' '.join(self.dependencies)
        recipes = ['\t' + ' '.join(cmd) for cmd in self.cmds]
        # Make does not handle rules with multiple targets well in multiprocess
        # mode. Workaround from
        # https://www.gnu.org/savannah-checkouts/gnu/automake/manual/html_node/Multiple-Outputs.html
        if len(self.targets) > 1:
            make_hack = self.targets[0] + ': ' + self.targets[1]
        else:
            make_hack = ''
        return '\n'.join([rule] + recipes + [make_hack])


class DataGenerator:
    def __init__(self):
        self.input_test_data = None

    @property
    def description(self):
        descriptions = []
        if self.input_test_data:
            descriptions.extend(self.input_test_data.description)
        descriptions.append(self._description())
        return descriptions

    def _description(self):
        raise NotImplemented

    @property
    def source(self):
        if type(self) == Source:
            return self
        else:
            return self.input_test_data.source

class Source(DataGenerator):
    def __init__(self, zip_filename):
        super().__init__()
        if not zip_filename.endswith('.zip'):
            raise ValueError()

        data_prefix = zip_filename[:-len('.zip')]
        self.data_prefix = data_prefix
        dicom_data_zip = os.path.join(data_directory, 'dicom', zip_filename)
        self.annotaed_points_path = os.path.join(data_directory, 'points', data_prefix + '-golden.mat')

        self.output_data_prefix = os.path.join(output_directory, data_prefix)
        output_voxels_path = self.output_data_prefix + '-voxels.mat'
        output_points_path = self.output_data_prefix + '-points.mat'

        cmds = []
        cmds.append(['./dicom2mat', dicom_data_zip, output_voxels_path])
        if os.path.exists(self.annotaed_points_path):
            cmds.append(['cp', self.annotaed_points_path, output_points_path])
        self.make_rule = MakeRule(targets=[output_voxels_path, output_points_path], dependencies=[], cmds=cmds)

    def _description(self):
        return 'Loaded from {}'.format(self.data_prefix)


class Decimation(DataGenerator):
    def __init__(self, input_test_data, decimation_factor):
        super().__init__()
        self.decimation_factor = decimation_factor

        self.input_test_data = input_test_data
        input_data_prefix = input_test_data.output_data_prefix
        source_voxels_path = input_data_prefix + '-voxels.mat'
        source_points_path = input_data_prefix + '-points.mat'

        self.output_data_prefix = '{}_decimated_{}'.format(input_data_prefix, decimation_factor)
        output_voxels_path = self.output_data_prefix + '-voxels.mat'
        output_points_path = self.output_data_prefix + '-points.mat'

        cmds = [
            ['python', '-m', 'testing.decimate_slices', source_voxels_path, output_voxels_path, decimation_factor],
            ['cp', source_points_path, output_points_path]
        ]
        self.make_rule = MakeRule(targets=[output_voxels_path, output_points_path], dependencies=[source_points_path, source_voxels_path], cmds=cmds)

    def _description(self):
        return 'Decimated by {}'.format(self.decimation_factor)

    @classmethod
    def generate_cases_for(cls, data_prefix):
        return [cls(data_prefix, decimation_factor) for decimation_factor in cls.decimation_factors]


class Distortion(DataGenerator):
    def __init__(self, input_test_data, distortion_factor):
        super().__init__()
        self.distortion_factor = distortion_factor

        self.input_test_data = input_test_data
        input_data_prefix = input_test_data.output_data_prefix
        source_voxels_path = input_data_prefix + '-voxels.mat'
        source_points_path = input_data_prefix + '-points.mat'

        self.output_data_prefix = '{}_distorted_{}'.format(input_data_prefix, distortion_factor)
        output_voxels_path = self.output_data_prefix + '-voxels.mat'
        output_points_path = self.output_data_prefix + '-points.mat'
        cmd = ['python', '-m', 'testing.distort_voxel', source_voxels_path, output_voxels_path, source_points_path, output_points_path,
               '--distort_factor', distortion_factor]

        self.make_rule = MakeRule(targets=[output_voxels_path, output_points_path], dependencies=[source_points_path, source_voxels_path], cmds=[cmd])

    def _description(self):
        return 'Distorted by {}'.format(self.distortion_factor)


class Rotation(DataGenerator):
    def __init__(self, input_test_data, rotation_deg):
        super().__init__()
        self.rotation_deg = rotation_deg

        self.input_test_data = input_test_data
        input_data_prefix = input_test_data.output_data_prefix
        source_voxels_path = input_data_prefix + '-voxels.mat'
        source_points_path = input_data_prefix + '-points.mat'

        self.output_data_prefix = '{}_rotated_{}'.format(input_data_prefix, rotation_deg)
        output_voxels_path = self.output_data_prefix + '-voxels.mat'
        output_points_path = self.output_data_prefix + '-points.mat'
        cmd = ['python', '-m', 'testing.distort_voxel', source_voxels_path, output_voxels_path, source_points_path, output_points_path,
               '--xyz_tpx', '0', '0', '0', rotation_deg, rotation_deg, rotation_deg]

        self.make_rule = MakeRule(targets=[output_voxels_path, output_points_path], dependencies=[source_points_path, source_voxels_path], cmds=[cmd])

    def _description(self):
        return 'Rotated by {} degrees'.format(self.rotation_deg)


class RotationAndDistortion(DataGenerator):
    pass


class Gaussian(DataGenerator):
    pass


class RadialFade(DataGenerator):
    pass


def get_test_data_generators():
    data_generators = []
    for data_prefix in data_prefixes:
        source_data = Source(data_prefix)
        data_generators.append(source_data)
        if not os.path.exists(source_data.annotaed_points_path):
            logger.debug('Annotated points not present for {}, skipping...'.format(data_prefix))
            continue

        decimation_factors = ('2', '3', '4')
        rotation_factors = ('2.5', '5')
        distortion_factors = ('0.8e-4', '2.4e-4')

        for decimation_factor in decimation_factors:
            data_generators.append(Decimation(source_data, decimation_factor))

        for distortion_factor in distortion_factors:
            distortion = Distortion(source_data, distortion_factor)
            data_generators.append(distortion)
            for rotation_factor in rotation_factors:
                data_generators.append(Rotation(distortion, rotation_factor))

        for rotation_factor in rotation_factors:
            rotation = Rotation(source_data, rotation_factor)
            data_generators.append(rotation)

    return data_generators


def load_voxels(voxels_path):
    input_data = scipy.io.loadmat(voxels_path)
    return input_data['voxels'], input_data['ijk_to_patient_xyz_transform']


def load_points(points_path):
    input_data = scipy.io.loadmat(points_path)
    return input_data['points']


def show_base_result(result, voxels_key='voxels'):
    context = result['context']
    descriptors = [
        {'points_xyz': context['FN_A'], 'scatter_kwargs': {'color': 'y', 'label': 'FN_A', 'marker': 'o'}},
        {'points_xyz': context['TP_A'], 'scatter_kwargs': {'color': 'g', 'label': 'TP_A', 'marker': 'o'}},
        {'points_xyz': context['TP_B'], 'scatter_kwargs': {'color': 'g', 'label': 'TP_B', 'marker': 'x'}},
        {'points_xyz': context['FP_B'], 'scatter_kwargs': {'color': 'r', 'label': 'FP_B', 'marker': 'x'}},
    ]
    voxels, ijk_to_xyz = load_voxels(context['case_input'][voxels_key])

    slicer = PointsSlicer(voxels, ijk_to_xyz, descriptors)
    slicer.add_renderer(render_slices)
    slicer.add_renderer(render_points)
    slicer.add_renderer(render_cursor)
    slicer.draw()
    plt.show()
