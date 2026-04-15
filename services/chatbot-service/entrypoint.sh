#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py waitdb

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Syncing products for RAG..."
python manage.py sync_products

echo "Starting chatbot service..."
exec python manage.py runserver 0.0.0.0:8000
