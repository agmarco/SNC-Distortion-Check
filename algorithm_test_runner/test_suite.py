
class TestSuite:
    def __init__(self):
        self.case_map = self.collect()

    @classmethod
    def get_name(cls):
        return getattr(cls, 'name', cls.__name__)

    def collect(self):
        raise NotImplementedError()

    def run(self, case_id, case):
        raise NotImplementedError()

    def run_single(self, store, case_id, case):
        pass

    def run_all(self, store):
        for case_id, case in self.case_map.items():
            self.run_single(store, case_id, case)

    def verify(self, result_old, result_new):
        raise NotImplementedError()
