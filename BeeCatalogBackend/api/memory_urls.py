# api/memory_urls.py

from django.urls import path
from .memory_views import (
    ProductMemoryStatsView,
    ClearProductMemoryView,
    DeleteProductMemoryView,
    ExportProductMemoryView,
    ListProductsMemoryView,
    GetProductMemoryView,
    ForceRegenerateProductView,
    memory_health_check
)

urlpatterns = [
    # Estatísticas da memória
    path('memory/stats/', ProductMemoryStatsView.as_view(), name='memory_stats'),
    
    # Gerenciamento da memória
    path('memory/clear/', ClearProductMemoryView.as_view(), name='clear_memory'),
    path('memory/delete/', DeleteProductMemoryView.as_view(), name='delete_product_memory'),
    path('memory/export/', ExportProductMemoryView.as_view(), name='export_memory'),
    
    # Consulta de produtos na memória
    path('memory/list/', ListProductsMemoryView.as_view(), name='list_products_memory'),
    path('memory/get/', GetProductMemoryView.as_view(), name='get_product_memory'),
    
    # Regeneração forçada
    path('memory/force-regenerate/', ForceRegenerateProductView.as_view(), name='force_regenerate_product'),
    
    # Health check
    path('memory/health/', memory_health_check, name='memory_health_check'),
]