#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py waitdb

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Waiting for product-service to be ready..."
MAX_RETRIES=15
RETRY_COUNT=0
until wget --spider --quiet http://product-service:8000/products/ 2>/dev/null; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "WARNING: product-service not ready after ${MAX_RETRIES} attempts, starting anyway..."
    break
  fi
  echo "  product-service not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES), retrying in 3s..."
  sleep 3
done

echo "Syncing products for RAG..."
python manage.py sync_products --max-retries 3

echo "Starting chatbot service..."
exec python manage.py runserver 0.0.0.0:8000
