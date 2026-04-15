import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Wait for the database to be available'

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        max_retries = 60
        retry_count = 0
        while retry_count < max_retries:
            try:
                conn = connections['default']
                conn.ensure_connection()
                self.stdout.write(self.style.SUCCESS('Database available!'))
                return
            except OperationalError:
                retry_count += 1
                self.stdout.write(f'Database unavailable, waiting 2 seconds... ({retry_count}/{max_retries})')
                time.sleep(2)
                connections.close_all()
        raise OperationalError('Could not connect to database after max retries')
