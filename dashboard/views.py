"""
Dashboard views module.
Provides the main dashboard view with KPI cards and JSON API endpoints for Chart.js graphs.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .services import (
    get_kpi_data,
    get_monthly_revenue,
    get_opportunities_by_stage,
    get_monthly_new_clients,
    get_top_vendedores,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view displaying KPI cards.
    Chart data is loaded asynchronously via the JSON API endpoints.
    All authenticated users (any role) can access the dashboard.
    """
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kpi'] = get_kpi_data(self.request.user)
        context['current_year'] = timezone.now().year
        return context


class ChartRevenueAPIView(LoginRequiredMixin, View):
    """
    JSON API endpoint for monthly revenue bar chart.
    Returns labels (month names in Spanish) and datasets compatible with Chart.js.
    URL: /api/charts/revenue/
    """

    def get(self, request):
        year = request.GET.get('year', timezone.now().year)
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = timezone.now().year

        data = get_monthly_revenue(request.user, year)

        month_labels = [
            'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ]

        return JsonResponse({
            'labels': month_labels,
            'datasets': [{
                'label': 'Ingresos Mensuales',
                'data': [float(item['revenue']) for item in data],
                'backgroundColor': '#2c6e8a',
                'borderColor': '#1e3a5f',
                'borderWidth': 1,
            }]
        })


class ChartPipelineAPIView(LoginRequiredMixin, View):
    """
    JSON API endpoint for opportunities by stage doughnut chart.
    Returns labels (stage names in Spanish) and datasets compatible with Chart.js.
    URL: /api/charts/pipeline/
    """

    STAGE_LABELS = {
        'prospeccion': 'Prospección',
        'calificacion': 'Calificación',
        'propuesta': 'Propuesta',
        'negociacion': 'Negociación',
    }

    def get(self, request):
        data = get_opportunities_by_stage(request.user)

        labels = [self.STAGE_LABELS.get(item['stage'], item['stage']) for item in data]
        values = [item['count'] for item in data]

        colors = ['#1e3a5f', '#2c6e8a', '#10b981', '#4a4a4a']

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Oportunidades por Etapa',
                'data': values,
                'backgroundColor': colors[:len(values)],
                'borderColor': '#ffffff',
                'borderWidth': 2,
            }]
        })


class ChartClientsAPIView(LoginRequiredMixin, View):
    """
    JSON API endpoint for new clients per month line chart.
    Returns labels (month names in Spanish) and datasets compatible with Chart.js.
    URL: /api/charts/clients/
    """

    def get(self, request):
        year = request.GET.get('year', timezone.now().year)
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = timezone.now().year

        data = get_monthly_new_clients(request.user, year)

        month_labels = [
            'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ]

        return JsonResponse({
            'labels': month_labels,
            'datasets': [{
                'label': 'Nuevos Clientes',
                'data': [item['count'] for item in data],
                'borderColor': '#10b981',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                'borderWidth': 2,
                'fill': True,
                'tension': 0.3,
            }]
        })


class ChartVendedoresAPIView(LoginRequiredMixin, View):
    """
    JSON API endpoint for top vendedores horizontal bar chart.
    Returns labels (vendedor names) and datasets compatible with Chart.js.
    URL: /api/charts/vendedores/
    """

    def get(self, request):
        data = get_top_vendedores(limit=5)

        labels = [item['vendedor_name'] for item in data]
        values = [float(item['total_revenue']) for item in data]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Ingresos por Vendedor',
                'data': values,
                'backgroundColor': '#1e3a5f',
                'borderColor': '#2c6e8a',
                'borderWidth': 1,
            }]
        })
