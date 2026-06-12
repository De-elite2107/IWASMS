from rest_framework import serializers
from .models import SecurityAlert


class SecurityAlertSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField(source='event.id', read_only=True)
    source_ip = serializers.CharField(source='event.source_ip', read_only=True)
    attack_type = serializers.CharField(source='event.attack_type', read_only=True)
    url = serializers.CharField(source='event.url', read_only=True)
    assigned_to_username = serializers.SerializerMethodField()

    class Meta:
        model = SecurityAlert
        fields = [
            'id', 'event_id', 'source_ip', 'attack_type', 'url',
            'title', 'description', 'severity', 'status',
            'created_at', 'updated_at', 'resolved_at',
            'assigned_to', 'assigned_to_username',
            'analyst_notes', 'automated_response_taken',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'event_id']

    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None
