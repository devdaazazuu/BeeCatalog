# backbeecatalog/celery.py

import os
from celery import Celery
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
# Isso é importante tanto para o 'runserver' quanto para o 'worker'
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')

app = Celery('backbeecatalog')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
