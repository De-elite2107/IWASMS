"""
Celery tasks for ML operations
"""
import logging
from iwasms.celery import app

logger = logging.getLogger(__name__)


@app.task(name='apps.ml.tasks.retrain_models_task', bind=True)
def retrain_models_task(self):
    """Queue model retraining."""
    try:
        from ml_engine.trainer import DatasetLoader, EnsembleTrainer
        loader = DatasetLoader()
        X_df, y = loader.load()
        trainer = EnsembleTrainer()
        result = trainer.train(X_df, y)
        _register_models(result)
        logger.info("Retraining complete via Celery task")
        return {'status': 'complete', 'timestamp': result['timestamp']}
    except Exception as e:
        logger.error(f"Retraining task failed: {e}", exc_info=True)
        raise


def _register_models(result: dict):
    """Save trained model metadata to DB."""
    import json
    from apps.ml.models import MLModel

    metrics = result['metrics']
    ts = result['timestamp']
    paths = result['model_paths']

    # Deactivate previous
    MLModel.objects.filter(is_active=True).update(is_active=False)

    model_path_dict = {k: v for k, v in paths.items()
                       if k not in ('scaler', 'label_map', 'metrics')}

    MLModel.objects.create(
        name='ensemble_stacked',
        version=ts,
        model_path=json.dumps(model_path_dict),
        scaler_path=paths.get('scaler', ''),
        meta_learner_path=paths.get('meta_learner', ''),
        label_map_path=paths.get('label_map', ''),
        is_active=True,
        accuracy=metrics.get('accuracy', 0.0),
        f1_score=metrics.get('f1_score', 0.0),
        auc_roc=metrics.get('auc_roc', 0.0),
        false_positive_rate=metrics.get('false_positive_rate', 0.0),
        trained_on_samples=metrics.get('trained_on_samples', 0),
    )
    # Reset inference singleton so it picks up new model
    from apps.ml.inference import InferenceService
    InferenceService.reset_instance()
    logger.info(f"New model registered: ensemble_stacked v{ts}")
