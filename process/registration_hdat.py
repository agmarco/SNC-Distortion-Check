from collections import OrderedDict
from functools import wraps
import math

import matplotlib.pyplot as plt
import numpy as np
from hdat import Suite, MetricsChecker

from . import file_io
from .registration import rigidly_register_and_categorize
from .visualization import scatter3
from .phantoms import paramaters
from . import affine
from .utils import format_xyztpx
from . import points_utils


def random_unit_vector():
    unormalized = np.random.normal(0, 0.5, (3,))
    magnitude = np.linalg.norm(unormalized)
    assert magnitude > 0
    return unormalized/magnitude


def supress_near_isocenter(distortion):
    '''
    MR Scanners are designed to not have distortion near the isocenter.

    This decorator supresses distortion near the isocenter using a sigmoidal
    function.  Distortions at 100mm are 1/2 the value they would have been
    without the supression.
    '''
    @wraps(distortion)
    def supressed_distortion(x, y, z):
        dx, dy, dz = distortion(x, y, z)

        distances_to_isocenter = math.sqrt(x*x + y*y + z*z)
        supression_factor = distances_to_isocenter/(100 + distances_to_isocenter)
        return (dx*supression_factor, dy*supression_factor, dz*supression_factor)

    return supressed_distortion


def no_distortion(x, y, z):
    return (0, 0, 0)


@supress_near_isocenter
def wavy_distortion(x, y, z):
    return (4*math.sin(x/50 + 30), 4*math.cos(x*y/90 + 30), (x + z)/100)


