import uuid

from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """
    Immutable audit log for tracking important events.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    event_type = models.CharField(max_length=100, db_index=True)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'core_audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['event_type', 'created_at']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'system'
        return f"{self.event_type} by {user_str} at {self.created_at}"
