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


def random_unit_vector():
    unormalized = np.random.normal(0, 0.5, (3,))
    magnitude = np.linalg.norm(unormalized)
    assert magnitude > 0
    return unormalized/magnitude


class RegistrationSuite(Suite):
    id = 'registration'

    def collect(self):
        cases = {
            '603A_max_trans': {
                'phantom': '603A',
                'seed': 133,
                'translation_magnitude': 0.5,
                'error_magnitude': 0.3,
                'distortion': None,
                'rotations': (0, 0, 0),
            },
            '603A_max_rot': {
                'phantom': '603A',
                'seed': 134,
                'translation_magnitude': 0.1,
                'error_magnitude': 0.3,
                'distortion': None,
                'rotations': (0, 0, 4),
            },
        }
        return cases

    def generate_B(self, A, case_input):
        '''
        Given a set of "ideal" points, A, apply a number of transformations to
        them to generate a set of "detected points", B.
        '''
        np.random.seed(case_input['seed'])

        grid_spacing = paramaters[case_input['phantom']]['grid_spacing']
        grid_radius = paramaters[case_input['phantom']]['grid_radius']

        translation_magnitude = case_input['translation_magnitude']*grid_radius
        x, y, z = random_unit_vector()*translation_magnitude
        theta, phi, xi = [math.radians(r) for r in case_input['rotations']]
        xyztpx_expected = np.array([x, y, z, theta, phi, xi])

        if case_input['distortion'] is not None:
            # TODO: implement this
            B_distorted = A.copy()
        else:
            B_distorted = A.copy()

        noise_sigma = case_input['error_magnitude']*grid_radius
        B_noise = B_distorted + np.random.normal(0, noise_sigma, A.shape)
        B_translated_rotated = affine.apply_xyztpx(xyztpx_expected, B_noise)

        return B_translated_rotated, xyztpx_expected

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
        # TODO: add a metric for the angle change

        context['FN_A_S'] = FN_A_S
        context['TP_A_S'] = TP_A_S
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

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
        case_input = result['case_input']

        FN_A_S = context['FN_A_S']
        TP_A_S = context['TP_A_S']
        TP_B = context['TP_B']
        FP_B = context['FP_B']

        print('actual:')
        self._print_xyztpx(*context['xyztpx_actual'])
        print('expected:')
        self._print_xyztpx(*context['xyztpx_expected'])
        print('diff')
        self._print_xyztpx(*(context['xyztpx_actual'] - context['xyztpx_expected']))
        print('stats')
        print('TP = {}, FP = {}, FN = {}'.format(TP_B.shape[1], FP_B.shape[1], FN_A_S.shape[1]))

        A_S = np.hstack((context['FN_A_S'], context['TP_A_S']))

        scatter3({
            'A': context['A'],
            'A_S': A_S,
            'B': context['B'],
            'isocenter': context['isocenter'].reshape(3, 1),
        })
        plt.show()
