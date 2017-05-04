from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np

from . import file_io
from .registration import rigidly_register_and_categorize
from hdatt.suite import Suite
from .visualization import scatter3


class RegistrationSuite(Suite):
    id = 'registration'

    def collect(self):
        cases = {
            '006': {
                'B': 'data/points/006_pruned.mat',
                'A': 'data/points/603A.mat',
            },
        }
        return cases

    def run(self, case_input):
        metrics = OrderedDict()
        context = OrderedDict()

        A = file_io.load_points(case_input['A'])['points']
        B = file_io.load_points(case_input['B'])['points']

        assumed_center_of_mass_isocenter = np.mean(B, axis=1)
        context['isocenter'] = assumed_center_of_mass_isocenter

        xyztpx, FN_A_S, TP_A_S, TP_B, FP_B = rigidly_register_and_categorize(
            A,
            B
        )

        x, y, z, theta, phi, xi = xyztpx

        context['x'] = x
        context['y'] = y
        context['z'] = z
        context['theta'] = theta
        context['phi'] = phi
        context['xi'] = xi

        metrics['registration_shift'] = np.sqrt(x*x + y*y + z*z)
        # TODO: add a metric for the angle change

        context['FN_A_S'] = FN_A_S
        context['TP_A_S'] = TP_A_S
        context['TP_B'] = TP_B
        context['FP_B'] = FP_B

        return metrics, context

    def verify(self, old_metrics, new_metrics):
        pass

    def show(self, result):
        context = result['context']
        case_input = result['case_input']

        A = file_io.load_points(case_input['A'])['points']
        B = file_io.load_points(case_input['B'])['points']

        scatter3({
            'A': A,
            'B': B,
            #'FN_A_S': context['FN_A_S'],
            'TP_A_S': context['TP_A_S'],
            #'TP_B': context['TP_B'],
            #'FP_B': context['FP_B'],
            'isocenter': context['isocenter'].reshape(3, 1),
        })
        plt.show()
