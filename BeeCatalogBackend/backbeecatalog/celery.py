# backbeecatalog/celery.py

import os
import logging
from celery import Celery
from celery.signals import setup_logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
# Isso é importante tanto para o 'runserver' quanto para o 'worker'
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')

app = Celery('backbeecatalog')

# Configuração do Celery a partir do Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configurações adicionais de performance
app.conf.update(
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task settings
    task_compression='gzip',
    result_compression='gzip',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Configuração de logging estruturado para Celery
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)

# Auto-discover tasks
app.autodiscover_tasks()

# Configuração de filas dedicadas
app.conf.task_routes = {
    'api.tasks.generate_spreadsheet_task': {'queue': 'spreadsheet'},
    'api.tasks.scrape_images_task': {'queue': 'scraping'},
    'api.tasks.organizador_ia_task': {'queue': 'ai'},
    'api.tasks.generate_main_content_task': {'queue': 'ai'},
    'api.tasks.process_chunk_task': {'queue': 'ai'},
}

# Definição das filas
app.conf.task_default_queue = 'default'
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'spreadsheet': {
        'exchange': 'spreadsheet',
        'routing_key': 'spreadsheet',
    },
    'scraping': {
        'exchange': 'scraping',
        'routing_key': 'scraping',
    },
    'ai': {
        'exchange': 'ai',
        'routing_key': 'ai',
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
