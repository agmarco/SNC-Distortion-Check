import logging
import os

import heroku3

logger = logging.getLogger(__name__)


class HerokuAPI:
    def __init__(self):
        self.heroku_connection = heroku3.from_key(os.getenv('HEROKU_API_KEY'))
        self.heroku_app_name = os.getenv('HEROKU_APP_NAME')
        self.heroku_app = self.heroku_connection.apps()[self.heroku_app_name]

    def worker_is_on(self):
        active_dynos = [dyno.type for dyno in self.heroku_app.dynos()]
        return 'worker' in active_dynos

    def start_worker(self):
        if not self.worker_is_on():
            return self.heroku_app.process_formation()['worker'].scale(1)

    def stop_worker(self):
        if self.worker_is_on():
            return self.heroku_app.process_formation()['worker'].scale(0)
