"""
Events app — Serializers
"""
from rest_framework import serializers
from .models import SecurityEvent, WebApplication


class WebApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ['id', 'name', 'base_url', 'organization', 'created_at']
        read_only_fields = ['id', 'created_at']


class SecurityEventSerializer(serializers.ModelSerializer):
    alert_status = serializers.SerializerMethodField()

    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'timestamp', 'source_ip', 'destination_ip',
            'http_method', 'url', 'user_agent',
            'attack_type', 'severity', 'is_attack',
            'confidence_score', 'processing_latency_ms',
            'web_application', 'alert_status', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_alert_status(self, obj):
        try:
            return obj.alert.status
        except Exception:
            return None


class SecurityEventDetailSerializer(serializers.ModelSerializer):
    predictions = serializers.SerializerMethodField()
    alert = serializers.SerializerMethodField()

    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'timestamp', 'source_ip', 'destination_ip',
            'http_method', 'url', 'user_agent', 'raw_request',
            'attack_type', 'severity', 'is_attack',
            'confidence_score', 'processing_latency_ms',
            'web_application', 'predictions', 'alert', 'created_at',
        ]

    def get_predictions(self, obj):
        from apps.ml.serializers import ModelPredictionSerializer
        return ModelPredictionSerializer(obj.predictions.all(), many=True).data

    def get_alert(self, obj):
        try:
            from apps.alerts.serializers import SecurityAlertSerializer
            return SecurityAlertSerializer(obj.alert).data
        except Exception:
            return None


class ClassifyRequestSerializer(serializers.Serializer):
    method = serializers.CharField(max_length=20, default='GET')
    url = serializers.CharField()
    headers = serializers.DictField(default=dict)
    body = serializers.CharField(allow_blank=True, default='')
    source_ip = serializers.IPAddressField(default='127.0.0.1')
    destination_ip = serializers.IPAddressField(required=False, allow_null=True, default=None)
    web_application_id = serializers.UUIDField(required=False, allow_null=True, default=None)
