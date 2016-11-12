class ResultStore:
    def latest_manually_verified_result(self, suite_id, case_id):
        raise NotImplementedError()

    def retrieve(self, suite_id, case_id, result_id):
        raise NotImplementedError()

    def persist(self, result):
        raise NotImplementedError()
