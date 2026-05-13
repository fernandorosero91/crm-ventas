"""
Admin configuration for the notifications app.
"""
from django.contrib import admin

from .models import Notification, EmailLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = ['recipient', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['recipient__username', 'title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """
    Admin interface for EmailLog model.
    Provides read-only view of outbound email attempts.
    """
    list_display = ['recipient_email', 'subject', 'status', 'retry_count', 'sent_at']
    list_filter = ['status']
    search_fields = ['recipient_email', 'subject']
    readonly_fields = ['created_at', 'updated_at', 'sent_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        """Email logs are created programmatically only."""
        return False

    def has_change_permission(self, request, obj=None):
        """Email logs should not be modified manually."""
        return False
