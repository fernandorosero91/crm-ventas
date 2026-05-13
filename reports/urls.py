"""
URL configuration for the reports app.
"""
from django.urls import path

from .views import ReportView, ExportPDFView, ExportExcelView, ExportCSVView

app_name = 'reports'

urlpatterns = [
    path('', ReportView.as_view(), name='report_filter'),
    path('exportar/pdf/', ExportPDFView.as_view(), name='export_pdf'),
    path('exportar/excel/', ExportExcelView.as_view(), name='export_excel'),
    path('exportar/csv/', ExportCSVView.as_view(), name='export_csv'),
]
