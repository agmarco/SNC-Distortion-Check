import os

import heroku3

from server.celery import app


heroku_connection = heroku3.from_key(os.getenv('HEROKU_API_KEY'))
heroku_app = heroku_connection.apps()['cirs-dev']
celery_info = app.control.inspect()


def worker_is_on():
    active_dynos = heroku_app.dynos()
    return len(active_dynos) == 2


def no_jobs_in_queue():
    return not celery_info.app.current_worker_task


def start_worker():
    if not worker_is_on():
        return heroku_app.process_formation()['worker'].scale(1)

def stop_worker():
    if no_jobs_in_queue() and worker_is_on():
        return heroku_app.process_formation()['worker'].scale(0)
