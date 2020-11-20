import os

import heroku3

from server.celery import app


heroku_connection = heroku3.from_key(os.getenv('HEROKU_API_KEY'))
heroku_app = heroku_connection.apps()[os.getenv('HEROKU_APP_NAME')]
celery_info = app.control.inspect()


def worker_is_on():
    if heroku_app.dynos():
        active_dynos = [dyno.type for dyno in heroku_app.dynos()]
        return 'worker' in active_dynos
    else:
        return False



def no_jobs_in_queue():
    return not celery_info.active() or celery_info.scheduled() or celery_info.registered()


def start_worker():
    if not worker_is_on():
        return heroku_app.process_formation()['worker'].scale(1)


def stop_worker():
    if worker_is_on():
        return heroku_app.process_formation()['worker'].scale(0)
