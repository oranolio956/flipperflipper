# Worker Deployment Guide

## Overview

This guide provides instructions for deploying the three backend workers (Privastra, Scheduler, and Scraper) with all the fixes applied to resolve deployment issues.

## Key Fixes Applied

### 1. Python Version Compatibility
- **Issue**: Greenlet build failure with Python 3.13
- **Fix**: Use Python 3.12 in Docker containers
- **File**: `worker.Dockerfile`

### 2. Syntax Error Fix
- **Issue**: SyntaxError in circuit_breaker.py at line 131
- **Fix**: Corrected the conditional statement syntax
- **File**: `app/core/circuit_breaker.py`

### 3. Dependency Management
- **Issue**: Missing or incompatible dependencies
- **Fix**: Created `worker-requirements.txt` with proper versions
- **File**: `worker-requirements.txt`

## Project Structure

```
/workspace/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── celery_app.py      # Celery configuration
│   │   ├── circuit_breaker.py  # Circuit breaker pattern
│   │   └── database.py         # Database configuration
│   └── workers/
│       ├── __init__.py
│       ├── startup.py          # Worker initialization
│       ├── privastra.py        # Privastra worker tasks
│       ├── scraper.py          # Scraper worker tasks
│       └── maintenance.py      # Maintenance tasks
├── worker.Dockerfile           # Docker configuration
├── worker-requirements.txt     # Python dependencies
└── docker-compose.workers.yml  # Docker Compose configuration
```

## Deployment Steps

### 1. Local Development

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r worker-requirements.txt

# Run Redis and PostgreSQL
docker-compose -f docker-compose.workers.yml up redis postgres

# Run workers
celery -A app.core.celery_app worker --loglevel=info
```

### 2. Docker Deployment

```bash
# Build and run all services
docker-compose -f docker-compose.workers.yml up --build

# Run in detached mode
docker-compose -f docker-compose.workers.yml up -d

# View logs
docker-compose -f docker-compose.workers.yml logs -f privastra-worker
docker-compose -f docker-compose.workers.yml logs -f scheduler
docker-compose -f docker-compose.workers.yml logs -f scraper
```

### 3. Production Deployment

#### Environment Variables

Create a `.env` file:

```env
# Database
DB_USER=proxyuser
DB_PASSWORD=secure_password_here
DB_NAME=proxydb
DATABASE_URL=postgresql+asyncpg://proxyuser:secure_password_here@postgres:5432/proxydb

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_URL=redis://redis:6379/1

# Flower (monitoring)
FLOWER_USER=admin
FLOWER_PASSWORD=secure_password_here

# Environment
ENVIRONMENT=production
```

#### Kubernetes Deployment

Create deployments for each worker:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privastra-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: privastra-worker
  template:
    metadata:
      labels:
        app: privastra-worker
    spec:
      containers:
      - name: worker
        image: your-registry/worker:latest
        command: ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info", "-Q", "privastra,default"]
        env:
        - name: CELERY_BROKER_URL
          value: redis://redis-service:6379/0
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Monitoring

### 1. Flower UI

Access Flower at http://localhost:5555 for real-time monitoring of:
- Active workers
- Task execution
- Queue status
- Worker performance

### 2. Health Checks

The system includes built-in health checks:

```python
# Check worker health
celery -A app.core.celery_app inspect ping

# Run health check task
from app.workers.maintenance import health_check
health_check.delay()
```

### 3. Logs

Configure centralized logging:

```python
# In app/core/celery_app.py
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
)
```

## Scaling

### Horizontal Scaling

```bash
# Scale specific worker type
docker-compose -f docker-compose.workers.yml up -d --scale scraper=3

# Or in Kubernetes
kubectl scale deployment scraper-worker --replicas=5
```

### Vertical Scaling

Adjust resources in `docker-compose.workers.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G  # Increase memory
    reservations:
      memory: 1G
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all __init__.py files are present
   - Check PYTHONPATH includes the app directory

2. **Connection Errors**
   - Verify Redis and PostgreSQL are running
   - Check environment variables are set correctly

3. **Memory Issues**
   - Monitor worker memory usage
   - Adjust `worker_max_tasks_per_child` in celery config

### Debug Commands

```bash
# Check worker status
celery -A app.core.celery_app inspect active

# Check registered tasks
celery -A app.core.celery_app inspect registered

# Purge all tasks
celery -A app.core.celery_app purge

# Monitor events
celery -A app.core.celery_app events
```

## Maintenance

### Regular Tasks

The system includes automated maintenance tasks:

- **Daily**: Cleanup old results, generate reports
- **Hourly**: Health checks
- **Weekly**: Database vacuum

### Manual Maintenance

```python
# Run cleanup manually
from app.workers.maintenance import cleanup_old_results
cleanup_old_results.delay()

# Vacuum database
from app.workers.maintenance import vacuum_database
vacuum_database.delay()
```

## Security Considerations

1. **Use secrets management** for production passwords
2. **Enable SSL/TLS** for Redis and PostgreSQL connections
3. **Implement rate limiting** for external API calls
4. **Use network policies** in Kubernetes
5. **Regular security updates** for dependencies

## Performance Optimization

1. **Connection Pooling**: Configured in database.py
2. **Circuit Breaker**: Prevents cascading failures
3. **Task Retry Logic**: Exponential backoff with jitter
4. **Batch Processing**: Available in scraper worker
5. **Resource Limits**: Set appropriate CPU/memory limits

## Conclusion

This deployment setup provides a robust, scalable solution for running backend workers with:
- Automatic error recovery
- Health monitoring
- Resource management
- Easy scaling
- Production-ready configurations

For additional support or custom requirements, refer to the individual component documentation.