import os

from celery import Celery
from celery.signals import setup_logging

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('hireranker')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks([
    'tasks',
])

# Configure task routing
app.conf.task_routes = {
    'tasks.resume_tasks.parse_resume_task': {'queue': 'resumes'},
    'tasks.resume_tasks.process_candidate_batch': {'queue': 'resumes'},
    'tasks.resume_tasks.process_single_candidate_import': {'queue': 'resumes'},
    'tasks.evaluation_tasks.evaluate_candidate_task': {'queue': 'evaluations'},
    'tasks.evaluation_tasks.evaluate_project_candidates_task': {'queue': 'evaluations'},
    'tasks.evaluation_tasks.answer_recruiter_query_task': {'queue': 'evaluations'},
    'tasks.evaluation_tasks.generate_review_report_task': {'queue': 'evaluations'},
}

# Task serialization
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    # Retry defaults
    task_default_retry_delay=60,
    task_max_retries=3,
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    # Beat schedule (if using celery beat)
    beat_schedule={},
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery connectivity."""
    print(f'Request: {self.request!r}')
