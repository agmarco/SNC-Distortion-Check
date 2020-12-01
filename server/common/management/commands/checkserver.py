import logging

from django.core.management.base import BaseCommand

from server.common.heroku_api import HerokuConnect
from server.celery import app

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage worker state'

    def _no_jobs_in_queue(self):
        try:
            celery_info = app.control.inspect()
            return not celery_info.active() or celery_info.scheduled() or celery_info.registered()
        except Exception:
            logging.error('Celery app not detected.')

    def handle(self, **options):
        heroku_connection = HerokuConnect()
        if heroku_connection.worker_is_on() and self._no_jobs_in_queue():
            return heroku_connection.stop_worker()
        elif not self._no_jobs_in_queue():
            logger.info('Jobs in queue. Keeping worker server on.')
        else:
            logger.info('Worker is already off.')
