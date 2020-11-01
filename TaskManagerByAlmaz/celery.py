import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TaskManagerByAlmaz.settings')

app = Celery('TaskManagerByAlmaz') # Here we must give a project name as an argument
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-tasks-every-minute': {
        'task': 'TaskManagerByAlmaz.tasks.check_tasks',
        'schedule': crontab(minute='*/1')
    },
}
