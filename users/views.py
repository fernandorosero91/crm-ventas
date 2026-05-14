"""
Views for user authentication, registration, profile management, and user administration.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.cache import cache
from django.http import HttpResponseForbidden
from datetime import timedelta
from core.mixins import RoleRequiredMixin, PaginationMixin
from .models import CustomUser
from .forms import (
    RegistrationForm, CustomLoginForm, ProfileUpdateForm,
    PasswordChangeForm, UserManagementForm
)


class CustomLoginView(DjangoLoginView):
    """
    Custom login view with rate limiting and CSRF protection.
    Implements 5 failed attempts → 15 minute lockout.
    """
    template_name = 'users/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to role-appropriate page."""
        user = self.request.user
        
        if user.is_superuser or user.role == 'administrator':
            return reverse_lazy('dashboard:admin_dashboard')
        elif user.role == 'supervisor':
            return reverse_lazy('dashboard:supervisor_dashboard')
        else:  # vendedor
            return reverse_lazy('clientes:client_list')
    
    def form_invalid(self, form):
        """Handle failed login attempts with rate limiting."""
        username = form.data.get('username', '')
        
        if username:
            # Track failed attempts in cache
            cache_key = f'login_attempts_{username}'
            attempts = cache.get(cache_key, 0)
            attempts += 1
            
            # Set cache with 15 minute expiry
            cache.set(cache_key, attempts, 900)  # 900 seconds = 15 minutes
            
            if attempts >= 5:
                messages.error(
                    self.request,
                    'Demasiados intentos fallidos. Su cuenta ha sido bloqueada temporalmente por 15 minutos.'
                )
                return render(self.request, self.template_name, {
                    'form': form,
                    'locked': True
                })
        
        # Generic error message (never reveal which field failed)
        messages.error(
            self.request,
            'Credenciales incorrectas. Por favor, verifique su usuario y contraseña.'
        )
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """Clear failed attempts on successful login."""
        username = form.cleaned_data.get('username')
        cache_key = f'login_attempts_{username}'
        cache.delete(cache_key)
        
        messages.success(self.request, f'Bienvenido, {form.get_user().get_full_name()}!')
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Check if account is locked before processing login."""
        if request.method == 'POST':
            username = request.POST.get('username', '')
            cache_key = f'login_attempts_{username}'
            attempts = cache.get(cache_key, 0)
            
            if attempts >= 5:
                messages.error(
                    request,
                    'Su cuenta está temporalmente bloqueada. Intente nuevamente en 15 minutos.'
                )
                return render(request, self.template_name, {
                    'form': self.form_class(),
                    'locked': True
                })
        
        return super().dispatch(request, *args, **kwargs)


def logout_view(request):
    """
    Logout view that destroys session and redirects to login.
    """
    logout(request)
    messages.info(request, 'Ha cerrado sesión exitosamente.')
    return redirect('users:login')


class RegistrationView(RoleRequiredMixin, CreateView):
    """
    User registration view - only accessible by administrators.
    """
    model = CustomUser
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:user_list')
    allowed_roles = ['administrator']
    
    def form_valid(self, form):
        """Save new user and display success message."""
        user = form.save()
        messages.success(
            self.request,
            f'Usuario {user.username} registrado exitosamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Display error messages."""
        messages.error(
            self.request,
            'Error al registrar usuario. Por favor, corrija los errores indicados.'
        )
        return super().form_invalid(form)


@login_required
def profile_view(request):
    """
    View and update user profile.
    Role field is not editable.
    """
    user = request.user
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Error al actualizar perfil. Corrija los errores indicados.')
    else:
        form = ProfileUpdateForm(instance=user)
    
    return render(request, 'users/profile.html', {
        'form': form,
        'user': user
    })


@login_required
def password_change_view(request):
    """
    Change user password with current password verification.
    Invalidates all other sessions on success.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            form.save()
            # Update session to prevent logout
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Error al cambiar contraseña. Corrija los errores indicados.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/password_change.html', {
        'form': form
    })


class UserListView(RoleRequiredMixin, PaginationMixin, ListView):
    """
    List all users with role filter - Admin only.
    """
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    allowed_roles = ['administrator']
    paginate_by = 15
    
    def get_queryset(self):
        """Filter users by role if specified."""
        queryset = CustomUser.objects.all().select_related('supervisor')
        
        role_filter = self.request.GET.get('role')
        if role_filter and role_filter in dict(CustomUser.ROLE_CHOICES):
            queryset = queryset.filter(role=role_filter)
        
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)
        context['role_choices'] = CustomUser.ROLE_CHOICES
        context['current_role_filter'] = self.request.GET.get('role', '')
        context['current_status_filter'] = self.request.GET.get('status', '')
        return context


class UserCreateView(RoleRequiredMixin, CreateView):
    """
    Create new user - Admin only.
    """
    model = CustomUser
    form_class = UserManagementForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    allowed_roles = ['administrator']
    
    def form_valid(self, form):
        """Set temporary password and save user."""
        user = form.save(commit=False)
        # Set temporary password (should be changed on first login)
        user.set_password('TempPass123!')
        user.save()
        
        messages.success(
            self.request,
            f'Usuario {user.username} creado exitosamente. Contraseña temporal: TempPass123!'
        )
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """Display error messages."""
        messages.error(
            self.request,
            'Error al crear usuario. Corrija los errores indicados.'
        )
        return super().form_invalid(form)


class UserUpdateView(RoleRequiredMixin, UpdateView):
    """
    Edit existing user - Admin only.
    """
    model = CustomUser
    form_class = UserManagementForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    allowed_roles = ['administrator']
    context_object_name = 'user_obj'
    
    def form_valid(self, form):
        """Save user changes."""
        messages.success(
            self.request,
            f'Usuario {form.instance.username} actualizado exitosamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Display error messages."""
        messages.error(
            self.request,
            'Error al actualizar usuario. Corrija los errores indicados.'
        )
        return super().form_invalid(form)


class UserDetailView(RoleRequiredMixin, DetailView):
    """
    View user details - Admin only.
    """
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
    allowed_roles = ['administrator']
    
    def get_context_data(self, **kwargs):
        """Add team members if user is supervisor."""
        context = super().get_context_data(**kwargs)
        
        if self.object.role == 'supervisor':
            context['team_members'] = self.object.get_team_members()
        
        return context


@login_required
def user_deactivate_view(request, pk):
    """
    Soft delete user (set is_active=False) - Admin only.
    """
    if request.user.role != 'administrator':
        return HttpResponseForbidden('No tiene permisos para realizar esta acción.')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, f'Usuario {user.username} desactivado exitosamente.')
        return redirect('users:user_list')
    
    return render(request, 'users/user_confirm_deactivate.html', {
        'user_obj': user
    })


@login_required
def user_activate_view(request, pk):
    """
    Reactivate user (set is_active=True) - Admin only.
    """
    if request.user.role != 'administrator':
        return HttpResponseForbidden('No tiene permisos para realizar esta acción.')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        user.is_active = True
        user.save()
        messages.success(request, f'Usuario {user.username} activado exitosamente.')
        return redirect('users:user_list')
    
    return redirect('users:user_list')
