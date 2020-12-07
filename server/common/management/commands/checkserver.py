import logging

from celery.exceptions import CeleryError
from django.core.management.base import BaseCommand

from server.common.heroku_api import HerokuAPI
from server.celery import app

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage worker state'

   @staticmethod
    def _no_jobs_in_queue():
        try:
            celery_info = app.control.inspect()
            if celery_info.active() or celery_info.scheduled() or celery_info.registered():
                logger.info(f"""There are {celery_info.scheduled()} celery tasks scheduled; {celery_info.active()} 
                tasks active and {celery_info.registered()} tasks registered.""")
                return False
            else:
                return True
        except CeleryError:
            logger.error('Celery app not detected.')

    def handle(self, **options):
        heroku_connection = HerokuAPI()
        if heroku_connection.worker_is_on() and self._no_jobs_in_queue():
            heroku_connection.stop_worker()
            return logger.info('Worker server scaled to 0.')
        elif not self._no_jobs_in_queue():
            logger.info('Jobs in queue. Keeping worker server on.')
        else:
            logger.info('Worker is already off.')

