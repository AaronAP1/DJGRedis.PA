#!/bin/bash
set -e
echo "Starting UPEU PPP API..."
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH
cd /home/site/wwwroot
python manage.py migrate --noinput || echo "Migrations skipped"
python manage.py collectstatic --noinput || echo "Static skipped"
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 config.wsgi:application