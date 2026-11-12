#!/usr/bin/env bash
# Start step: create the tables, load the FAKE demo data, then serve with gunicorn.
set -o errexit
python manage.py migrate --no-input
python manage.py seed_demo
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}" --timeout 120
