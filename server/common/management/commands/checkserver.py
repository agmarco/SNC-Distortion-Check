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
    def jobs_in_queue():
        try:
            celery_inspect = app.control.inspect()
            celery_info = {
                'scheduled': len(list(chain(*celery_inspect.scheduled().values()))),
                'active': len(list(chain(*celery_inspect.scheduled().values())))
            }
            if celery_info['active'] or celery_info['scheduled']:
                logger.info(f'There are {celery_info["scheduled"]} celery tasks scheduled and {celery_info["scheduled"]} tasks active.')
                return True
            else:
                return False
        except CeleryError:
            logger.error('Celery app not detected.')

    def handle(self, **options):
        heroku_connection = HerokuAPI()
        if heroku_connection.worker_is_on() and not self.jobs_in_queue():
            heroku_connection.stop_worker()
            return logger.info('Worker server scaled to 0.')
        elif self.jobs_in_queue():
            logger.info('Jobs in queue. Keeping worker server on.')
        else:
            logger.info('Worker is already off.')
