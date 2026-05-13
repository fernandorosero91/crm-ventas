"""
Admin configuration for ventas app models.
"""
from django.contrib import admin
from .models import Opportunity, FollowUp, StageChange


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    """
    Admin interface for Opportunity model.
    """
    list_display = [
        'title',
        'client',
        'estimated_value',
        'probability',
        'weighted_value',
        'stage',
        'assigned_vendedor',
        'expected_close_date',
        'is_active',
    ]
    list_filter = [
        'stage',
        'is_active',
        'assigned_vendedor',
        'expected_close_date',
    ]
    search_fields = [
        'title',
        'client__company_name',
        'client__contact_name',
    ]
    readonly_fields = [
        'weighted_value',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'client', 'assigned_vendedor')
        }),
        ('Valores', {
            'fields': ('estimated_value', 'probability', 'weighted_value')
        }),
        ('Fechas', {
            'fields': ('expected_close_date', 'actual_close_date')
        }),
        ('Estado', {
            'fields': ('stage', 'loss_reason', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    """
    Admin interface for FollowUp model.
    """
    list_display = [
        'follow_up_type',
        'opportunity',
        'client',
        'date',
        'next_action_date',
        'created_by',
        'is_active',
    ]
    list_filter = [
        'follow_up_type',
        'is_active',
        'date',
        'next_action_date',
    ]
    search_fields = [
        'notes',
        'opportunity__title',
        'client__company_name',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Información básica', {
            'fields': ('follow_up_type', 'date', 'created_by')
        }),
        ('Asociaciones', {
            'fields': ('opportunity', 'client'),
            'description': 'Debe estar asociado al menos con un cliente o una oportunidad.'
        }),
        ('Detalles', {
            'fields': ('notes', 'next_action_date')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



@admin.register(StageChange)
class StageChangeAdmin(admin.ModelAdmin):
    """
    Admin interface for StageChange model (audit trail).
    """
    list_display = [
        'opportunity',
        'from_stage',
        'to_stage',
        'changed_by',
        'changed_at',
    ]
    list_filter = [
        'from_stage',
        'to_stage',
        'changed_at',
    ]
    search_fields = [
        'opportunity__title',
        'opportunity__client__company_name',
    ]
    readonly_fields = [
        'opportunity',
        'from_stage',
        'to_stage',
        'changed_by',
        'changed_at',
    ]
    
    def has_add_permission(self, request):
        """StageChange records are created automatically, not manually."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """StageChange records should not be deleted (audit trail)."""
        return False
