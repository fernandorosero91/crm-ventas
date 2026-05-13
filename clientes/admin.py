"""
Admin configuration for the clientes app.
"""
from django.contrib import admin

from .models import Client, ClientStatusHistory


class ClientStatusHistoryInline(admin.TabularInline):
    """Inline display of status history records within the Client admin."""
    model = ClientStatusHistory
    extra = 0
    readonly_fields = ('previous_status', 'new_status', 'changed_by', 'changed_at', 'reason')
    can_delete = False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'contact_name',
        'email',
        'phone',
        'industry',
        'assigned_vendedor',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
        'industry',
        'assigned_vendedor',
    )
    search_fields = (
        'company_name',
        'contact_name',
        'email',
        'phone',
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    inlines = [ClientStatusHistoryInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClientStatusHistory)
class ClientStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'previous_status',
        'new_status',
        'changed_by',
        'changed_at',
    )
    list_filter = (
        'new_status',
        'previous_status',
        'changed_by',
    )
    search_fields = (
        'client__company_name',
        'client__contact_name',
        'reason',
    )
    readonly_fields = ('changed_at',)
