# api/history_urls.py

from django.urls import path
from .history_views import (
    CatalogHistoryView,
    ValidateMemoryView,
    DeleteMemoryView,
    MemoryStatsView
)

urlpatterns = [
    # Histórico de catalogação
    path('history/', CatalogHistoryView.as_view(), name='catalog_history'),
    
    # Validação de memória
    path('memory/validate/<str:product_id>/', ValidateMemoryView.as_view(), name='validate_memory'),
    
    # Exclusão de memória
    path('memory/delete/<str:product_id>/', DeleteMemoryView.as_view(), name='delete_memory'),
    
    # Estatísticas da memória
    path('memory/stats/', MemoryStatsView.as_view(), name='memory_stats'),
]