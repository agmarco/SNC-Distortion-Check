web: gunicorn server.wsgi --timeout 120 --log-file -
worker: REMAP_SIGTERM=SIGQUIT celery -A server worker --loglevel=INFO -Ofair -E
