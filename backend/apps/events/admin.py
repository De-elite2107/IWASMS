from django.contrib import admin
from .models import SecurityEvent, WebApplication


@admin.register(WebApplication)
class WebApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'base_url', 'created_at']
    search_fields = ['name', 'organization']


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'source_ip', 'http_method', 'attack_type', 'severity', 'is_attack', 'confidence_score']
    list_filter = ['severity', 'is_attack', 'attack_type']
    search_fields = ['source_ip', 'url', 'attack_type']
    readonly_fields = ['id', 'created_at', 'timestamp']
    ordering = ['-timestamp']
