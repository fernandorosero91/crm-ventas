"""
Core views including custom error handlers.
"""
from django.shortcuts import render


def custom_403(request, exception=None):
    """Custom 403 Forbidden page."""
    return render(request, '403.html', status=403)


def custom_404(request, exception=None):
    """Custom 404 Not Found page."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 Internal Server Error page."""
    return render(request, '500.html', status=500)
