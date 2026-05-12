from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for CustomUser model.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'supervisor', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'phone', 'avatar', 'supervisor')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'phone', 'avatar', 'supervisor')
        }),
    )
