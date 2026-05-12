"""
URL configuration for dashboard app.
Temporary placeholder URLs for user authentication redirects.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Placeholder dashboard views (to be implemented in task 14)
    path('admin/', views.placeholder_dashboard, name='admin_dashboard'),
    path('supervisor/', views.placeholder_dashboard, name='supervisor_dashboard'),
    path('vendedor/', views.placeholder_dashboard, name='vendedor_dashboard'),
]
