"""
Management command: Generate synthetic behavior data and save to database.
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import BehaviorEvent, CustomerProfile
from apps.analytics.ml.synthetic_data import generate_synthetic_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate synthetic customer behavior data for training'

    def add_arguments(self, parser):
        parser.add_argument(
            '--num-customers', type=int, default=500,
            help='Number of synthetic customers to generate (default: 500)')
        parser.add_argument(
            '--seed', type=int, default=42,
            help='Random seed for reproducibility (default: 42)')
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing behavior data before generating')

    def handle(self, *args, **options):
        num_customers = options['num_customers']
        seed = options['seed']

        if options['clear']:
            self.stdout.write('Clearing existing data...')
            BehaviorEvent.objects.all().delete()
            CustomerProfile.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))

        self.stdout.write(f'Generating synthetic data for {num_customers} customers...')

        data = generate_synthetic_data(num_customers=num_customers, seed=seed)

        events_by_customer = data['events_by_customer']
        customer_metadata = data['customer_metadata']

        # Save events to database
        total_events = 0
        batch_size = 1000
        event_objects = []

        for customer_id, events in events_by_customer.items():
            for event in events:
                event_objects.append(BehaviorEvent(
                    customer_id=customer_id,
                    event_type=event['event_type'],
                    product_id=event.get('product_id'),
                    product_name=event.get('product_name', ''),
                    category_name=event.get('category_name', ''),
                    amount=event.get('amount', 0),
                    quantity=event.get('quantity', 1),
                    metadata=event.get('metadata', {}),
                    timestamp=event['timestamp'],
                ))

                if len(event_objects) >= batch_size:
                    BehaviorEvent.objects.bulk_create(event_objects)
                    total_events += len(event_objects)
                    event_objects = []

        if event_objects:
            BehaviorEvent.objects.bulk_create(event_objects)
            total_events += len(event_objects)

        self.stdout.write(self.style.SUCCESS(
            f'Generated {num_customers} customers with {total_events} events'))
        self.stdout.write(f'Category count: {len(data["category_to_idx"])}')

        # Show persona distribution
        persona_counts = {}
        for meta in customer_metadata.values():
            p = meta['persona']
            persona_counts[p] = persona_counts.get(p, 0) + 1

        self.stdout.write('\nPersona Distribution:')
        for persona, count in sorted(persona_counts.items()):
            self.stdout.write(f'  {persona}: {count}')
