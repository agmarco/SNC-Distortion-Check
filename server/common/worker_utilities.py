import os
import warnings

from celery.exceptions import CeleryError
import heroku3

from server.celery import app

heroku_connection = heroku3.from_key(os.getenv('HEROKU_API_KEY'))
heroku_app_name = os.getenv('HEROKU_APP_NAME')
heroku_app = heroku_connection.apps()[heroku_app_name]


# Base exception thrown because heroku3 exceptions are not defined in documentation
def worker_is_on():
    try:
        active_dynos = [dyno.type for dyno in heroku_app.dynos()]
        return 'worker' in active_dynos
    except Exception:
        if heroku_app_name:
            warnings.warn("""{0} was thrown when checking dynos on {1} app in Heroku. Check to make sure the app name 
            matches an app in the cirs heroku dashboard and the dynos are configured""".format(
                           Exception, heroku_app_name))
        else:
            warnings.warn("""{0} was thrown because you have not set HEROKU_APP_NAME in your .env file. To 
            resolve this error, set the key to 'cirs-dev' or 'cirs-production'.""".format(Exception))
        return False


def no_jobs_in_queue():
    try:
        celery_info = app.control.inspect()
        return not celery_info.active() or celery_info.scheduled() or celery_info.registered()
    except CeleryError:
        warnings.warn('Celery queue not checked', CeleryError)
        return False


def start_worker():
    if not worker_is_on():
        return heroku_app.process_formation()['worker'].scale(1)


def stop_worker():
    if worker_is_on():
        return heroku_app.process_formation()['worker'].scale(0)
