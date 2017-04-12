web: gunicorn server.wsgi --timeout 120 --log-file -
worker: celery -A server worker --loglevel=INFO
