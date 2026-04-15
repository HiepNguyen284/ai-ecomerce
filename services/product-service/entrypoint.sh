#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py waitdb

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Seeding products..."
python manage.py seed_products

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
