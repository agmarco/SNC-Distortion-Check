web: gunicorn server.wsgi --reload --timeout 120 --log-file -
worker: celery -A server worker --loglevel=INFO
