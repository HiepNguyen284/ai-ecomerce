#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py waitdb

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

# Wait for user-service and product-service to be ready
# echo "Waiting for user-service..."
# for i in $(seq 1 30); do
#     if python -c "import requests; r=requests.get('http://user-service:8000/users/health/', timeout=3); exit(0 if r.status_code < 500 else 1)" 2>/dev/null; then
#         echo "  user-service is ready!"
#         break
#     fi
#     echo "  Waiting... ($i/30)"
#     sleep 3
# done

# echo "Waiting for product-service..."
# for i in $(seq 1 30); do
#     if python -c "import requests; r=requests.get('http://product-service:8000/products/health/', timeout=3); exit(0 if r.status_code < 500 else 1)" 2>/dev/null; then
#         echo "  product-service is ready!"
#         break
#     fi
#     echo "  Waiting... ($i/30)"
#     sleep 3
# done

# Step 1: Seed users (separate command, cleans up temp file on finish)
# echo "Step 1: Seeding users..."
# python manage.py seed_users --skip-if-enough

# Step 2: Generate behavior data
# echo "Step 2: Generating behavior data..."
# python manage.py generate_behavior_data --skip-if-exists

echo "Starting AI service..."
exec python manage.py runserver 0.0.0.0:8000
