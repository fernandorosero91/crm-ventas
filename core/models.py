from django.db import models


class ActiveManager(models.Manager):
    """
    Custom manager that filters queryset to return only active records.
    Filters by is_active=True by default.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
    """
    Abstract base model providing common fields for all models.
    
    Fields:
        created_at: Timestamp when the record was created (auto-set on creation)
        updated_at: Timestamp when the record was last updated (auto-set on every save)
        is_active: Boolean flag for soft deletion (default True)
    
    Managers:
        objects: ActiveManager - returns only active records (is_active=True)
        all_objects: Default Manager - returns all records including inactive
    """
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    is_active = models.BooleanField(default=True)

    # Custom manager for active records (default)
    objects = ActiveManager()
    
    # Manager for accessing all records including inactive
    all_objects = models.Manager()

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """
    Model for storing request logs and audit trail.
    Used by RequestLoggingMiddleware to track user actions.
    """
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    endpoint = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status_code = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.method} {self.endpoint} - {self.timestamp}"
