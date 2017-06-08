from collections import OrderedDict
import math

import matplotlib.pyplot as plt
import numpy as np

from . import file_io
from .registration import rigidly_register_and_categorize
from hdatt.suite import Suite
from .visualization import scatter3
from .phantoms import paramaters
from . import affine
from .utils import print_xyztpx
from . import points_utils


def random_unit_vector():
    unormalized = np.random.normal(0, 0.5, (3,))
    magnitude = np.linalg.norm(unormalized)
    assert magnitude > 0
    return unormalized/magnitude


def distort_point_identity(x, y, z):
    return (x, y, z)


def distort_point_bad(x, y, z):
    return (x + x/40 - x*x/600, y - y/35*x/35, z - x/40)


class RegistrationSuite(Suite):
    '''
    The registration HDAT tests register a set of phantom CAD points to a
    modified version of itself.  The set of modified points applies the
    following transforms:

    1. Randomly remove a fraction of the total points
    2. Distort each point---specified using a function that takes an (x, y, z)
       tuple and returns an (x, y, z) tuple (where values are in mm)
    3. Apply a random translation with a specified magnitude
    4. Rotate by specified amounts along each axis---specified in degrees
    5. Adds gaussian noise---the sigma for the noise is specified in mm

    The random seed for each test is also specified.
    '''
    id = 'registration'

    def collect(self):
        cases = {
            '603A_max_trans': {
                'phantom': '603A',
                'seed': 133,
                'false_negative_fraction': 0,
                'distort_point': distort_point_identity,
                'rotations_in_degrees': (0, 0, 0),
                'translation_magnitude_mm': 5,
                'noise_sigma_mm': 0.3,
            },
            '603A_max_trans_pruned': {
                'phantom': '603A',
                'seed': 133,
                'false_negative_fraction': 0.2,
                'distort_point': distort_point_identity,
                'rotations_in_degrees': (0, 0, 0),
                'translation_magnitude_mm': 5,
                'noise_sigma_mm': 0.3,
            },
            '603A_max_rot': {
                'phantom': '603A',
                'seed': 134,
                'false_negative_fraction': 0,
                'distort_point': distort_point_identity,
                'rotations_in_degrees': (0, 0, 4),
                'translation_magnitude_mm': 0.1,
                'noise_sigma_mm': 0.3,
            },
            '603A_max_rot_trans': {
                'phantom': '603A',
                'seed': 134,
                'false_negative_fraction': 0,
                'distort_point': distort_point_identity,
                'rotations_in_degrees': (2, -2, 4),
                'translation_magnitude_mm': 4,
                'noise_sigma_mm': 0.3,
            },
            '603A_worstcase': {
                'phantom': '603A',
                'seed': 134,
                'false_negative_fraction': 0.1,
                'distort_point': distort_point_bad,
                'rotations_in_degrees': (2, -2, 4),
                'translation_magnitude_mm': 4,
                'noise_sigma_mm': 0.1,
            },
        }
        return cases

    def generate_B(self, A, case_input):
        np.random.seed(case_input['seed'])

        dim, num_points = A.shape
        assert dim == 3

        # 1. randomly remove points
        num_points_to_remove = round(case_input['false_negative_fraction']*num_points)
        points_to_remove = np.random.choice(num_points, num_points - num_points_to_remove, replace=False)
        B_pruned = A[:, points_to_remove]

        # 2. distortion
        distort_point = case_input['distort_point']
        B_distorted = B_pruned
        for i in range(B_distorted.shape[1]):
            B_distorted[:, i] = distort_point(*B_distorted[:, i])

        # 3 and 4. rotation then translation
        translation_magnitude = case_input['translation_magnitude_mm']
        x, y, z = random_unit_vector()*translation_magnitude
        theta, phi, xi = [math.radians(r) for r in case_input['rotations_in_degrees']]
        xyztpx_expected = np.array([x, y, z, theta, phi, xi])
        B_translated_rotated = affine.apply_xyztpx(xyztpx_expected, B_distorted)

        # 5. add gaussian noise
        B_noise = B_translated_rotated + np.random.normal(0, case_input['noise_sigma_mm'], B_translated_rotated.shape)

        return B_noise, xyztpx_expected

    def run(self, case_input):
        metrics = OrderedDict()
        context = OrderedDict()

        points_file = paramaters[case_input['phantom']]['points_file']
        A = file_io.load_points(points_file)['points']

        B, xyztpx_expected = self.generate_B(A, case_input)
        context['A'] = A
        context['B'] = B
        context['xyztpx_expected'] = xyztpx_expected

        context['isocenter'] = np.array([0, 0, 0])

        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                A, B, context['isocenter'], skip_brute=True)

        context['xyztpx_actual'] = xyztpx
        x, y, z, theta, phi, xi = xyztpx

        metrics['registration_shift'] = np.sqrt(x*x + y*y + z*z)

        context['FN_A_S'] = FN_A_S
        context['TP_A_S'] = TP_A_S
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        FLE_percentiles = points_utils.FLE_percentiles(TP_A_S, TP_B)
        for p in [0, 25, 50, 75, 95, 99, 100]:
            metrics['FLE_{}'.format(p)] = FLE_percentiles[p]

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        pass

    def _print_xyztpx(self, x, y, z, theta, phi, xi):
        msg = 'trans = ({:06.4f}mm, {:06.4f}mm, {:06.4f}mm)\n' + \
              'rot = ({:06.4f}deg, {:06.4f}deg, {:06.4f}deg)'
        theta, phi, xi = (math.degrees(r) for r in (theta, phi, xi))
        print(msg.format(x, y, z, theta, phi, xi))

    def show(self, result):
        context = result['context']
        metrics = result['metrics']
        case_input = result['case_input']

        FN_A_S = context['FN_A_S']
        TP_A_S = context['TP_A_S']
        TP_B = context['TP_B']
        FP_B = context['FP_B']

        print('actual:')
        print_xyztpx(context['xyztpx_actual'])
        print('expected:')
        print_xyztpx(context['xyztpx_expected'])
        print('diff')
        print_xyztpx(context['xyztpx_actual'] - context['xyztpx_expected'])
        print('stats')
        print('TP = {}, FP = {}, FN = {}'.format(TP_B.shape[1], FP_B.shape[1], FN_A_S.shape[1]))
        print(points_utils.format_FLE_percentile(metrics['FLE_99']))
        print(points_utils.format_FLE_percentile(metrics['FLE_50']))
        print(points_utils.format_FLE_percentile(metrics['FLE_25']))

        A_S = np.hstack((context['FN_A_S'], context['TP_A_S']))

        scatter3({
            'CAD': context['A'],
            'CAD Shifted': A_S,
            'Detected': context['B'],
            'isocenter': context['isocenter'].reshape(3, 1),
        })
        plt.show()
