# api/import_urls.py

from django.urls import path
from .import_views import (
    SpreadsheetPreviewView,
    SpreadsheetImportView,
    SpreadsheetColumnsView,
    ImportHistoryView,
    ImportTemplateView
)

urlpatterns = [
    # Preview de planilha antes da importação
    path('spreadsheet/preview/', SpreadsheetPreviewView.as_view(), name='spreadsheet_preview'),
    
    # Importação de planilha para memória
    path('spreadsheet/import/', SpreadsheetImportView.as_view(), name='spreadsheet_import'),
    
    # Análise de colunas da planilha
    path('spreadsheet/columns/', SpreadsheetColumnsView.as_view(), name='spreadsheet_columns'),
    
    # Histórico e informações de importação
    path('import/history/', ImportHistoryView.as_view(), name='import_history'),
    
    # Download de template para importação
    path('import/template/', ImportTemplateView.as_view(), name='import_template'),
]