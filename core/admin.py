from django.contrib import admin
from core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model.
    Provides read-only view of request logs.
    """
    list_display = ['user', 'method', 'endpoint', 'status_code', 'ip_address', 'timestamp']
    list_filter = ['method', 'status_code', 'timestamp']
    search_fields = ['user__username', 'user__email', 'endpoint', 'ip_address']
    readonly_fields = ['user', 'endpoint', 'method', 'timestamp', 'ip_address', 'user_agent', 'status_code']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs."""
        return request.user.is_superuser
