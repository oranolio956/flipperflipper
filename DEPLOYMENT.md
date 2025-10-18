# Production Deployment Guide (Oranolio RAT Web Interface)

This guide outlines a safe, reproducible way to run the web interface and (optionally) the C2 listener using open-source tools.

## 1) Prerequisites
- Linux host or VM
- Docker 24+ and Docker Compose v2
- Domain (optional but recommended) and DNS pointing to the host
- Open ports: 80/443 for web, 4040 for C2 (optional)

## 2) Environment
Create `.env` at repo root:

```
STITCH_ADMIN_USER=change_me
STITCH_ADMIN_PASSWORD=use_a_long_random_password
STITCH_SECRET_KEY=$(openssl rand -hex 32)
STITCH_ENABLE_HTTPS=true
STITCH_ALLOWED_ORIGINS=https://your-domain
STITCH_REDIS_URL=redis://redis:6379
# SAFE demo mode disables real C2 and payload generation
STITCH_SAFE_DEMO=false
```

## 3) Dockerfile

```
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Default to production-like run of web interface
CMD ["python", "web_app_real.py"]
```

## 4) docker-compose.yml

```
services:
  web:
    build: .
    image: oranolio:web
    restart: unless-stopped
    env_file: .env
    ports:
      - "5000:5000"
    depends_on:
      - redis
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
```

## 5) Reverse Proxy + TLS
Use Caddy (easy automatic TLS) or Nginx.

Example Caddyfile:

```
your-domain.com {
  reverse_proxy web:5000
}
```

Run Caddy as a sidecar or on the host; point it to `web:5000` (docker network) or `localhost:5000` if running locally.

## 6) Running

```
docker compose up -d --build
```

Visit: https://your-domain

## 7) Operations
- Metrics: enable with `STITCH_ENABLE_METRICS=true` and scrape `/metrics`
- Backups: `GET /api/backup` (protect with API keys)
- API Keys: enable with `STITCH_ENABLE_API_KEYS=true`

## 8) SAFE_DEMO Mode
If `STITCH_SAFE_DEMO=true`, the app:
- Does not start the C2 listener
- Returns simulated connections
- Generates a harmless text artifact instead of real payloads

## 9) Hardening
- Run behind a reverse proxy with TLS
- Set strict `STITCH_ALLOWED_ORIGINS`
- Keep `STITCH_DEBUG=false`
- Use long, unique admin credentials
- Enable Redis for shared rate limiting

## 10) Notes
- Building Windows `.exe` requires a Windows builder or Wine + PyInstaller; not included here.
- Real payload execution should only be performed in an isolated, authorized lab environment.
