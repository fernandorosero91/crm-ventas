"""
URL configuration for the clientes app.
"""
from django.urls import path

from .views import (
    ClientCreateView,
    ClientDeleteView,
    ClientDetailView,
    ClientListView,
    ClientSearchView,
    ClientUpdateView,
)

app_name = 'clientes'

urlpatterns = [
    path('', ClientListView.as_view(), name='client_list'),
    path('nuevo/', ClientCreateView.as_view(), name='client_create'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('<int:pk>/editar/', ClientUpdateView.as_view(), name='client_update'),
    path('<int:pk>/eliminar/', ClientDeleteView.as_view(), name='client_delete'),
    path('buscar/', ClientSearchView.as_view(), name='client_search'),
]
