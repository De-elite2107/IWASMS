from rest_framework import serializers
from .models import MLModel, ModelPrediction


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'version', 'is_active',
            'accuracy', 'f1_score', 'auc_roc', 'false_positive_rate',
            'trained_on_samples', 'training_duration_seconds', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ModelPredictionSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)

    class Meta:
        model = ModelPrediction
        fields = [
            'id', 'model_name', 'predicted_label', 'confidence',
            'raw_probabilities', 'inference_time_ms', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
