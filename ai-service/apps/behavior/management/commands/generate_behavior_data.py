"""
Django management command to generate user behavior data.

Generates data_user500.csv with 500 users and 8 behavior types
using REAL user UUIDs and product UUIDs from the databases,
then loads it into the AI service database.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.behavior.data_generator import generate_behavior_data
from apps.behavior.models import UserBehavior


class Command(BaseCommand):
    help = 'Generate user behavior data (data_user500.csv) with 500 real users and 8 actions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Skip generation if data_user500.csv already exists',
        )
        parser.add_argument(
            '--no-db-load',
            action='store_true',
            help='Only generate CSV, do not load into database',
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Custom output path for the CSV file',
        )

    def handle(self, *args, **options):
        data_dir = getattr(settings, 'DATA_DIR', os.path.join(settings.BASE_DIR, 'data'))
        output_path = options['output'] or os.path.join(data_dir, 'data_user500.csv')

        # Check if file already exists
        if options['skip_if_exists'] and os.path.exists(output_path):
            # Also check if DB has data
            if UserBehavior.objects.exists():
                self.stdout.write(self.style.WARNING(
                    f'data_user500.csv already exists at {output_path} and DB has data. Skipping.'
                ))
                return

        self.stdout.write(self.style.MIGRATE_HEADING('Generating User Behavior Data'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Target: 500 users with REAL UUIDs from databases')
        self.stdout.write(f'  Actions: view, click, search, add_to_cart, add_to_wishlist, purchase, review, share')
        self.stdout.write(f'  Source: user-service DB (user_db) + product-service DB (product_db)')
        self.stdout.write('=' * 60)

        stats, records = generate_behavior_data(output_path, stdout=self.stdout)

        if 'error' in stats:
            self.stdout.write(self.style.ERROR(f'\nError: {stats["error"]}'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n{"=" * 60}'))
        self.stdout.write(self.style.SUCCESS(f'Data generated successfully!'))
        self.stdout.write(f'  Total records: {stats["total_records"]}')
        self.stdout.write(f'  Total users:   {stats["total_users"]} (real UUIDs)')
        self.stdout.write(f'  Total products: {stats["total_products"]} (real UUIDs)')
        self.stdout.write(f'  Date range:    {stats["date_range"]["start"]} to {stats["date_range"]["end"]}')
        self.stdout.write(f'  CSV saved to:  {output_path}')
        self.stdout.write(f'\nAction distribution:')
        for action, count in stats['action_distribution'].items():
            pct = count / stats['total_records'] * 100 if stats['total_records'] > 0 else 0
            bar = '█' * int(pct)
            self.stdout.write(f'  {action:>18s}: {count:>6d} ({pct:5.1f}%) {bar}')

        # Load into database
        if not options['no_db_load']:
            self.stdout.write(f'\nLoading data into AI database...')
            self._load_to_db(records)
            self.stdout.write(self.style.SUCCESS(
                f'Loaded {len(records)} records into user_behaviors table!'
            ))

    def _load_to_db(self, records):
        """Bulk load records into the UserBehavior table."""
        from datetime import datetime

        # Clear existing data
        deleted_count = UserBehavior.objects.all().delete()[0]
        if deleted_count:
            self.stdout.write(f'  Cleared {deleted_count} existing records')

        # Bulk create in batches
        batch_size = 5000
        behaviors = []
        loaded = 0

        for record in records:
            behaviors.append(UserBehavior(
                user_id=record['user_id'],
                product_id=record['product_id'],
                action=record['action'],
                timestamp=datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S'),
            ))

            if len(behaviors) >= batch_size:
                UserBehavior.objects.bulk_create(behaviors)
                loaded += len(behaviors)
                self.stdout.write(f'  Loaded {loaded}/{len(records)} records...')
                behaviors = []

        if behaviors:
            UserBehavior.objects.bulk_create(behaviors)
            loaded += len(behaviors)

        self.stdout.write(f'  Total loaded: {loaded} records')
