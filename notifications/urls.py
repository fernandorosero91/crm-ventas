"""
URL configuration for the notifications app.
"""
from django.urls import path

from .views import (
    GetUnreadCountView,
    MarkAllReadView,
    MarkAsReadView,
    NotificationListView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', MarkAsReadView.as_view(), name='mark_as_read'),
    path('mark-all-read/', MarkAllReadView.as_view(), name='mark_all_read'),
    path('unread-count/', GetUnreadCountView.as_view(), name='unread_count'),
]
