"""
URL configuration for the ventas app.

Provides URL routing for:
- Opportunity CRUD operations (list, create, detail, update, delete)
- Follow-up registration and management
- Pipeline view for visual stage management
- Opportunity search and filtering

Requirements: 15.1
"""
from django.urls import path

from .views import (
    OpportunityListView,
    OpportunityCreateView,
    OpportunityDetailView,
    OpportunityUpdateView,
    OpportunityDeleteView,
    OpportunityStageChangeView,
    OpportunityPipelineView,
    FollowUpCreateView,
    FollowUpUpdateView,
    FollowUpDeleteView,
)

app_name = 'ventas'

urlpatterns = [
    # Opportunity CRUD paths
    path('', OpportunityListView.as_view(), name='opportunity_list'),
    path('nueva/', OpportunityCreateView.as_view(), name='opportunity_create'),
    path('<int:pk>/', OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('<int:pk>/editar/', OpportunityUpdateView.as_view(), name='opportunity_update'),
    path('<int:pk>/eliminar/', OpportunityDeleteView.as_view(), name='opportunity_delete'),
    path('<int:pk>/cambiar-etapa/', OpportunityStageChangeView.as_view(), name='opportunity_stage_change'),
    
    # Pipeline view for visual stage management
    path('pipeline/', OpportunityPipelineView.as_view(), name='opportunity_pipeline'),
    
    # Follow-up paths
    path('seguimiento/nuevo/', FollowUpCreateView.as_view(), name='followup_create'),
    path('seguimiento/<int:pk>/editar/', FollowUpUpdateView.as_view(), name='followup_update'),
    path('seguimiento/<int:pk>/eliminar/', FollowUpDeleteView.as_view(), name='followup_delete'),
]
