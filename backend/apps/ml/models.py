"""
ML app — MLModel and ModelPrediction models
"""
import uuid
from django.db import models


class MLModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)        # 'random_forest', 'xgboost', etc.
    version = models.CharField(max_length=50)
    model_path = models.TextField()
    scaler_path = models.TextField(blank=True, default='')
    meta_learner_path = models.TextField(blank=True, default='')
    label_map_path = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=False, db_index=True)
    accuracy = models.FloatField(default=0.0)
    f1_score = models.FloatField(default=0.0)
    auc_roc = models.FloatField(default=0.0)
    false_positive_rate = models.FloatField(default=0.0)
    trained_on_samples = models.IntegerField(default=0)
    training_duration_seconds = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} v{self.version} (active={self.is_active})"


class ModelPrediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        'events.SecurityEvent', on_delete=models.CASCADE, related_name='predictions'
    )
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    predicted_label = models.CharField(max_length=100)
    confidence = models.FloatField()
    raw_probabilities = models.JSONField(default=dict)
    inference_time_ms = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction {self.predicted_label} ({self.confidence:.2f})"
