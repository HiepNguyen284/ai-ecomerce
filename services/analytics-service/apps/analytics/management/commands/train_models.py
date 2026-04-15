"""
Management command: Train all deep learning models for customer behavior analysis.
"""

import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import (
    BehaviorEvent, CustomerProfile, SegmentDefinition,
    ModelTrainingLog,
)
from apps.analytics.ml.trainer import TrainingPipeline
from apps.analytics.ml.predictor import get_predictor
from apps.analytics.ml.features import extract_customer_features, features_to_vector

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train all deep learning models for customer behavior analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs', type=int, default=None,
            help='Override default number of epochs for all models')
        parser.add_argument(
            '--clusters', type=int, default=5,
            help='Number of customer segments (default: 5)')

    def handle(self, *args, **options):
        start_time = time.time()

        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== Customer Behavior Deep Learning Training Pipeline ==='))

        # Step 1: Load events from database
        self.stdout.write('\n📊 Loading behavior events from database...')
        events = BehaviorEvent.objects.all().order_by('timestamp')

        if events.count() == 0:
            self.stdout.write(self.style.ERROR(
                'No behavior events found! Run generate_behavior_data first.'))
            return

        # Group events by customer
        events_by_customer = {}
        for event in events.iterator(chunk_size=2000):
            cid = str(event.customer_id)
            if cid not in events_by_customer:
                events_by_customer[cid] = []
            events_by_customer[cid].append({
                'event_type': event.event_type,
                'product_id': str(event.product_id) if event.product_id else None,
                'product_name': event.product_name,
                'category_name': event.category_name,
                'amount': float(event.amount),
                'quantity': event.quantity,
                'timestamp': event.timestamp,
                'metadata': event.metadata,
            })

        self.stdout.write(f'  Loaded {events.count()} events '
                         f'for {len(events_by_customer)} customers')

        # Step 2: Configure and train
        config = {
            'clustering': {'n_clusters': options['clusters']},
        }
        if options['epochs']:
            for key in ['autoencoder', 'churn', 'clv', 'sequence']:
                if key not in config:
                    config[key] = {}
                config[key]['epochs'] = options['epochs']

        pipeline = TrainingPipeline(config)
        self.stdout.write('\n🧠 Starting training...\n')

        results = pipeline.train_all(events_by_customer)

        # Step 3: Save training logs
        self.stdout.write('\n📝 Saving training logs...')
        version = timezone.now().strftime('%Y%m%d_%H%M')

        for model_name, metrics in results.items():
            ModelTrainingLog.objects.create(
                model_name=model_name,
                version=version,
                epochs=metrics.get('epochs', 0),
                final_loss=metrics.get('final_loss', 0),
                accuracy=metrics.get('accuracy'),
                metrics=metrics,
                num_samples=len(events_by_customer),
                training_duration_seconds=metrics.get('duration', 0),
                model_path=f'ml_models/{model_name}.pt',
                is_active=True,
            )

        # Deactivate previous versions
        ModelTrainingLog.objects.exclude(version=version).update(is_active=False)

        # Step 4: Save segment definitions
        self.stdout.write('\n🏷️  Saving segment definitions...')
        SegmentDefinition.objects.all().delete()

        segment_defs = results.get('clustering', {}).get(
            'segment_definitions', [])
        for seg in segment_defs:
            SegmentDefinition.objects.create(
                segment_id=seg['segment_id'],
                name=seg['name'],
                name_vi=seg.get('name_vi', seg['name']),
                description=seg.get('description', ''),
                description_vi=seg.get('description_vi', ''),
                color=seg.get('color', '#6366f1'),
                icon=seg.get('icon', 'users'),
                customer_count=seg.get('customer_count', 0),
                avg_clv=0,
                avg_order_frequency=seg.get('avg_frequency', 0),
                avg_monetary=seg.get('avg_monetary', 0),
                avg_churn_risk=0,
                centroid=seg.get('centroid', []),
            )

        # Step 5: Run predictions and save profiles
        self.stdout.write('\n👤 Computing customer profiles...')
        predictor = get_predictor()
        predictor.load()  # Force reload with new models

        reference_date = timezone.now()
        profile_count = 0

        for cid, events in events_by_customer.items():
            try:
                prediction = predictor.predict_customer(
                    events, cid, reference_date)
                if not prediction:
                    continue

                features = prediction.get('features', {})

                CustomerProfile.objects.update_or_create(
                    customer_id=cid,
                    defaults={
                        'customer_email': f'customer@example.com',
                        'customer_name': f'Customer',
                        'recency_days': features.get('recency_days', 0),
                        'frequency': features.get('frequency', 0),
                        'monetary': features.get('monetary', 0),
                        'avg_order_value': features.get('avg_order_value', 0),
                        'max_order_value': features.get('max_order_value', 0),
                        'min_order_value': features.get('min_order_value', 0),
                        'total_items_purchased': features.get('total_items_purchased', 0),
                        'unique_products_bought': features.get('unique_products', 0),
                        'unique_categories_bought': features.get('unique_categories', 0),
                        'avg_items_per_order': features.get('avg_items_per_order', 0),
                        'cancelled_order_ratio': features.get('cancelled_ratio', 0),
                        'days_as_customer': features.get('days_as_customer', 0),
                        'order_frequency_monthly': features.get('order_frequency_monthly', 0),
                        'preferred_hour': features.get('preferred_hour', 0),
                        'preferred_day_of_week': features.get('preferred_dow', 0),
                        'weekend_purchase_ratio': features.get('weekend_ratio', 0),
                        'category_distribution': features.get('category_distribution', {}),
                        'top_categories': features.get('top_categories', []),
                        'segment_id': prediction.get('segment_id', 0),
                        'segment_name': prediction.get('segment_name', ''),
                        'churn_risk': prediction.get('churn_risk', 0),
                        'predicted_clv': prediction.get('predicted_clv', 0),
                        'embedding': prediction.get('embedding', []),
                    }
                )
                profile_count += 1
            except Exception as e:
                logger.error(f"Error computing profile for {cid}: {e}")

        # Update segment statistics
        for seg in SegmentDefinition.objects.all():
            profiles = CustomerProfile.objects.filter(segment_id=seg.segment_id)
            seg.customer_count = profiles.count()
            if seg.customer_count > 0:
                from django.db.models import Avg
                agg = profiles.aggregate(
                    avg_clv=Avg('predicted_clv'),
                    avg_churn=Avg('churn_risk'),
                    avg_monetary=Avg('monetary'),
                    avg_freq=Avg('order_frequency_monthly'),
                )
                seg.avg_clv = agg['avg_clv'] or 0
                seg.avg_churn_risk = agg['avg_churn'] or 0
                seg.avg_monetary = agg['avg_monetary'] or 0
                seg.avg_order_frequency = agg['avg_freq'] or 0
            seg.save()

        total_time = time.time() - start_time

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Training complete! {profile_count} profiles computed.'))
        self.stdout.write(f'Total time: {total_time:.1f}s')

        # Print summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📋 Training Summary:')
        for model_name, metrics in results.items():
            loss = metrics.get('final_loss', 0)
            acc = metrics.get('accuracy', None)
            dur = metrics.get('duration', 0)
            acc_str = f', accuracy: {acc:.4f}' if acc is not None else ''
            self.stdout.write(
                f'  {model_name}: loss={loss:.6f}{acc_str} ({dur:.1f}s)')

        self.stdout.write('\n🏷️  Segments:')
        for seg in SegmentDefinition.objects.all():
            self.stdout.write(
                f'  {seg.name_vi} ({seg.name}): '
                f'{seg.customer_count} customers, '
                f'Avg CLV: {seg.avg_clv:,.0f}₫')
