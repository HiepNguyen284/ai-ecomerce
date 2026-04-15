#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py waitdb

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

# Check if data and models exist, if not generate and train
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics_service.settings')
django.setup()
from apps.analytics.models import BehaviorEvent, CustomerProfile
event_count = BehaviorEvent.objects.count()
profile_count = CustomerProfile.objects.count()
print(f'Events: {event_count}, Profiles: {profile_count}')
if event_count == 0:
    print('NEED_DATA')
elif profile_count == 0:
    print('NEED_TRAIN')
else:
    print('READY')
" 2>/dev/null | tail -1 > /tmp/status.txt

STATUS=$(cat /tmp/status.txt)

if [ "$STATUS" = "NEED_DATA" ]; then
    echo "Generating synthetic behavior data..."
    python manage.py generate_behavior_data --num-customers 500 --clear
    echo "Training deep learning models..."
    python manage.py train_models --clusters 5
elif [ "$STATUS" = "NEED_TRAIN" ]; then
    echo "Training deep learning models..."
    python manage.py train_models --clusters 5
else
    echo "Data and models already exist. Skipping generation."
fi

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
