from algorithm_test_runner.test_suite import TestSuite


class TestFeatureDetection(TestSuite):
    name = 'feature-detection'
    
    def collect(self):
        return {
            'mri-001-axial': {
                'images': './data/mri-001-axial',
                'golden': './data/points/mri-001-axial-golden.mat',
            }
        }
