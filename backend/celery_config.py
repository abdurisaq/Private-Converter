# Celery configuration

import os
import sys


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'private-converter.settings')
from celery import Celery


app = Celery("private-converter", broker="redis://localhost:6379/0")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

print("Using Celery broker:", app.conf.broker_url)

# Windows compatibility: Use solo pool to avoid multiprocessing issues
if sys.platform == 'win32':
    app.conf.update(
        worker_pool='solo',
        worker_prefetch_multiplier=1,
        task_always_eager=False,
        task_eager_propagates=False,
    )

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

 