@supress_near_isocenter
def bad_distortion(x, y, z):
    return (x/25, y/19, x/32 + y/20 + z/25)


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
    6. Add extra points

    The random seed for each test is also specified.
    '''
    id = 'registration'

    def collect(self):
        cases = {
            '603A_small_trans': {
                'phantom': '603A',
                'seed': 133,
                'false_negative_fraction': 0,
                'distort_point': no_distortion,
                'rotations_in_degrees': (0, 0, 0),
                'translation_magnitude_mm': 5,
                'noise_sigma_mm': 0.3,
                'false_positive_fraction': 0,
            },
            '603A_trans_pruned': {
                'phantom': '603A',
                'seed': 133,
                'false_negative_fraction': 0.2,
                'distort_point': no_distortion,
                'rotations_in_degrees': (0, 0, 0),
                'translation_magnitude_mm': 5,
                'noise_sigma_mm': 0.3,
                'false_positive_fraction': 0,
            },
            '603A_rot_trans': {
                'phantom': '603A',
                'seed': 134,
                'false_negative_fraction': 0,
                'distort_point': wavy_distortion,
                'rotations_in_degrees': (2, -2, 4),
                'translation_magnitude_mm': 4,
                'noise_sigma_mm': 0.3,
                'false_positive_fraction': 0,
            },
            '603A_worstcase': {
                'phantom': '603A',
                'seed': 134,
                'false_negative_fraction': 0.15,
                'distort_point': bad_distortion,
                'rotations_in_degrees': (2, -2, 4),
                'translation_magnitude_mm': 5,
                'noise_sigma_mm': 0.3,
                'false_positive_fraction': 0.5,
            },
            '604_big_trans': {
                'phantom': '604',
                'seed': 133,
                'false_negative_fraction': 0.1,
                'distort_point': no_distortion,
                'rotations_in_degrees': (3.5, 5.6, 3.5),
                'translation_magnitude_mm': 65,
                'noise_sigma_mm': 1.4,
                'false_positive_fraction': 0.1,
            },
            '603A_big_trans': {
                'phantom': '603A',
                'seed': 133,
                'false_negative_fraction': 0.15,
                'distort_point': no_distortion,
                'rotations_in_degrees': (-4.2, 3.3, 4.5),
                'translation_magnitude_mm': 54,
                'noise_sigma_mm': 0.9,
                'false_positive_fraction': 0.1,
            },
        }
        return cases

    def generate_B(self, A, case_input):
        np.random.seed(case_input['seed'])

        dim, num_points = A.shape
        assert dim == 3

        # 1. randomly remove points (generate FNs)
        num_points_to_remove = round(case_input['false_negative_fraction']*num_points)
        points_to_remove = np.random.choice(num_points, num_points - num_points_to_remove, replace=False)
        B_pruned = A[:, points_to_remove]

        # 2. distortion
        distort_point = case_input['distort_point']
        B_distorted = B_pruned
        for i in range(B_distorted.shape[1]):
            B_distorted[:, i] += distort_point(*B_distorted[:, i])

        # 3 and 4. rotation then translation
        translation_magnitude = case_input['translation_magnitude_mm']
        x, y, z = random_unit_vector()*translation_magnitude
        theta, phi, xi = [math.radians(r) for r in case_input['rotations_in_degrees']]
        xyztpx_expected = np.array([x, y, z, theta, phi, xi])
        B_translated_rotated = affine.apply_xyztpx(xyztpx_expected, B_distorted)

        # 5. add gaussian noise
        B_noise = B_translated_rotated + np.random.normal(0, case_input['noise_sigma_mm'], B_translated_rotated.shape)

        # 6. randomly add points (generate FPs)
        extent_min = np.amin(B_noise, axis=1)
        extent_max = np.amax(B_noise, axis=1)
        extent_delta = extent_max - extent_min
        num_points_to_add = round(case_input['false_positive_fraction']*num_points)
        B_extra = np.zeros((3, num_points_to_add))
        for d in [0, 1, 2]:
            low = extent_min[d] - 0.2*extent_delta[d]
            high = extent_max[d] + 0.2*extent_delta[d]
            B_extra[d, :] = np.random.uniform(low, high, num_points_to_add)
        B_final = np.hstack((B_noise, B_extra))

        return B_final, xyztpx_expected

    def FLE_percentiles_near_isocenter(self, TP_B, TP_A_S, isocenter_in_B):
        distances_to_isocenter = np.linalg.norm(TP_B - isocenter_in_B.reshape(3, 1), axis=0)
        distortion_free_radius = 30
        points_near_isocenter = distances_to_isocenter < distortion_free_radius
        TP_B_near_isocenter = TP_B[:, points_near_isocenter]
        TP_A_S_near_isocenter = TP_A_S[:, points_near_isocenter]
        return points_utils.FLE_percentiles(TP_A_S_near_isocenter, TP_B_near_isocenter)

    def run(self, case_input):
        metrics = OrderedDict()
        context = OrderedDict()

        phantom_paramaters = paramaters[case_input['phantom']]
        points_file = phantom_paramaters['points_file']
        A = file_io.load_points(points_file)['points']

        B, xyztpx_expected = self.generate_B(A, case_input)
        context['A'] = A
        context['B'] = B
        context['xyztpx_expected'] = xyztpx_expected

        isocenter_in_B = np.array([0, 0, 0], dtype=np.double)
        context['isocenter_in_B'] = isocenter_in_B

        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
                A, B, phantom_paramaters['grid_spacing'], isocenter_in_B)

        context['xyztpx_actual'] = xyztpx
        x, y, z, theta, phi, xi = xyztpx
        metrics['x'] = x
        metrics['y'] = y
        metrics['z'] = z
        metrics['theta_degrees'] = math.degrees(theta)
        metrics['phi_degrees'] = math.degrees(phi)
        metrics['xi_degrees'] = math.degrees(xi)

        metrics['registration_shift'] = np.sqrt(x*x + y*y + z*z)

        context['FN_A_S'] = FN_A_S
        context['TP_A_S'] = TP_A_S
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        FLE_percentiles = points_utils.FLE_percentiles(TP_A_S, TP_B)
        FLE_percentiles_near_isocenter = self.FLE_percentiles_near_isocenter(
                TP_A_S, TP_B, isocenter_in_B)

        for p in [25, 50, 95, 99, 100]:
            context['FLE_{}'.format(p)] = FLE_percentiles[p]
            context['FLE_{}_near_isocenter'.format(p)] = FLE_percentiles_near_isocenter[p]

        metrics['FLE_100'] = FLE_percentiles[100]['r']
        metrics['FLE_50'] = FLE_percentiles[50]['r']
        metrics['FLE_50_near_isocenter'] = FLE_percentiles[50]['r']

        return metrics, context

    def check(self, old, new):
        checker = MetricsChecker(old, new)
        shift_tolerance = 0.1
        checker.close('x', abs_tol=shift_tolerance)
        checker.close('y', abs_tol=shift_tolerance)
        checker.close('z', abs_tol=shift_tolerance)
        rotation_tolerance = 0.2
        checker.close('theta_degrees', abs_tol=rotation_tolerance)
        checker.close('phi_degrees', abs_tol=rotation_tolerance)
        checker.close('xi_degrees', abs_tol=rotation_tolerance)
        checker.close('FLE_100', abs_tol=shift_tolerance)
        checker.close('FLE_50', abs_tol=shift_tolerance)
        checker.close('FLE_50_near_isocenter', abs_tol=0.02)
        return checker.result()

    def show(self, result):
        context = result['context']
        case_input = result['case_input']

        FN_A_S = context['FN_A_S']
        TP_A_S = context['TP_A_S']
        TP_B = context['TP_B']
        FP_B = context['FP_B']
        isocenter_in_B = context['isocenter_in_B'].reshape(3, 1)

        print('actual:')
        print(format_xyztpx(context['xyztpx_actual']))
        print('expected:')
        print(format_xyztpx(context['xyztpx_expected']))
        print('diff')
        print(format_xyztpx(context['xyztpx_actual'] - context['xyztpx_expected']))
        print('stats')
        print('TP = {}, FP = {}, FN = {}'.format(TP_B.shape[1], FP_B.shape[1], FN_A_S.shape[1]))
        print('FLE global')
        print(points_utils.format_FLE_percentile(context['FLE_100']))
        print(points_utils.format_FLE_percentile(context['FLE_95']))
        print(points_utils.format_FLE_percentile(context['FLE_50']))
        print(points_utils.format_FLE_percentile(context['FLE_25']))
        print('FLE near isocenter')
        print(points_utils.format_FLE_percentile(context['FLE_100_near_isocenter']))
        print(points_utils.format_FLE_percentile(context['FLE_95_near_isocenter']))
        print(points_utils.format_FLE_percentile(context['FLE_50_near_isocenter']))
        print(points_utils.format_FLE_percentile(context['FLE_25_near_isocenter']))

        A_S = np.hstack((context['FN_A_S'], context['TP_A_S']))

        scatter3({
            'CAD': context['A'],
            'CAD Registered to Detected': A_S,
            'Detected': context['B'],
            'isocenter': isocenter_in_B,
        })
        plt.show()

        distances_to_isocenter = np.linalg.norm(TP_B - isocenter_in_B, axis=0)
        distortion_free_radius = 60
        points_near_isocenter = distances_to_isocenter < distortion_free_radius
        TP_B_near_isocenter = TP_B[:, points_near_isocenter]
        TP_A_S_near_isocenter = TP_A_S[:, points_near_isocenter]

        scatter3({
            'CAD Registered to Detected': TP_A_S_near_isocenter,
            'Detected': TP_B_near_isocenter,
            'isocenter': isocenter_in_B,
        })
        plt.show()
