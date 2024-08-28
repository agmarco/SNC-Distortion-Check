import logging

from celery.exceptions import CeleryError
from django.core.management.base import BaseCommand

from server.common.heroku_api import HerokuAPI
from server.celery import app

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage worker state'

    @staticmethod
    def celery_count(queue_property):
        celery_app = list(queue_property.keys())[0]
        return len(queue_property[celery_app])

    def count_queue(self):
        inspect = app.control.inspect()
        return self.celery_count(inspect.active()) + self.celery_count(inspect.scheduled()) + self.celery_count(
            inspect.reserved())

    def _jobs_in_queue(self):
        try:
            return bool(self.count_queue())
        except CeleryError:
            logger.error('Celery app not detected.')

    def handle(self, **options):
        heroku_connection = HerokuAPI()
        if heroku_connection.worker_is_on():
            if self._jobs_in_queue():
                return logger.info(f'There are {self.count_queue()} jobs in queue. Keeping worker server on.')
            else:
                heroku_connection.stop_worker()
                return logger.info('There are no jobs in queue. Worker server scaled to 0.')
        else:
            return logger.info('Worker is already off.')
