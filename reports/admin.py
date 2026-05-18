"""
Admin configuration for the reports app.
"""
from django.contrib import admin

from .models import ReportLog


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = (
        'generated_by',
        'report_type',
        'export_format',
        'record_count',
        'generated_at',
    )
    list_filter = (
        'report_type',
        'export_format',
        'generated_at',
    )
    search_fields = (
        'generated_by__username',
        'generated_by__first_name',
        'generated_by__last_name',
    )
    readonly_fields = (
        'generated_by',
        'report_type',
        'export_format',
        'filters_applied',
        'record_count',
        'generated_at',
    )
    date_hierarchy = 'generated_at'

    def has_add_permission(self, request):
        # Logs are created programmatically only
        return False

    def has_change_permission(self, request, obj=None):
        return False
