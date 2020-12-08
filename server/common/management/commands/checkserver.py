import logging

from celery.exceptions import CeleryError
from django.core.management.base import BaseCommand
from itertools import chain

from server.common.heroku_api import HerokuAPI
from server.celery import app

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage worker state'

    @staticmethod
    def _jobs_in_queue():
        try:
            celery_inspect = app.control.inspect()
            if celery_inspect.scheduled() or celery_inspect.active():
                celery_info = {
                    'scheduled': len(list(chain(*celery_inspect.scheduled().values()))),
                    'active': len(list(chain(*celery_inspect.active().values())))
                }
                logger.info(
                    f'There are {celery_info["scheduled"]} celery tasks scheduled and {celery_info["active"]} tasks active.')
                if not celery_info["scheduled"] and not celery_info["active"]:
                    return False
                else:
                    return True
            else:
                return False
        except CeleryError:
            logger.error('Celery app not detected.')

    def handle(self, **options):
        heroku_connection = HerokuAPI()
        if heroku_connection.worker_is_on() and not self._jobs_in_queue():
            heroku_connection.stop_worker()
            return logger.info('Worker server scaled to 0.')
        elif self._jobs_in_queue():
            logger.info('Jobs in queue. Keeping worker server on.')
        else:
            logger.info('Worker is already off.')
