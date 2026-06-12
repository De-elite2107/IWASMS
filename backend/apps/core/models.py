"""
Core app — AuditLog and ResponseAction models

AuditLog: Immutable append-only record (FR-12).
ResponseAction: Automated actions taken in response to alerts.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditLog(models.Model):
    """
    Immutable audit trail. INSERT-only by design (no UPDATE/DELETE grants in production).
    Satisfies FR-12: All events logged; tamper-evident.
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('classify', 'Classify Request'),
        ('alert_created', 'Alert Created'),
        ('alert_resolved', 'Alert Resolved'),
        ('alert_false_positive', 'Alert Marked False Positive'),
        ('model_retrain', 'Model Retrain Triggered'),
        ('model_promoted', 'Model Promoted to Active'),
        ('ip_blocked', 'IP Blocked'),
        ('export', 'Data Exported'),
        ('config_change', 'Configuration Changed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True, default='')
    resource_id = models.CharField(max_length=255, blank=True, default='')
    detail = models.JSONField(default=dict)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user', 'timestamp']),
        ]
        # Note: In production PostgreSQL, the role used by Django should only have
        # INSERT privilege on this table (no UPDATE/DELETE) to enforce immutability.

    def __str__(self):
        return f"[{self.action}] by {self.user} at {self.timestamp}"

    def save(self, *args, **kwargs):
        # Prevent updates to existing records
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog records are immutable and cannot be deleted.")


class ResponseAction(models.Model):
    """
    Automated or manual response actions taken for a security alert.
    Maps to the response_actions table in Section 3.7.
    """
    ACTION_TYPE_CHOICES = [
        ('ip_block', 'IP Blocked'),
        ('rate_limit', 'Rate Limited'),
        ('session_kill', 'Session Terminated'),
        ('notify', 'Notification Sent'),
        ('escalate', 'Escalated to Admin'),
        ('manual', 'Manual Action'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(
        'alerts.SecurityAlert', on_delete=models.CASCADE, related_name='response_actions'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    description = models.TextField(default='')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='response_actions'
    )
    performed_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.action_type} on alert {self.alert_id}"
