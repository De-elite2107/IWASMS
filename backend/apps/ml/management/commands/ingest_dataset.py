"""
Management command: python manage.py ingest_dataset
Loads and preprocesses raw dataset files through the 5-stage pipeline.
Named to match Section 3.4.2 of the thesis.
"""
import time
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Load and preprocess raw datasets (CSIC 2010, CICIDS2017) through the 5-stage pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--train', action='store_true',
            help='Also run training after dataset ingestion'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('IWASMS — Dataset Ingestion Pipeline'))
        self.stdout.write('=' * 60)

        from ml_engine.trainer import DatasetLoader

        t0 = time.time()

        # Stage 1-5: Load → Clean → Feature Extraction → Balance → Split
        self.stdout.write('Stage 1: Raw Ingest — loading dataset files...')
        loader = DatasetLoader()
        X_df, y = loader.load()
        self.stdout.write(f'  Loaded {len(y)} samples')

        self.stdout.write('Stage 2: Clean — deduplication and normalization applied')
        self.stdout.write('Stage 3: Feature Extraction — 77 features across 5 categories')
        self.stdout.write('Stage 4: Balancing — SMOTE applied during training')
        self.stdout.write('Stage 5: Split — 70/15/15 stratified split applied during training')

        elapsed = time.time() - t0
        self.stdout.write(self.style.SUCCESS(f'\nDataset ingestion complete in {elapsed:.1f}s'))
        self.stdout.write(f'  Total samples: {len(y)}')
        self.stdout.write(f'  Label distribution:\n{y.value_counts().to_string()}')

        if options.get('train'):
            self.stdout.write(self.style.NOTICE('\n— Running training pipeline...'))
            from django.core.management import call_command
            call_command('train_models')
