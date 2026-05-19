"""
URL configuration for dashboard app.
Includes the main dashboard view and JSON API endpoints for Chart.js data.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard view (all roles)
    path('', views.DashboardView.as_view(), name='index'),

    # Legacy role-based redirects (kept for backward compatibility)
    path('admin/', views.DashboardView.as_view(), name='admin_dashboard'),
    path('supervisor/', views.DashboardView.as_view(), name='supervisor_dashboard'),
    path('vendedor/', views.DashboardView.as_view(), name='vendedor_dashboard'),

    # Chart.js JSON API endpoints
    path('api/charts/revenue/', views.ChartRevenueAPIView.as_view(), name='chart_revenue'),
    path('api/charts/pipeline/', views.ChartPipelineAPIView.as_view(), name='chart_pipeline'),
    path('api/charts/clients/', views.ChartClientsAPIView.as_view(), name='chart_clients'),
    path('api/charts/vendedores/', views.ChartVendedoresAPIView.as_view(), name='chart_vendedores'),
]
