"""
Views for the notifications app.
Provides list, mark-as-read, mark-all-read, and unread-count endpoints.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Paginated list of all notifications for the current user,
    ordered by most recent first.
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False,
        ).count()
        return context


class MarkAsReadView(LoginRequiredMixin, View):
    """
    Marks a single notification as read (POST only).
    Only the notification's recipient may mark it.
    Returns JSON: {"success": true}
    """

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return JsonResponse({'success': True})


class MarkAllReadView(LoginRequiredMixin, View):
    """
    Marks all unread notifications for the current user as read (POST only).
    Redirects back to the notification list.
    """

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return redirect('notifications:notification_list')


class GetUnreadCountView(LoginRequiredMixin, View):
    """
    Returns the unread notification count for the current user (GET).
    Used by the navbar dropdown to refresh the badge.
    Returns JSON: {"count": N}
    """

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return JsonResponse({'count': count})
