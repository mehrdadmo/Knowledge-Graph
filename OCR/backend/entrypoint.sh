#!/bin/bash
set -e

# Run migrations
python manage.py migrate --noinput
python manage.py createtestuser

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 300 backend.wsgi:application