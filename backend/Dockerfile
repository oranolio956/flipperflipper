FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download GeoIP database
RUN mkdir -p /app/geoip && \
    curl -L "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb" \
    -o /app/geoip/GeoLite2-City.mmdb

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 proxyuser && \
    chown -R proxyuser:proxyuser /app

USER proxyuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "proxy_tester:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]