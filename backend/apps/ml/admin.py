from django.contrib import admin
from .models import MLModel, ModelPrediction


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'is_active', 'accuracy', 'f1_score', 'auc_roc', 'created_at']
    list_filter = ['is_active']
    readonly_fields = ['id', 'created_at']


@admin.register(ModelPrediction)
class ModelPredictionAdmin(admin.ModelAdmin):
    list_display = ['predicted_label', 'confidence', 'inference_time_ms', 'created_at']
    readonly_fields = ['id', 'created_at']
