"""
Views for the clientes app.
Implements role-based CRUD, smart search, advanced filters, and soft delete.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.mixins import (
    OwnershipRequiredMixin,
    PaginationMixin,
    RoleRequiredMixin,
    RoleScopedQuerysetMixin,
)
from .forms import ClientForm
from .models import Client, ClientStatusHistory


# ---------------------------------------------------------------------------
# Helper: scope a queryset to the requesting user's role
# ---------------------------------------------------------------------------

def _scope_clients_for_user(queryset, user):
    """
    Filter a Client queryset according to the user's role.
    - administrator: all records
    - supervisor: records of team members
    - vendedor: own records only
    """
    if user.role == 'administrator':
        return queryset
    if user.role == 'supervisor':
        team_ids = list(user.get_team_members().values_list('id', flat=True))
        team_ids.append(user.id)
        return queryset.filter(assigned_vendedor__in=team_ids)
    # vendedor
    return queryset.filter(assigned_vendedor=user)


# ---------------------------------------------------------------------------
# 8.1 + 8.2 — ClientListView with role-based filtering, search, and filters
# ---------------------------------------------------------------------------

class ClientListView(LoginRequiredMixin, PaginationMixin, ListView):
    """
    Paginated list of clients with role-based scoping, smart search,
    and advanced filters (status, industry, vendedor, date range).
    """
    model = Client
    template_name = 'clientes/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        user = self.request.user
        params = self.request.GET

        # Determine base queryset based on status filter
        status_filter = params.get('status', '')
        if status_filter == 'inactive':
            qs = Client.all_objects.filter(is_active=False)
        elif status_filter == 'active':
            qs = Client.objects.all()
        else:
            qs = Client.objects.all()

        # Role-based scoping
        qs = _scope_clients_for_user(qs, user)

        # Smart search (min 2 chars)
        q = params.get('q', '').strip()
        if len(q) >= 2:
            # Try numeric match for client ID
            id_filter = Q()
            if q.isdigit():
                id_filter = Q(id=int(q))
            qs = qs.filter(
                id_filter
                | Q(company_name__icontains=q)
                | Q(contact_name__icontains=q)
                | Q(email__icontains=q)
            )

        # Advanced filters
        industry = params.get('industry', '').strip()
        if industry:
            qs = qs.filter(industry__icontains=industry)

        vendedor_id = params.get('assigned_vendedor', '').strip()
        if vendedor_id and vendedor_id.isdigit():
            qs = qs.filter(assigned_vendedor_id=int(vendedor_id))

        date_from = params.get('date_from', '').strip()
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = params.get('date_to', '').strip()
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs.select_related('assigned_vendedor', 'created_by').order_by('company_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET

        # Repopulate filter values
        context['search_query'] = params.get('q', '')
        context['filter_status'] = params.get('status', '')
        context['filter_industry'] = params.get('industry', '')
        context['filter_vendedor'] = params.get('assigned_vendedor', '')
        context['filter_date_from'] = params.get('date_from', '')
        context['filter_date_to'] = params.get('date_to', '')

        # Vendedor list for admin/supervisor filter dropdown
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = self.request.user
        if user.role == 'administrator':
            context['vendedores'] = User.objects.filter(role='vendedor', is_active=True)
        elif user.role == 'supervisor':
            context['vendedores'] = user.get_team_members()
        else:
            context['vendedores'] = User.objects.none()

        return context


# ---------------------------------------------------------------------------
# 8.3 — ClientCreateView
# ---------------------------------------------------------------------------

class ClientCreateView(RoleRequiredMixin, CreateView):
    """
    Create a new client. Vendedores are auto-assigned as the owner.
    Administrators and supervisors can select any active vendedor.
    RoleRequiredMixin already extends LoginRequiredMixin.
    """
    model = Client
    form_class = ClientForm
    template_name = 'clientes/client_form.html'
    allowed_roles = ['administrator', 'vendedor', 'supervisor']
    success_url = reverse_lazy('clientes:client_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        client = form.save(commit=False)
        user = self.request.user

        # Auto-assign vendedor for vendedor role
        if user.role == 'vendedor':
            client.assigned_vendedor = user

        client.created_by = user
        client.save()
        messages.success(self.request, f'Cliente "{client.company_name}" creado exitosamente.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nuevo Cliente'
        context['form_action'] = 'Crear'
        return context


# ---------------------------------------------------------------------------
# 8.3 — ClientUpdateView
# ---------------------------------------------------------------------------

class ClientUpdateView(LoginRequiredMixin, OwnershipRequiredMixin, UpdateView):
    """
    Update an existing client. Only the assigned vendedor, their supervisor,
    or an administrator may edit.
    """
    model = Client
    form_class = ClientForm
    template_name = 'clientes/client_form.html'
    ownership_field = 'assigned_vendedor'
    success_url = reverse_lazy('clientes:client_list')

    def get_queryset(self):
        # Allow editing inactive clients too (use all_objects)
        return Client.all_objects.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        client = form.save()
        messages.success(self.request, f'Cliente "{client.company_name}" actualizado exitosamente.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Cliente: {self.object.company_name}'
        context['form_action'] = 'Guardar cambios'
        return context


# ---------------------------------------------------------------------------
# 8.4 — ClientDetailView with timeline
# ---------------------------------------------------------------------------

class ClientDetailView(LoginRequiredMixin, DetailView):
    """
    Full client profile with activity timeline, opportunities, and stats.
    """
    model = Client
    template_name = 'clientes/client_detail.html'
    context_object_name = 'client'

    def get_queryset(self):
        return Client.all_objects.select_related('assigned_vendedor', 'created_by')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        if user.role == 'administrator':
            return obj
        if user.role == 'supervisor':
            team_ids = list(user.get_team_members().values_list('id', flat=True))
            team_ids.append(user.id)
            if obj.assigned_vendedor_id in team_ids:
                return obj
            raise PermissionDenied('No tiene permisos para ver este cliente.')
        # vendedor
        if obj.assigned_vendedor == user:
            return obj
        raise PermissionDenied('No tiene permisos para ver este cliente.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object

        # Status history timeline
        context['status_history'] = client.status_history.select_related('changed_by').order_by('-changed_at')

        # Opportunities (graceful if ventas app not yet available)
        try:
            from ventas.models import Opportunity
            opportunities = Opportunity.all_objects.filter(client=client).select_related(
                'assigned_vendedor'
            ).order_by('-created_at')
            context['opportunities'] = opportunities

            # Stats
            total_opps = opportunities.count()
            won_opps = opportunities.filter(stage='cierre_ganado')
            total_revenue = won_opps.aggregate(total=Sum('estimated_value'))['total'] or 0
            closed_count = opportunities.filter(
                stage__in=['cierre_ganado', 'cierre_perdido']
            ).count()
            conversion_rate = (
                round(won_opps.count() / closed_count * 100, 1) if closed_count > 0 else 0
            )
            context['stats'] = {
                'total_opportunities': total_opps,
                'total_revenue': total_revenue,
                'conversion_rate': conversion_rate,
            }

            # Follow-ups (10 most recent)
            from ventas.models import FollowUp
            context['follow_ups'] = FollowUp.objects.filter(
                client=client
            ).select_related('created_by').order_by('-date')[:10]

        except ImportError:
            context['opportunities'] = []
            context['follow_ups'] = []
            context['stats'] = {
                'total_opportunities': 0,
                'total_revenue': 0,
                'conversion_rate': 0,
            }

        return context


# ---------------------------------------------------------------------------
# 8.5 — ClientDeleteView (soft delete)
# ---------------------------------------------------------------------------

class ClientDeleteView(LoginRequiredMixin, View):
    """
    Soft-delete a client: sets is_active=False and records a status history entry.
    Accepts POST only; confirmation is handled via a modal in the template.
    """

    def post(self, request, pk):
        client = get_object_or_404(Client.all_objects, pk=pk)
        user = request.user

        # Ownership check
        if user.role == 'vendedor' and client.assigned_vendedor != user:
            raise PermissionDenied('No tiene permisos para eliminar este cliente.')
        if user.role == 'supervisor':
            team_ids = list(user.get_team_members().values_list('id', flat=True))
            team_ids.append(user.id)
            if client.assigned_vendedor_id not in team_ids:
                raise PermissionDenied('No tiene permisos para eliminar este cliente.')

        if not client.is_active:
            messages.warning(request, 'Este cliente ya se encuentra inactivo.')
            return redirect('clientes:client_list')

        reason = request.POST.get('reason', '').strip()

        # Record status change
        ClientStatusHistory.objects.create(
            client=client,
            previous_status=True,
            new_status=False,
            changed_by=user,
            reason=reason,
        )

        client.is_active = False
        client.save()

        messages.success(request, f'Cliente "{client.company_name}" desactivado exitosamente.')
        return redirect('clientes:client_list')


# ---------------------------------------------------------------------------
# 8.2 — ClientSearchView (JSON autocomplete)
# ---------------------------------------------------------------------------

class ClientSearchView(LoginRequiredMixin, View):
    """
    Returns a JSON list of matching clients for autocomplete.
    Role-scoped, top 10 results.
    """

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse([], safe=False)

        qs = Client.objects.all()
        qs = _scope_clients_for_user(qs, request.user)

        id_filter = Q()
        if q.isdigit():
            id_filter = Q(id=int(q))

        qs = qs.filter(
            id_filter
            | Q(company_name__icontains=q)
            | Q(contact_name__icontains=q)
            | Q(email__icontains=q)
        ).values('id', 'company_name', 'contact_name', 'email')[:10]

        return JsonResponse(list(qs), safe=False)
