import logging
import os

from celery.exceptions import CeleryError
import heroku3

from server.celery import app

heroku_connection = heroku3.from_key(os.getenv('HEROKU_API_KEY'))
heroku_app_name = os.getenv('HEROKU_APP_NAME')
heroku_app = heroku_connection.apps()[heroku_app_name]

logger = logging.getLogger(__name__)


# Base exception thrown because heroku3 exceptions are not defined in documentation
def worker_is_on():
    try:
        active_dynos = [dyno.type for dyno in heroku_app.dynos()]
        return 'worker' in active_dynos
    except Exception:
        if heroku_app_name:
            logger.debug("""{0} was thrown when checking dynos on {1} app in Heroku. Check to make sure the app name 
            matches an app in the cirs heroku dashboard.""".format(
                Exception, heroku_app_name))
        else:
            logger.debug("""{0} was thrown because you have not set HEROKU_APP_NAME in your .env file. To 
            resolve this error, set the key to 'cirs-dev' or 'cirs-production'.""".format(Exception))
        return False


def no_jobs_in_queue():
    try:
        celery_info = app.control.inspect()
        return not celery_info.active() or celery_info.scheduled() or celery_info.registered()
    except CeleryError:
        logger.debug('The celery queue was not checked because it threw this exception: {0}'.format(CeleryError))
        return False


def start_worker():
    if not worker_is_on():
        try:
            return heroku_app.process_formation()['worker'].scale(1)
        except Exception:
            logger.debug(
                '{0} was thrown when trying to scale up the worker dyno on {1}.'.format(Exception, heroku_app_name))


def stop_worker():
    try:
        if worker_is_on():
            return heroku_app.process_formation()['worker'].scale(0)
    except Exception:
        logger.debug(
            '{0} was thrown when trying to scale down the worker dyno on {1}.'.format(Exception, heroku_app_name))