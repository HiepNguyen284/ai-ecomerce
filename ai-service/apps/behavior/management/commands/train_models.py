"""
Django management command to train RNN, LSTM, BiLSTM models
on user behavior data and select the best model.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Train RNN, LSTM, BiLSTM models on behavior data and select best model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs', type=int, default=30,
            help='Number of training epochs (default: 30)',
        )
        parser.add_argument(
            '--seq-length', type=int, default=10,
            help='Sequence length for sliding window (default: 10)',
        )
        parser.add_argument(
            '--csv',  type=str, default=None,
            help='Custom path to data_user500.csv',
        )

    def handle(self, *args, **options):
        from apps.behavior.ml.trainer import run_full_pipeline

        data_dir = getattr(
            settings, 'DATA_DIR',
            os.path.join(settings.BASE_DIR, 'data'),
        )
        csv_path = options['csv'] or os.path.join(data_dir, 'data_user500.csv')
        output_dir = os.path.join(data_dir, 'ml_models')

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(
                f'CSV not found: {csv_path}. '
                f'Run generate_behavior_data first.'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            'Training Behavior Prediction Models'))
        self.stdout.write(f'  CSV:        {csv_path}')
        self.stdout.write(f'  Output:     {output_dir}')
        self.stdout.write(f'  Epochs:     {options["epochs"]}')
        self.stdout.write(f'  Seq Length: {options["seq_length"]}')

        results = run_full_pipeline(
            csv_path=csv_path,
            output_dir=output_dir,
            epochs=options['epochs'],
            seq_length=options['seq_length'],
            stdout=self.stdout,
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n★ Best model: {results["best_model_name"]} '
            f'saved to {output_dir}/model_best.pt'))
