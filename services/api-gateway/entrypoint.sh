#!/bin/sh
set -e

echo "Starting API Gateway..."
exec python manage.py runserver 0.0.0.0:8000
