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
            return not celery_info.active() or celery_info.scheduled() or celery_info.registered()
        except CeleryError:
            logging.error('Celery app not detected.')

    def handle(self, **options):
        heroku_connection = HerokuAPI()
        if heroku_connection.worker_is_on() and self._no_jobs_in_queue():
            return heroku_connection.stop_worker()
        elif not self._no_jobs_in_queue():
            logger.info('Jobs in queue. Keeping worker server on.')
        else:
            logger.info('Worker is already off.')

