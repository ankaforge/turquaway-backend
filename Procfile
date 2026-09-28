web: gunicorn main.wsgi:application --timeout 65
worker: celery -A main worker --loglevel=info --concurrency=2