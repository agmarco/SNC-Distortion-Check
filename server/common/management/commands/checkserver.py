import logging

from django.core.management.base import BaseCommand

from server.common.worker_utilities import worker_is_on, stop_worker, no_jobs_in_queue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage worker state'

    def handle(self, **options):
        if worker_is_on() and no_jobs_in_queue():
            return stop_worker()
        elif not no_jobs_in_queue():
            logger.info('Jobs in queue. Keeping worker server on.')
        else:
            logger.info('Worker is already off.')
