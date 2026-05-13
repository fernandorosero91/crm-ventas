"""
URL configuration for crm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


def health_check(request):
    """
    Simple health check endpoint for Dockploy and load balancers.
    Returns HTTP 200 with {"status": "ok"} when the application is running.
    """
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Health check for Dockploy (Requirements: 6.6)
    path('health/', health_check, name='health_check'),

    # Root redirect to login
    path('', RedirectView.as_view(url='/users/login/', permanent=False), name='home'),

    # App URL configurations (Requirements: 1.7)
    path('users/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('clientes/', include('clientes.urls')),
    path('ventas/', include('ventas.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls', namespace='reports')),
]

# Serve static and media files in development (Requirements: 1.7)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
