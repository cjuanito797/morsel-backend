import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slip_jab_eats_backend.settings')
app = Celery('slip_jab_eats_backend')

# load task modules
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

