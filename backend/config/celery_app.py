import os

import django
from celery import Celery
from django.conf import settings

from config.redis_url import patch_celery_redis_env_from_os

patch_celery_redis_env_from_os()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

app = Celery('meeting_transcriber')
app.config_from_object('django.conf:settings', namespace='CELERY')
# Ensure broker/result URIs match Django settings (handles rediss ssl_cert_reqs).
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery 5 + this layout: autodiscover often registers zero custom tasks; import binds them to `app`.
import apps.meetings.tasks  # noqa: E402, F401
