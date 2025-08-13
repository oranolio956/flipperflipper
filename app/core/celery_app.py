import os
from celery import Celery
from kombu import Queue
from celery.schedules import crontab
from typing import Optional

# Get environment variables
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Create Celery instance
celery_app = Celery('app')

# Celery configuration
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.workers.privastra.*': {'queue': 'privastra'},
        'app.workers.scraper.*': {'queue': 'scraper'},
        'app.workers.scheduler.*': {'queue': 'default'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('privastra', routing_key='privastra'),
        Queue('scraper', routing_key='scraper'),
    ),
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Result backend configuration
    result_expires=3600,  # 1 hour
    result_compression='gzip',
    
    # Task execution configuration
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Beat schedule configuration
    beat_schedule={
        'cleanup-old-results': {
            'task': 'app.workers.maintenance.cleanup_old_results',
            'schedule': crontab(minute=0, hour=0),  # Daily at midnight
        },
        'health-check': {
            'task': 'app.workers.maintenance.health_check',
            'schedule': 60.0,  # Every minute
        },
    },
    
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)

# Set broker connection retry on startup
if ENVIRONMENT == 'production':
    celery_app.conf.broker_connection_retry_on_startup = True

# Import tasks after Celery app is configured
celery_app.autodiscover_tasks(['app.workers'])