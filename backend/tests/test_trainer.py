"""
Tests: Model training and evaluation pipeline
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_engine.trainer import DatasetLoader, EnsembleTrainer


class TestMLPipeline:
    def test_dataset_loader(self):
        loader = DatasetLoader()
        X, y = loader.load()
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y)
        assert len(X) >= 100  # Default synthetic generation size
        assert X.shape[1] == 1
        assert list(X.columns) == ['request']

    def test_ensemble_trainer(self):
        loader = DatasetLoader()
        X, y = loader.load()

        # Downsample to 100 samples for extremely fast test execution
        X_small = X.head(100)
        y_small = y.head(100)

        trainer = EnsembleTrainer()
        result = trainer.train(X_small, y_small)

        assert 'metrics' in result
        assert 'model_paths' in result
        assert 'timestamp' in result

        metrics = result['metrics']
        assert 'accuracy' in metrics
        assert 'f1_score' in metrics
        assert 'auc_roc' in metrics
        assert 'false_positive_rate' in metrics
        assert metrics['accuracy'] >= 0.0
        assert metrics['accuracy'] <= 1.0

        paths = result['model_paths']
        assert 'scaler' in paths
        assert 'meta_learner' in paths

