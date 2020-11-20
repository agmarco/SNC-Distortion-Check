import heroku3

from server.celery import app

heroku_connection = heroku3.from_key('c442f7d9-b279-4d36-9051-34bf0f9a9c65')
heroku_app = heroku_connection.apps()['cirs-dev']


def worker_is_on():
    active_dynos = heroku_app.dynos()
    return len(active_dynos) == 2


def no_jobs_in_queue():
    celery_info = app.control.inspect()
    worker_status = celery_info.app.current_worker_task
    if not worker_status:
        return True
    else:
        return False


def start_worker():
    if not worker_is_on():
        return heroku_app.process_formation()['worker'].scale(1)


def stop_worker():
    if no_jobs_in_queue() and worker_is_on():
        return heroku_app.process_formation()['worker'].scale(0)
