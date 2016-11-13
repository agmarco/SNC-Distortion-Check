import os
from copy import deepcopy

from algorithm_test_runner.util import deep_equal


class Store:
    def select_golden(self, suite_id, case_id):
        '''
        Select the most up-to-date, manually verified (golden) result for a
        given suite and case.
        '''
        raise NotImplementedError()

    def select(self, suite_id, case_id, result_id):
        '''
        Select a particular result.
        '''
        raise NotImplementedError()

    def insert(self, result):
        '''
        Insert a result.  The result will have the following keys:

        - suite_id
        - case_id
        - id (the result id)
        '''
        raise NotImplementedError()


class JSONOnDiskStore(Store):
    def __init__(self, directory):
        self.root = os.path.abspath(directory)
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        elif os.path.isfile(self.root):
            raise ValueError('Root of store "{}" is a file'.format(self.root))

    def select_golden(self, suite_id, case_id):
        return None

    def select(self, suite_id, case_id, result_id):
        return None

    def insert(self, result):
        suite_id = result['suite_id']
        case_id = result['case_id']
        result_id = result['result_id']
        case_directory = os.path.join(self.root, suite_id, case_id)

        if not os.path.exists(case_directory):
            os.makedirs(case_directory)
        elif os.path.isfile(case_directory):
            raise ValueError('Can not insert result, "{}" is a file'.format(case_directory))

        result_filename = os.path.join(case_directory, '{}.json'.format(result_id))

        if os.path.isfile(result_filename):
            with open(result_filename, 'r') as result_file:
                existing_result = json.load(result_file)
            _validate_only_stamps_changed(existing_result, result)

        with open(result_filename, 'w') as result_file:
            json.dump(result, result_file)

    def _validate_only_stamps_changed(self, old_result, new_result):
        old = deepcopy(old_result)
        new = deepcopy(new_result)
        del old['stamps']
        del new['stamps']
        if not deep_equal(old, new):
            result_id = new['id']
            msg = 'Unable to insert result "{}" because the existing ' + \
                  'file differs by more than the validation stamps'
            raise ValueError(msg.format(result_id))
