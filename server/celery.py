import os
import sys

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

from django.conf import settings

app = Celery("cirs")

app.conf.accept_content = {'json'}
app.conf.broker_url = os.getenv('REDIS_URL')

# only acknowledge tasks once we have finished; this ensures that if Heroku
# hard-resets our dyno, the tasks will be restarted once the dyno is restarted
app.conf.task_acks_late = True

# kill workers after each task to control memory leaks (we don't care about
# latency very much)
app.conf.worker_max_tasks_per_child = 1

# only run two tasks at a time (to stay within Heroku memory limits)
app.conf.worker_concurrency = 2

# we want to disable prefetch, since long-running processes can unnecessarily
# delay running other tasks, and we don't care about the latency savings that
# prefetch provides
app.conf.worker_prefetch_multiplier = 1

# ensure that tasks don't run forever, and that they are not redelivered to
# other workers until after the timeout length
max_task_duration_secs = 4*3600
app.conf.broker_transport_options = {'visibility_timeout': max_task_duration_secs + 60}
app.conf.task_time_limit = max_task_duration_secs

if settings.TESTING:
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
