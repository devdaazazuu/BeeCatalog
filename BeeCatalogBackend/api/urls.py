from django.urls import path
from .views import (
    SpreadsheetUploadView, 
    SpreadsheetGenerateView, 
    TaskStatusView, 
    ScrapeImagesView,
    OrganizadorIAView
)

urlpatterns = [
    path('upload-planilha/', SpreadsheetUploadView.as_view(), name='upload-planilha'),
    path('scrape-images/', ScrapeImagesView.as_view(), name='scrape-images'),
    path('gerar-planilha/', SpreadsheetGenerateView.as_view(), name='gerar-planilha'),
    path('organizador-ia/', OrganizadorIAView.as_view(), name='organizador_ia'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
]
