"""
Reusable view mixins for common functionality.
Provides role-based access control and pagination configuration.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.conf import settings


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin to enforce role-based access control on views.
    
    Usage:
        class MyView(RoleRequiredMixin, View):
            allowed_roles = ['administrator', 'supervisor']
    
    Attributes:
        allowed_roles: List of role names that can access this view
    """
    allowed_roles = []  # Must be overridden in subclass

    def dispatch(self, request, *args, **kwargs):
        """
        Check if user has required role before dispatching request.
        
        Raises:
            PermissionDenied: If user role is not in allowed_roles
        """
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has required role
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied("No tiene permisos para acceder a esta página.")
        
        return super().dispatch(request, *args, **kwargs)


class PaginationMixin:
    """
    Mixin to add configurable pagination to list views.
    
    Usage:
        class MyListView(PaginationMixin, ListView):
            paginate_by = 30  # Optional: override default
    
    Attributes:
        paginate_by: Number of items per page (default from settings)
        page_size_options: Available page size options for user selection
    """
    paginate_by = None  # Will use DEFAULT_PAGE_SIZE from settings if not set
    page_size_options = None  # Will use PAGE_SIZE_OPTIONS from settings if not set

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set defaults from settings if not overridden
        if self.paginate_by is None:
            self.paginate_by = getattr(settings, 'DEFAULT_PAGE_SIZE', 15)
        
        if self.page_size_options is None:
            self.page_size_options = getattr(settings, 'PAGE_SIZE_OPTIONS', [15, 30, 50])

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by.
        Allows user to override via query parameter.
        
        Args:
            queryset: The queryset being paginated
            
        Returns:
            Number of items per page
        """
        # Allow user to select page size via query parameter
        page_size = self.request.GET.get('page_size')
        
        if page_size:
            try:
                page_size = int(page_size)
                # Validate against allowed options
                if page_size in self.page_size_options:
                    return page_size
            except (ValueError, TypeError):
                pass
        
        return self.paginate_by

    def get_context_data(self, **kwargs):
        """
        Add pagination context to template.
        
        Returns:
            Context dictionary with pagination data
        """
        context = super().get_context_data(**kwargs)
        context['page_size_options'] = self.page_size_options
        context['current_page_size'] = self.get_paginate_by(None)
        return context


class RoleScopedQuerysetMixin:
    """
    Mixin to filter queryset based on user role.
    
    Implements role-based data scoping:
    - Vendedor: sees only their assigned records
    - Supervisor: sees records of their team members
    - Administrator: sees all records
    
    Usage:
        class MyListView(RoleScopedQuerysetMixin, ListView):
            scope_field = 'assigned_vendedor'  # Field to filter by
    """
    scope_field = 'assigned_vendedor'  # Override in subclass if needed

    def get_queryset(self):
        """
        Filter queryset based on user role.
        
        Returns:
            Filtered queryset based on user permissions
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'administrator':
            # Administrators see all records
            return queryset
        
        elif user.role == 'supervisor':
            # Supervisors see records of their team members
            team_members = user.get_team_members()
            team_ids = list(team_members.values_list('id', flat=True))
            team_ids.append(user.id)  # Include supervisor's own records
            
            filter_kwargs = {f'{self.scope_field}__in': team_ids}
            return queryset.filter(**filter_kwargs)
        
        elif user.role == 'vendedor':
            # Vendedores see only their own records
            filter_kwargs = {self.scope_field: user}
            return queryset.filter(**filter_kwargs)
        
        # Default: return empty queryset for unknown roles
        return queryset.none()


class OwnershipRequiredMixin:
    """
    Mixin to ensure user can only modify their own records.
    
    Usage:
        class MyUpdateView(OwnershipRequiredMixin, UpdateView):
            ownership_field = 'assigned_vendedor'
    """
    ownership_field = 'assigned_vendedor'

    def get_object(self, queryset=None):
        """
        Get object and verify ownership.
        
        Raises:
            PermissionDenied: If user doesn't own the object
        """
        obj = super().get_object(queryset)
        user = self.request.user

        # Administrators can modify anything
        if user.role == 'administrator':
            return obj
        
        # Supervisors can modify team members' records
        if user.role == 'supervisor':
            owner = getattr(obj, self.ownership_field)
            team_members = user.get_team_members()
            if owner == user or owner in team_members:
                return obj
            raise PermissionDenied("No tiene permisos para modificar este registro.")
        
        # Vendedores can only modify their own records
        if user.role == 'vendedor':
            owner = getattr(obj, self.ownership_field)
            if owner == user:
                return obj
            raise PermissionDenied("No tiene permisos para modificar este registro.")
        
        raise PermissionDenied("No tiene permisos para acceder a este registro.")
