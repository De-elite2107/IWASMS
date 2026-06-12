"""
Management command: python manage.py ingest_and_train
Loads dataset and trains the ensemble model.
"""
import time
import json
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Load dataset and train the IWASMS ensemble ML model'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('IWASMS — Starting training pipeline...'))

        from ml_engine.trainer import DatasetLoader, EnsembleTrainer

        t0 = time.time()
        loader = DatasetLoader()
        X_df, y = loader.load()
        self.stdout.write(f'Dataset loaded: {len(y)} samples')

        trainer = EnsembleTrainer()
        result = trainer.train(X_df, y)

        # Register in DB
        from apps.ml.tasks import _register_models
        _register_models(result)

        elapsed = time.time() - t0
        self.stdout.write(self.style.SUCCESS(
            f'\nTraining complete in {elapsed:.1f}s\n'
            f'Accuracy:  {result["metrics"]["accuracy"]:.4f}\n'
            f'F1 Score:  {result["metrics"]["f1_score"]:.4f}\n'
            f'AUC-ROC:   {result["metrics"]["auc_roc"]:.4f}\n'
            f'FPR:       {result["metrics"]["false_positive_rate"]:.4f}\n'
        ))
