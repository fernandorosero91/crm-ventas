"""
Views for the ventas (sales) app.
Implements opportunity CRUD, pipeline management, and follow-up tracking.
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
)
from .models import Opportunity, FollowUp, StageChange
from .services import get_opportunities_for_user, get_pipeline_summary


# ---------------------------------------------------------------------------
# Helper: scope opportunities to the requesting user's role
# ---------------------------------------------------------------------------

def _scope_opportunities_for_user(queryset, user):
    """
    Filter an Opportunity queryset according to the user's role.
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
# 15.1 + 15.2 + 15.3 + 15.4 — OpportunityListView with role-based filtering,
# pipeline summary cards, advanced table, and pagination
# ---------------------------------------------------------------------------

class OpportunityListView(LoginRequiredMixin, PaginationMixin, ListView):
    """
    Paginated list of opportunities with role-based scoping, pipeline summary,
    advanced filters, and sortable columns.
    
    Features:
    - Role-based data filtering (vendedor/supervisor/administrator)
    - Pipeline summary cards showing count per stage
    - Advanced table with sortable columns (title, client, value, stage, date)
    - Filters by stage, vendedor, client, date range, value range
    - Pagination with configurable page sizes (15/30/50)
    
    Validates: Requirements 15.1, 15.2, 15.3, 15.4
    """
    model = Opportunity
    template_name = 'ventas/opportunity_list.html'
    context_object_name = 'opportunities'

    def get_queryset(self):
        user = self.request.user
        params = self.request.GET

        # Base queryset with role-based scoping
        qs = get_opportunities_for_user(user)

        # Smart search (min 2 chars)
        q = params.get('q', '').strip()
        if len(q) >= 2:
            # Try numeric match for opportunity ID
            id_filter = Q()
            if q.isdigit():
                id_filter = Q(id=int(q))
            qs = qs.filter(
                id_filter
                | Q(title__icontains=q)
                | Q(client__company_name__icontains=q)
            )

        # Advanced filters
        stage = params.get('stage', '').strip()
        if stage:
            qs = qs.filter(stage=stage)

        vendedor_id = params.get('assigned_vendedor', '').strip()
        if vendedor_id and vendedor_id.isdigit():
            qs = qs.filter(assigned_vendedor_id=int(vendedor_id))

        client_id = params.get('client', '').strip()
        if client_id and client_id.isdigit():
            qs = qs.filter(client_id=int(client_id))

        date_from = params.get('date_from', '').strip()
        if date_from:
            qs = qs.filter(expected_close_date__gte=date_from)

        date_to = params.get('date_to', '').strip()
        if date_to:
            qs = qs.filter(expected_close_date__lte=date_to)

        value_min = params.get('value_min', '').strip()
        if value_min:
            try:
                qs = qs.filter(estimated_value__gte=float(value_min))
            except ValueError:
                pass

        value_max = params.get('value_max', '').strip()
        if value_max:
            try:
                qs = qs.filter(estimated_value__lte=float(value_max))
            except ValueError:
                pass

        # Sorting
        sort_by = params.get('sort', 'expected_close_date')
        sort_order = params.get('order', 'asc')
        
        valid_sort_fields = {
            'title': 'title',
            'client': 'client__company_name',
            'value': 'estimated_value',
            'stage': 'stage',
            'date': 'expected_close_date',
        }
        
        sort_field = valid_sort_fields.get(sort_by, 'expected_close_date')
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        
        return qs.select_related('client', 'assigned_vendedor').order_by(sort_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        params = self.request.GET

        # Pipeline summary cards (count per stage)
        queryset = self.get_queryset()
        pipeline_summary = get_pipeline_summary(user, queryset)
        context['pipeline_summary'] = pipeline_summary

        # Repopulate filter values
        context['search_query'] = params.get('q', '')
        context['filter_stage'] = params.get('stage', '')
        context['filter_vendedor'] = params.get('assigned_vendedor', '')
        context['filter_client'] = params.get('client', '')
        context['filter_date_from'] = params.get('date_from', '')
        context['filter_date_to'] = params.get('date_to', '')
        context['filter_value_min'] = params.get('value_min', '')
        context['filter_value_max'] = params.get('value_max', '')
        context['sort_by'] = params.get('sort', 'date')
        context['sort_order'] = params.get('order', 'asc')

        # Stage choices for filter dropdown
        context['stage_choices'] = Opportunity.STAGE_CHOICES

        # Vendedor list for admin/supervisor filter dropdown
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if user.role == 'administrator':
            context['vendedores'] = User.objects.filter(role='vendedor', is_active=True)
        elif user.role == 'supervisor':
            context['vendedores'] = user.get_team_members()
        else:
            context['vendedores'] = User.objects.none()

        # Client list for filter dropdown (role-scoped)
        from clientes.models import Client
        if user.role == 'administrator':
            context['clients'] = Client.objects.all()
        elif user.role == 'supervisor':
            team_ids = list(user.get_team_members().values_list('id', flat=True))
            team_ids.append(user.id)
            context['clients'] = Client.objects.filter(assigned_vendedor__in=team_ids)
        else:
            context['clients'] = Client.objects.filter(assigned_vendedor=user)

        return context


# ---------------------------------------------------------------------------
# 12.2 — OpportunityCreateView and OpportunityUpdateView
# ---------------------------------------------------------------------------

class OpportunityCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """
    Create a new sales opportunity.
    
    Features:
    - Forms with floating labels and real-time validation
    - estimated_value > 0, probability 0-100, expected_close_date not in past
    - Stage auto-set to 'prospeccion' on create
    - Client selector with search (role-scoped)
    - Auto-assigns vendedor if not specified
    
    Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5
    """
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'ventas/opportunity_form.html'
    success_url = reverse_lazy('ventas:opportunity_list')
    allowed_roles = ['vendedor', 'supervisor', 'administrator']

    def get_form_kwargs(self):
        """Pass the requesting user to the form for role-based scoping."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Set stage to 'prospeccion' and auto-assign vendedor if not specified.
        """
        opportunity = form.save(commit=False)
        
        # Ensure stage is 'prospeccion' for new opportunities
        opportunity.stage = 'prospeccion'
        
        # Auto-assign vendedor if not specified
        if not opportunity.assigned_vendedor:
            opportunity.assigned_vendedor = self.request.user
        
        opportunity.save()
        
        messages.success(
            self.request,
            f'Oportunidad "{opportunity.title}" creada exitosamente.'
        )
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Display error messages on form validation failure."""
        messages.error(
            self.request,
            'Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class OpportunityUpdateView(LoginRequiredMixin, OwnershipRequiredMixin, UpdateView):
    """
    Update an existing sales opportunity.
    
    Features:
    - Forms with floating labels and real-time validation
    - estimated_value > 0, probability 0-100, expected_close_date not in past
    - Client selector with search (role-scoped)
    - Ownership validation (vendedor can only edit own opportunities)
    
    Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5
    """
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'ventas/opportunity_form.html'
    ownership_field = 'assigned_vendedor'

    def get_success_url(self):
        """Redirect to opportunity detail page after successful update."""
        return reverse_lazy('ventas:opportunity_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        """Pass the requesting user to the form for role-based scoping."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save the updated opportunity and display success message."""
        opportunity = form.save()
        messages.success(
            self.request,
            f'Oportunidad "{opportunity.title}" actualizada exitosamente.'
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Display error messages on form validation failure."""
        messages.error(
            self.request,
            'Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


# ---------------------------------------------------------------------------
# 12.3 — OpportunityDetailView with stage management
# ---------------------------------------------------------------------------

class OpportunityDetailView(LoginRequiredMixin, DetailView):
    """
    Display full opportunity details with stage management.
    
    Features:
    - Full opportunity details with stage transition buttons
    - Stage change history timeline (chronological descending)
    - Associated follow-ups list (chronological descending)
    - Role-based access control
    
    Validates: Requirements 13.1, 14.4, 16.1
    """
    model = Opportunity
    template_name = 'ventas/opportunity_detail.html'
    context_object_name = 'opportunity'

    def get_queryset(self):
        """Apply role-based filtering to opportunity access."""
        user = self.request.user
        return _scope_opportunities_for_user(Opportunity.objects.all(), user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opportunity = self.object
        user = self.request.user

        # Stage change history (chronological descending)
        context['stage_changes'] = opportunity.stage_changes.select_related(
            'changed_by'
        ).order_by('-changed_at')

        # Associated follow-ups (chronological descending)
        context['follow_ups'] = opportunity.follow_ups.select_related(
            'created_by'
        ).order_by('-date')

        # Stage choices for transition buttons
        context['stage_choices'] = Opportunity.STAGE_CHOICES

        # Current stage info
        context['current_stage'] = opportunity.stage
        context['is_closed'] = opportunity.stage in ['cierre_ganado', 'cierre_perdido']

        # Permission flags
        context['can_edit'] = (
            user.role in ['administrator', 'supervisor']
            or opportunity.assigned_vendedor == user
        )
        context['can_change_stage'] = context['can_edit']
        context['can_move_backward'] = user.role in ['administrator', 'supervisor']

        return context


class OpportunityStageChangeView(LoginRequiredMixin, View):
    """
    Handle AJAX requests for stage transitions.
    
    Validates stage transition rules and creates audit records.
    Returns JSON response with success/error status.
    
    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8
    """
    def post(self, request, pk):
        """Process stage change request."""
        from .services import advance_stage
        from core.exceptions import StageTransitionError, InsufficientPermissionError
        import json

        try:
            # Get the opportunity with role-based scoping
            opportunity = get_object_or_404(
                _scope_opportunities_for_user(Opportunity.objects.all(), request.user),
                pk=pk
            )

            # Parse request data
            data = json.loads(request.body)
            new_stage = data.get('stage')
            actual_close_date = data.get('actual_close_date')
            loss_reason = data.get('loss_reason', '')

            # Attempt stage transition
            advance_stage(
                opportunity=opportunity,
                new_stage=new_stage,
                user=request.user,
                actual_close_date=actual_close_date,
                loss_reason=loss_reason
            )

            return JsonResponse({
                'success': True,
                'message': f'Etapa cambiada a {opportunity.get_stage_display()} exitosamente.',
                'new_stage': opportunity.stage,
                'new_stage_display': opportunity.get_stage_display(),
            })

        except (StageTransitionError, InsufficientPermissionError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Error inesperado al cambiar la etapa.'
            }, status=500)


# ---------------------------------------------------------------------------
# 12.4 — FollowUpCreateView
# ---------------------------------------------------------------------------

class FollowUpCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """
    Create a new follow-up record.
    
    Features:
    - Form with type selector, date picker, notes (min 10 chars), next_action_date
    - Can be linked to opportunity or client directly
    - Auto-assigns created_by to current user
    
    Validates: Requirements 14.1, 14.2, 14.3
    """
    model = FollowUp
    form_class = FollowUpForm
    template_name = 'ventas/followup_form.html'
    success_url = reverse_lazy('ventas:opportunity_list')
    allowed_roles = ['vendedor', 'supervisor', 'administrator']

    def get_form_kwargs(self):
        """Pass the requesting user to the form for role-based scoping."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-populate opportunity or client if provided in query params."""
        initial = super().get_initial()
        
        opportunity_id = self.request.GET.get('opportunity')
        if opportunity_id:
            try:
                opportunity = Opportunity.objects.get(pk=opportunity_id)
                initial['opportunity'] = opportunity
                initial['client'] = opportunity.client
            except Opportunity.DoesNotExist:
                pass
        
        client_id = self.request.GET.get('client')
        if client_id and not opportunity_id:
            try:
                from clientes.models import Client
                client = Client.objects.get(pk=client_id)
                initial['client'] = client
            except Client.DoesNotExist:
                pass
        
        return initial

    def form_valid(self, form):
        """Set created_by to current user and save."""
        follow_up = form.save(commit=False)
        follow_up.created_by = self.request.user
        follow_up.save()

        messages.success(
            self.request,
            'Seguimiento registrado exitosamente.'
        )

        # Redirect to opportunity detail if linked to opportunity
        if follow_up.opportunity:
            return redirect('ventas:opportunity_detail', pk=follow_up.opportunity.pk)
        
        # Otherwise redirect to client detail if linked to client
        if follow_up.client:
            return redirect('clientes:client_detail', pk=follow_up.client.pk)
        
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Display error messages on form validation failure."""
        messages.error(
            self.request,
            'Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class FollowUpUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing follow-up record.
    
    Only the creator or supervisor/administrator can edit.
    """
    model = FollowUp
    form_class = FollowUpForm
    template_name = 'ventas/followup_form.html'

    def get_queryset(self):
        """Restrict to follow-ups created by user or their team."""
        user = self.request.user
        if user.role == 'administrator':
            return FollowUp.objects.all()
        elif user.role == 'supervisor':
            team_ids = list(user.get_team_members().values_list('id', flat=True))
            team_ids.append(user.id)
            return FollowUp.objects.filter(created_by__in=team_ids)
        else:
            return FollowUp.objects.filter(created_by=user)

    def get_form_kwargs(self):
        """Pass the requesting user to the form for role-based scoping."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        """Redirect to opportunity or client detail page."""
        if self.object.opportunity:
            return reverse_lazy('ventas:opportunity_detail', kwargs={'pk': self.object.opportunity.pk})
        if self.object.client:
            return reverse_lazy('clientes:client_detail', kwargs={'pk': self.object.client.pk})
        return reverse_lazy('ventas:opportunity_list')

    def form_valid(self, form):
        """Save the updated follow-up and display success message."""
        follow_up = form.save()
        messages.success(
            self.request,
            'Seguimiento actualizado exitosamente.'
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Display error messages on form validation failure."""
        messages.error(
            self.request,
            'Por favor corrija los errores en el formulario.'
        )
        return super().form_invalid(form)


class FollowUpDeleteView(LoginRequiredMixin, View):
    """
    Soft delete a follow-up record (set is_active=False).
    
    Only the creator or supervisor/administrator can delete.
    """
    def post(self, request, pk):
        """Handle follow-up soft delete."""
        user = request.user
        
        # Get follow-up with permission check
        if user.role == 'administrator':
            follow_up = get_object_or_404(FollowUp, pk=pk)
        elif user.role == 'supervisor':
            team_ids = list(user.get_team_members().values_list('id', flat=True))
            team_ids.append(user.id)
            follow_up = get_object_or_404(FollowUp, pk=pk, created_by__in=team_ids)
        else:
            follow_up = get_object_or_404(FollowUp, pk=pk, created_by=user)

        # Soft delete
        follow_up.is_active = False
        follow_up.save()

        messages.success(request, 'Seguimiento eliminado exitosamente.')

        # Redirect to opportunity or client detail
        if follow_up.opportunity:
            return redirect('ventas:opportunity_detail', pk=follow_up.opportunity.pk)
        if follow_up.client:
            return redirect('clientes:client_detail', pk=follow_up.client.pk)
        return redirect('ventas:opportunity_list')


# ---------------------------------------------------------------------------
# 12.5 — Opportunity soft delete
# ---------------------------------------------------------------------------

class OpportunityDeleteView(LoginRequiredMixin, View):
    """
    Soft delete an opportunity (set is_active=False).
    
    Requires confirmation modal.
    Only owner or supervisor/administrator can delete.
    
    Validates: Requirements 16.2
    """
    def post(self, request, pk):
        """Handle opportunity soft delete."""
        user = request.user
        
        # Get opportunity with role-based scoping
        opportunity = get_object_or_404(
            _scope_opportunities_for_user(Opportunity.objects.all(), user),
            pk=pk
        )

        # Check ownership for vendedores
        if user.role == 'vendedor' and opportunity.assigned_vendedor != user:
            raise PermissionDenied('No tiene permisos para eliminar esta oportunidad.')

        # Soft delete
        opportunity.is_active = False
        opportunity.save()

        messages.success(
            request,
            f'Oportunidad "{opportunity.title}" eliminada exitosamente.'
        )
        return redirect('ventas:opportunity_list')


# ---------------------------------------------------------------------------
# Additional view: Pipeline visualization
# ---------------------------------------------------------------------------

class OpportunityPipelineView(LoginRequiredMixin, ListView):
    """
    Visual pipeline view showing opportunities grouped by stage.
    
    Provides a kanban-style board for drag-and-drop stage management.
    """
    model = Opportunity
    template_name = 'ventas/opportunity_pipeline.html'
    context_object_name = 'opportunities'

    def get_queryset(self):
        """Get opportunities with role-based scoping."""
        user = self.request.user
        return get_opportunities_for_user(user).select_related('client', 'assigned_vendedor')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        queryset = self.get_queryset()

        # Get pipeline summary
        pipeline_summary = get_pipeline_summary(user, queryset)
        context['pipeline_summary'] = pipeline_summary

        # Group opportunities by stage
        stages_with_opportunities = []
        for stage_info in pipeline_summary['stages']:
            stage_name = stage_info['name']
            stage_opportunities = queryset.filter(stage=stage_name)
            stages_with_opportunities.append({
                'name': stage_name,
                'display_name': stage_info['display_name'],
                'count': stage_info['count'],
                'total_value': stage_info['total_value'],
                'weighted_value': stage_info['weighted_value'],
                'opportunities': stage_opportunities,
            })

        context['stages_with_opportunities'] = stages_with_opportunities

        return context
