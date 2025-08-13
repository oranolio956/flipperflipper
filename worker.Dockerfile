FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY worker-requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r worker-requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

# Set Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=true

# Default command (override in docker-compose or deployment)
CMD ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info"]