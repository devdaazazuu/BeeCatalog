from django.urls import path, include
from .views import (
    SpreadsheetUploadView, 
    SpreadsheetGenerateView, 
    TaskStatusView, 
    ScrapeImagesView,
    OrganizadorIAView,
    ClearIACacheView
)

urlpatterns = [
    path('upload-planilha/', SpreadsheetUploadView.as_view(), name='upload-planilha'),
    path('scrape-images/', ScrapeImagesView.as_view(), name='scrape-images'),
    path('gerar-planilha/', SpreadsheetGenerateView.as_view(), name='gerar-planilha'),
    path('organizador-ia/', OrganizadorIAView.as_view(), name='organizador_ia'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('limpar-cache-ia/', ClearIACacheView.as_view(), name='limpar-cache-ia'),
    
    # URLs do sistema de memória inteligente
    path('', include('api.memory_urls')),
    
    # Spreadsheet Import System URLs
    path('', include('api.import_urls')),
    
    # Catalog History System URLs
    path('', include('api.history_urls')),
]
