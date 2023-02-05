import celery
from django.conf import settings

app = celery.Celery("crawler")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.timezone = settings.TIME_ZONE
app.conf.task_default_queue = "crawler"
app.conf.task_soft_time_limit = 10000
app.conf.task_time_limit = 10000
app.conf.worker_hijack_root_logger = False

app.conf.imports = ["crawler.utils"]
