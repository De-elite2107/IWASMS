from django.contrib import admin
from .models import SecurityAlert


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'created_at', 'assigned_to']
    list_filter = ['status', 'severity']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
