"""
Views for the reports app.
Provides ReportView: filter form + preview table with role-based data scoping.
Export views (PDF, Excel, CSV) are implemented in tasks 16.2 and 16.3.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from .forms import ReportFilterForm
from .models import ReportLog


# ---------------------------------------------------------------------------
# Role-scoping helper
# ---------------------------------------------------------------------------

def _scope_for_user(queryset, user, vendedor_field='assigned_vendedor'):
    """Filter a queryset to records visible to the given user."""
    if user.role == 'administrator':
        return queryset
    if user.role == 'supervisor':
        team_ids = list(user.get_team_members().values_list('id', flat=True))
        team_ids.append(user.id)
        return queryset.filter(**{f'{vendedor_field}__in': team_ids})
    # vendedor
    return queryset.filter(**{vendedor_field: user})


# ---------------------------------------------------------------------------
# Query builders per report type
# ---------------------------------------------------------------------------

def _query_clients(filters, user):
    """Build a Client queryset. Returns (queryset, summary_dict)."""
    from clientes.models import Client

    status = filters.get('status', '')
    if status == 'inactive':
        qs = Client.all_objects.filter(is_active=False)
    elif status == 'active':
        qs = Client.objects.all()
    else:
        qs = Client.all_objects.all()

    qs = _scope_for_user(qs, user, 'assigned_vendedor')

    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    seller = filters.get('seller')
    if seller:
        qs = qs.filter(assigned_vendedor=seller)

    qs = qs.select_related('assigned_vendedor').order_by('company_name')

    total = qs.count()
    summary = {
        'total': total,
        'active': qs.filter(is_active=True).count(),
        'inactive': qs.filter(is_active=False).count(),
    }
    return qs, summary


def _query_opportunities(filters, user, closed_won_only=False):
    """Build an Opportunity queryset. Returns (queryset, summary_dict)."""
    from ventas.models import Opportunity

    qs = Opportunity.all_objects.all()
    if closed_won_only:
        qs = qs.filter(stage='cierre_ganado')

    qs = _scope_for_user(qs, user, 'assigned_vendedor')

    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    seller = filters.get('seller')
    if seller:
        qs = qs.filter(assigned_vendedor=seller)

    stage = filters.get('status', '')
    if stage and not closed_won_only:
        qs = qs.filter(stage=stage)

    qs = qs.select_related('client', 'assigned_vendedor').order_by('-created_at')

    agg = qs.aggregate(
        total_value=Sum('estimated_value'),
        total_weighted=Sum('weighted_value'),
        avg_probability=Avg('probability'),
    )
    summary = {
        'total': qs.count(),
        'total_value': agg['total_value'] or 0,
        'total_weighted': agg['total_weighted'] or 0,
        'avg_probability': round(agg['avg_probability'] or 0, 1),
    }
    return qs, summary


def _query_follow_ups(filters, user):
    """Build a FollowUp queryset. Returns (queryset, summary_dict)."""
    from ventas.models import FollowUp

    qs = FollowUp.objects.all()
    qs = _scope_for_user(qs, user, 'created_by')

    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if date_from:
        qs = qs.filter(date__date__gte=date_from)
    if date_to:
        qs = qs.filter(date__date__lte=date_to)

    seller = filters.get('seller')
    if seller:
        qs = qs.filter(created_by=seller)

    follow_up_type = filters.get('status', '')
    if follow_up_type:
        qs = qs.filter(follow_up_type=follow_up_type)

    qs = qs.select_related('client', 'opportunity', 'created_by').order_by('-date')

    by_type = qs.values('follow_up_type').annotate(count=Count('id'))
    summary = {
        'total': qs.count(),
        'by_type': {item['follow_up_type']: item['count'] for item in by_type},
    }
    return qs, summary


def _build_queryset(report_type, filters, user):
    """Dispatch to the correct query builder."""
    if report_type == 'clients':
        return _query_clients(filters, user)
    if report_type == 'opportunities':
        return _query_opportunities(filters, user)
    if report_type == 'sales':
        return _query_opportunities(filters, user, closed_won_only=True)
    if report_type == 'followups':
        return _query_follow_ups(filters, user)
    return [], {'total': 0}


def _log_report(user, report_type, export_format, filters, count):
    """Create a ReportLog entry for audit purposes."""
    serializable_filters = {}
    for k, v in filters.items():
        if v is None:
            continue
        if hasattr(v, 'pk'):
            serializable_filters[k] = v.pk
        elif hasattr(v, 'isoformat'):
            serializable_filters[k] = v.isoformat()
        else:
            serializable_filters[k] = str(v)

    ReportLog.objects.create(
        generated_by=user,
        report_type=report_type,
        export_format=export_format,
        filters_applied=serializable_filters,
        record_count=count,
    )


# ---------------------------------------------------------------------------
# Main report view
# ---------------------------------------------------------------------------

PREVIEW_PAGE_SIZE = 15


class ReportView(LoginRequiredMixin, FormView):
    """
    Renders the report filter form (GET) and processes it (POST).

    On POST with format == 'preview': renders the same page with a results table.
    On POST with format in ('pdf', 'excel', 'csv'): redirects to the export URL.
    """
    template_name = 'reports/report_filter.html'
    form_class = ReportFilterForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reportes'
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        report_type = data['report_type']
        fmt = data['format']
        user = self.request.user

        filters = {
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
            'seller': data.get('seller'),
            'status': data.get('status', ''),
        }

        # Redirect to export views for non-preview formats
        if fmt != 'preview':
            # Store filters in session for the export view to pick up
            self.request.session['report_filters'] = {
                'report_type': report_type,
                'date_from': str(filters['date_from']) if filters['date_from'] else '',
                'date_to': str(filters['date_to']) if filters['date_to'] else '',
                'seller_id': filters['seller'].pk if filters['seller'] else '',
                'status': filters['status'],
                'format': fmt,
            }
            from django.urls import reverse
            url_map = {
                'pdf': 'reports:export_pdf',
                'excel': 'reports:export_excel',
                'csv': 'reports:export_csv',
            }
            return redirect(reverse(url_map[fmt]))

        # Build queryset for preview
        results, summary = _build_queryset(report_type, filters, user)
        record_count = results.count() if hasattr(results, 'count') else len(results)

        # Log the report generation
        _log_report(user, report_type, 'preview', filters, record_count)

        # Paginate
        page_number = self.request.POST.get('page', 1)
        paginator = Paginator(results, PREVIEW_PAGE_SIZE)
        page_obj = paginator.get_page(page_number)

        context = self.get_context_data(form=form)
        context.update({
            'results': page_obj,
            'page_obj': page_obj,
            'summary': summary,
            'report_type': report_type,
            'filters_applied': filters,
            'record_count': record_count,
            'show_preview': True,
        })
        return self.render_to_response(context)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


# ---------------------------------------------------------------------------
# Export views (stubs — full implementation in tasks 16.2 and 16.3)
# ---------------------------------------------------------------------------

class _ExportBaseView(LoginRequiredMixin, View):
    """
    Base class for export views.
    Reads filter parameters from the session (set by ReportView on POST).
    """
    export_format = 'preview'

    def _get_filters_from_session(self, request):
        """Retrieve and reconstruct filter dict from session."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        session_data = request.session.get('report_filters', {})
        filters = {
            'report_type': session_data.get('report_type', 'clients'),
            'date_from': None,
            'date_to': None,
            'seller': None,
            'status': session_data.get('status', ''),
        }

        import datetime
        raw_from = session_data.get('date_from', '')
        raw_to = session_data.get('date_to', '')
        if raw_from:
            try:
                filters['date_from'] = datetime.date.fromisoformat(raw_from)
            except ValueError:
                pass
        if raw_to:
            try:
                filters['date_to'] = datetime.date.fromisoformat(raw_to)
            except ValueError:
                pass

        seller_id = session_data.get('seller_id', '')
        if seller_id:
            try:
                filters['seller'] = User.objects.get(pk=int(seller_id))
            except (User.DoesNotExist, ValueError):
                pass

        return filters

    def get(self, request):
        filters = self._get_filters_from_session(request)
        report_type = filters.pop('report_type', 'clients')
        results, _ = _build_queryset(report_type, filters, request.user)

        from django.conf import settings
        max_records = getattr(settings, 'EXPORT_MAX_RECORDS', 10000)
        count = results.count() if hasattr(results, 'count') else len(results)
        if count > max_records:
            from core.exceptions import ExportLimitExceededError
            raise ExportLimitExceededError(
                f'El reporte excede el límite de {max_records} registros.'
            )

        _log_report(request.user, report_type, self.export_format, filters, count)
        return self._generate_response(results, report_type, filters)

    def _generate_response(self, results, report_type, filters):
        raise NotImplementedError


class ExportPDFView(_ExportBaseView):
    """Generate and download a PDF report. Full implementation in task 16.2."""
    export_format = 'pdf'

    def _generate_response(self, results, report_type, filters):
        from .services import generate_pdf_report
        pdf_buffer = generate_pdf_report(results, report_type, filters, self.request.user)
        filename = f"reporte_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        from django.http import HttpResponse
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportExcelView(_ExportBaseView):
    """Generate and download an Excel report. Full implementation in task 16.3."""
    export_format = 'excel'

    def _generate_response(self, results, report_type, filters):
        from .services import generate_excel_export
        excel_buffer = generate_excel_export(results, report_type, filters)
        filename = f"reporte_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        from django.http import HttpResponse
        response = HttpResponse(
            excel_buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportCSVView(_ExportBaseView):
    """Generate and download a CSV report. Full implementation in task 16.3."""
    export_format = 'csv'

    def _generate_response(self, results, report_type, filters):
        from .services import generate_csv_export
        csv_content = generate_csv_export(results, report_type)
        filename = f"reporte_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        from django.http import HttpResponse
        response = HttpResponse(
            b'\xef\xbb\xbf' + csv_content.encode('utf-8'),
            content_type='text/csv; charset=utf-8',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
