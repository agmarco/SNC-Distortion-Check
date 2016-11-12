import datetime


class Suite:
    '''
    Base class for a suite of algorithm test cases.

    Is responsible for collecting, running, verifying, and visualizing the
    results of running the algorithm against its test cases.
    '''
    def __init__(self, save_store, git_info, golden_store=None, flags=None):
        if flags is None:
            flags = {}

        self.case_map = self.collect()
        self.save_store = save_store
        self.golden_store = golden_store if golden_store else save_store
        self.git_info = git_info
        self.collect_only = 'collect_only' in flags

    def collect(self):
        '''
        Collect all of the cases for this suite, and return them as a dict-like
        mapping where the keys are the "case ids" and the values are the "case
        data"---whatever is needed to run the case.
        '''
        raise NotImplementedError()

    def verify(self, old_condensed_output, new_condensed_output):
        '''
        Given two result comparable outputs, verify if the second result passes based on
        the first result.  Should return a tuple with a boolean and a string
        with any comments.
        '''
        raise NotImplementedError()

    def run(self, case_id, case_input):
        '''
        Run the algorithm against a particular set of "case data".  Should
        return a two-tuple.  The first value of this tuple should contain a
        low-dimensional, easily comparable distilled version of the output.
        The second value can contain any context needed to visualize and
        interpret the result.  The context can be much larger and can contain
        the full result of running the algorithm.
        '''
        raise NotImplementedError()

    @classmethod
    def name(cls):
        return getattr(cls, 'alias', cls.__name__)

    def run_all_cases(self):
        all_pass = True
        for case_id, case_input in self.case_map.items():
            case_pass = self.run_case(case_id, case_input)
            all_pass = all_pass and case_pass
        return all_pass

    def run_case(self, case_id, case_input):
        print('Running {}.{}'.format(self.name(), case_id))
        if self.collect_only:
            return True

        run_result = self.run(case_id, case_input)
        self.validate_result(run_result)

        condensed_output, context = run_result

        result = self.build_result(case_id, condensed_output, context)

        stamp = self.automated_verify(result)
        result['stamps'].append(stamp)

        if self.save_store is None:
            raise ValueError('Unable to save the test result because no store is present')
        else:
            self.save_store.persist(result)

        return stamp['accepted']

    def validate_result(self, run_result):
        if type(run_result) != tuple and len(run_result) == 2:
            raise ValueError('Test Suite {} run must return a tuple'.format(self.name()))

    def build_result(self, case_id, condensed_output, context):
        run_datetime = datetime.datetime.utcnow()
        result = {
            'suite_id': self.name(),
            'case_id': case_id,
            'commit': self.git_info['commit'],
            'ran_by': self.git_info['user'],
            'ran_on': str(run_datetime),
            'condensed_output': condensed_output,
            'context': context,
            'stamps': [],
        }
        result['id'] = self.build_result_id(result)
        return result

    def build_result_id(self, result_without_id):
        # parsing the date time back into a timestamp seems crazy, but it is
        # necessary so that we can:
        # 1. Keep a clean method API for people wanting to overwrite the method
        # 2. Ensure that the `ran_on` and id timestamp are for the same date time
        ran_on_datetime = datetime.datetime.strptime(result_without_id['ran_on'], '%Y-%m-%d %H:%M:%S.%f')
        seconds_timestamp = int(ran_on_datetime.timestamp())
        return '{}-{}'.format(seconds_timestamp, result_without_id['commit'])

    def automated_verify(self, result):
        if self.golden_store is None:
            raise ValueError('No golden store is available to compare against')

        suite_id = self.name()
        golden_result = self.golden_store.last_manually_verified(suite_id, result['case_id'])

        if golden_result is not None:
            verified_against = golden_result['id']

            golden_condensed_output = golden_result['condensed_output']
            condensed_output = result['condensed_output']
            accepted, comments = self.verify(golden_condensed_output, condensed_output)
        else:
            verified_against = None
            accepted, comments = False, 'No golden result to verify against'

        return {
            'accepted': accepted,
            'verified_against': verified_against,
            'comments': comments,
            'verified_on': str(datetime.datetime.utcnow()),
            'verified_by': None,
        }

    def manual_verify(self, case_id, result_id, accepted, comments):
        if self.save_store is None:
            raise ValueError('No store is available to manually verify in')

        suite_id = self.name()
        result = self.save_store.query(suite_id, case_id, result_id)

        stamp = { 'accepted': accepted,
            'verified_against': None,
            'comments': comments,
            'verified_on': str(datetime.datetime.utcnow()),
            'verified_by': self.git_info['user'],
        }

        result['stamps'].append(stamp)

        self.save_store.persist(result)

        if self.golden_store is not self.save_store:
            self.golden_store.persist(result)
