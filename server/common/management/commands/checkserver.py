from django.core.management.base import BaseCommand
from server.common.worker_utilities import worker_is_on, stop_worker, no_jobs_in_queue


class Command(BaseCommand):
    help = 'Manage worker state'

    def handle(self, **options):
        if worker_is_on() and no_jobs_in_queue():
            return stop_worker()
        elif not no_jobs_in_queue():
            print('Jobs it queue. Keeping worker server on.')
        else:
            print('Worker is already off.')
