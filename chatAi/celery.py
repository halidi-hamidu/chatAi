import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatAi.settings')

app = Celery('chatAi')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-and-classify-every-5-minutes': {
        'task': 'chatAi.tasks.fetch_and_classify_messages',
        'schedule': crontab(minute='*/1'),  # every 1 minutes
    },
}
# Redis as both broker and result backend
app.conf.broker_url = 'redis://127.0.0.1:6379/0'
app.conf.result_backend = 'redis://127.0.0.1:6379/0'

# Optional: set task result expiration (in seconds)
app.conf.result_expires = 3600  # results expire after 1 hour
