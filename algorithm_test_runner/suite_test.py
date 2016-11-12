from collections import defaultdict, OrderedDict
import pytest

from algorithm_test_runner.suite import Suite
from algorithm_test_runner.util import is_manually_verified


class BasicSuite(Suite):
    def collect(self):
        return {
            'case1': 5,
            'case2': 9,
        }

    def verify(self, old, new):
        return old == new, 'Looks good!'

    def run(self, case_id, case_input):
        return case_input, {}


class MockStore:
    def __init__(self):
        self.data = defaultdict(lambda: defaultdict(lambda: OrderedDict()))

    def persist(self, result):
        suite_id = result['suite_id']
        case_id = result['case_id']
        result_id = result['id']
        self.data[suite_id][case_id][result_id] = result

    def last_manually_verified(self, suite_id, case_id):
        results = self.data.get(suite_id, {}).get(case_id, {})
        manually_verified_results = list(filter(is_manually_verified, results.values()))
        if len(manually_verified_results) > 0:
            return manually_verified_results[-1]
        else:
            return None

    def query(self, suite_id, case_id, result_id):
        return self.data.get(suite_id, {}).get(case_id, {}).get(result_id, None)


class TestAlgorithmRunnerTestSuite:
    def test_run_all_mark_good_rerun_integration(self):
        store = MockStore()
        git_info = {'commit': 'commit', 'user': 'dg'}
        suite = BasicSuite(store, git_info, golden_store=store)
        assert suite.run_all_cases() == False

        cases = store.data[suite.id()]
        assert len(cases.keys()) == 2

        for case_id, results in cases.items():
            assert len(results) == 1
            result = list(results.values())[0]
            suite.manual_verify(case_id, result['id'], True, '')

        # they should now pass because the golden store is updated
        assert suite.run_all_cases() == True
