"""
Alerts app — SecurityAlert model
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class SecurityAlert(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(
        'events.SecurityEvent', on_delete=models.CASCADE, related_name='alert'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(default='')
    severity = models.CharField(max_length=20, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_alerts'
    )
    analyst_notes = models.TextField(blank=True, default='')
    automated_response_taken = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['severity', 'status']),
        ]

    def __str__(self):
        return f"Alert [{self.status}]: {self.title}"

    def resolve(self, user=None, notes=''):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.assigned_to = user
        if notes:
            self.analyst_notes = notes
        self.save()

    def mark_false_positive(self, user=None, notes=''):
        self.status = 'false_positive'
        self.resolved_at = timezone.now()
        if user:
            self.assigned_to = user
        if notes:
            self.analyst_notes = notes
        self.save()
