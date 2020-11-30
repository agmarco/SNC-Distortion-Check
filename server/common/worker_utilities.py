import logging
import os

from celery.exceptions import CeleryError
import heroku3

from server.celery import app


logger = logging.getLogger(__name__)


class HerokuConnect:
    def __init__(self):
        self.heroku_connection = heroku3.from_key(os.getenv('HEROKU_API_KEY'))
        self.heroku_app_name = os.getenv('APP_NAME')
        self.heroku_app = self.heroku_connection.apps()[self.heroku_app_name]


def worker_is_on():
    try:
        heroku_connection = HerokuConnect()
        active_dynos = [dyno.type for dyno in heroku_connection.heroku_app.dynos()]
        return 'worker' in active_dynos
    except Exception:
        logger.debug("""{0} was thrown because you have not set APP_NAME in your .env file. To 
        resolve this error, set the key to 'cirs-dev' or 'cirs-production'.""".format(type(Exception).__name__))
        return False


def no_jobs_in_queue():
    try:
        celery_info = app.control.inspect()
        return not celery_info.active() or celery_info.scheduled() or celery_info.registered()
    except CeleryError:
        logger.error('The celery queue was not checked because it threw this exception: {0}'.format(CeleryError))
        return False


def start_worker():
    if not worker_is_on():
        try:
            heroku_connection = HerokuConnect()
            return heroku_connection.heroku_app.process_formation()['worker'].scale(1)
        except Exception:
            logger.error(
                '{0} was thrown when trying to scale up the worker dyno on {1}.'.format(type(Exception).__name__, heroku_connection.heroku_app_name))


def stop_worker(self):
    try:
        if self.worker_is_on():
            heroku_connection = HerokuConnect()
            return heroku_connection.heroku_app.process_formation()['worker'].scale(0)
    except Exception:
        logger.error(
            '{0} was thrown when trying to scale down the worker dyno on {1}.'.format(type(Exception).__name__, heroku_connection.heroku_app_name))
