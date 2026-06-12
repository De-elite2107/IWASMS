"""
Events app — SecurityEvent and WebApplication models
"""
import uuid
from django.db import models
from django.utils import timezone


class WebApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    base_url = models.URLField(max_length=500)
    organization = models.CharField(max_length=255)
    api_key = models.CharField(max_length=128, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.api_key:
            import secrets
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class SecurityEvent(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('normal', 'Normal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    source_ip = models.GenericIPAddressField(db_index=True)
    destination_ip = models.GenericIPAddressField(null=True, blank=True)
    http_method = models.CharField(max_length=10)
    url = models.TextField()
    user_agent = models.TextField(blank=True, default='')
    raw_request = models.JSONField(default=dict)
    attack_type = models.CharField(max_length=100, db_index=True, default='normal')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, db_index=True, default='normal')
    is_attack = models.BooleanField(default=False, db_index=True)
    confidence_score = models.FloatField(default=0.0)
    processing_latency_ms = models.FloatField(default=0.0)
    web_application = models.ForeignKey(
        WebApplication, on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'severity']),
            models.Index(fields=['source_ip', 'timestamp']),
            models.Index(fields=['attack_type', 'is_attack']),
        ]

    def __str__(self):
        return f"{self.attack_type} from {self.source_ip} at {self.timestamp}"
