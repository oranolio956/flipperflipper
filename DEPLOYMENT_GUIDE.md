# Enterprise Deployment Guide
## Production-Ready Deployment for Oranolio RAT - Elite C2 Framework

---

## 🚀 Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Python 3.10+ installed
- [ ] All dependencies from `requirements.txt` installed
- [ ] Environment variables configured
- [ ] SSL certificates obtained (Let's Encrypt recommended)
- [ ] Database backups configured
- [ ] Monitoring tools set up

### 2. Security Verification
- [ ] All default passwords changed
- [ ] SECRET_KEY set to cryptographically secure random value
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Security headers enabled
- [ ] HTTPS enforced
- [ ] Firewall rules configured

### 3. Performance Optimization
- [ ] Redis configured for session storage
- [ ] Static files served via CDN or nginx
- [ ] Database indexes created
- [ ] Logging configured
- [ ] Health checks enabled

---

## 📋 Environment Variables

Create a `.env` file in production:

```bash
# Flask Configuration
SECRET_KEY=<generate-with-python-secrets>
FLASK_ENV=production
FLASK_APP=main.py

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis (for sessions and caching)
REDIS_URL=redis://localhost:6379/0

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
SESSION_COOKIE_SECURE=True
WTF_CSRF_ENABLED=True

# Monitoring (Optional)
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/production.log

# CORS (if needed)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 🔧 Installation Steps

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/oranolio956/flipperflipper.git
cd flipperflipper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add this to your `.env` file as `SECRET_KEY`.

### 3. Initialize Databases

```bash
python3 initialize_databases.py
```

### 4. Generate Admin Setup Token

```bash
python3 -c "
from admin_setup import AdminSetupManager
manager = AdminSetupManager()
token = manager.generate_setup_token(expires_hours=24)
print(f'Admin Setup URL: https://yourdomain.com/admin/setup?token={token}')
"
```

---

## 🌐 Web Server Configuration

### Option 1: Nginx + Gunicorn (Recommended)

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Create systemd service
`/etc/systemd/system/oranolio.service`:

```ini
[Unit]
Description=Oranolio RAT Elite C2 Framework
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/flipperflipper
Environment="PATH=/var/www/flipperflipper/venv/bin"
ExecStart=/var/www/flipperflipper/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/var/www/flipperflipper/oranolio.sock \
    --timeout 120 \
    --access-logfile /var/log/oranolio/access.log \
    --error-logfile /var/log/oranolio/error.log \
    main:app

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
`/etc/nginx/sites-available/oranolio`:

```nginx
upstream oranolio {
    server unix:/var/www/flipperflipper/oranolio.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/oranolio_access.log;
    error_log /var/log/nginx/oranolio_error.log;

    # Max upload size
    client_max_body_size 16M;

    # Static files
    location /static {
        alias /var/www/flipperflipper/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://oranolio;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://oranolio;
        access_log off;
    }
}
```

#### Enable and Start Services

```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/oranolio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Enable and start application
sudo systemctl enable oranolio
sudo systemctl start oranolio
sudo systemctl status oranolio
```

---

## 🔒 SSL Certificate Setup

### Using Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

---

## 📊 Monitoring Setup

### Health Checks

The application provides several health check endpoints:

- `/health` - Basic health check
- `/health/detailed` - Detailed system metrics
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe
- `/metrics` - Prometheus metrics

### Uptime Monitoring

Configure external monitoring services:

1. **UptimeRobot** (Free)
   - Monitor: `https://yourdomain.com/health`
   - Interval: 5 minutes

2. **Pingdom** (Paid)
   - Monitor: `https://yourdomain.com/health`
   - Interval: 1 minute

3. **StatusCake** (Free tier available)
   - Monitor: `https://yourdomain.com/health`
   - Interval: 5 minutes

### Application Monitoring

#### Sentry (Error Tracking)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Add to .env
SENTRY_DSN=https://your-sentry-dsn
```

#### Prometheus (Metrics)

```bash
# Install Prometheus client
pip install prometheus-client

# Add to .env
PROMETHEUS_ENABLED=true

# Scrape endpoint: https://yourdomain.com/metrics
```

---

## 🗄️ Database Backup

### Automated Backup Script

Create `/usr/local/bin/backup-oranolio.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/oranolio"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/var/www/flipperflipper"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup databases
tar -czf $BACKUP_DIR/databases_$DATE.tar.gz \
    $APP_DIR/Application/admin_setup.db \
    $APP_DIR/data/*.db

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    $APP_DIR/.env \
    $APP_DIR/config.yaml

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Schedule with Cron

```bash
# Edit crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-oranolio.sh >> /var/log/oranolio-backup.log 2>&1
```

---

## 🔥 Firewall Configuration

### UFW (Ubuntu)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Fail2Ban (Brute Force Protection)

```bash
# Install fail2ban
sudo apt-get install fail2ban

# Create jail for application
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[oranolio-auth]
enabled = true
port = http,https
filter = oranolio-auth
logpath = /var/log/oranolio/error.log
maxretry = 5
bantime = 3600
```

---

## 📈 Performance Tuning

### Redis Configuration

```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Set maxmemory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
```

### Database Optimization

```bash
# For SQLite (if using)
# Run VACUUM periodically
python3 -c "
import sqlite3
for db in ['Application/admin_setup.db', 'data/email_auth.db', 'data/mfa_auth.db']:
    conn = sqlite3.connect(db)
    conn.execute('VACUUM')
    conn.close()
    print(f'Optimized {db}')
"
```

---

## 🧪 Testing Deployment

### 1. Health Check

```bash
curl https://yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Oranolio RAT - Elite C2 Framework",
  "timestamp": "2025-10-23T19:00:00.000000",
  "uptime_seconds": 123.45,
  "version": "1.0.0"
}
```

### 2. SSL Test

```bash
curl -I https://yourdomain.com
```

Check for:
- `Strict-Transport-Security` header
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

### 3. Load Test

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 https://yourdomain.com/health
```

---

## 🚨 Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u oranolio -n 50

# Check permissions
ls -la /var/www/flipperflipper

# Check Python environment
source /var/www/flipperflipper/venv/bin/activate
python3 -c "import flask; print(flask.__version__)"
```

### 502 Bad Gateway

```bash
# Check if application is running
sudo systemctl status oranolio

# Check socket file
ls -la /var/www/flipperflipper/oranolio.sock

# Check nginx error log
sudo tail -f /var/log/nginx/error.log
```

### High Memory Usage

```bash
# Check memory usage
free -h

# Check application memory
ps aux | grep gunicorn

# Restart application
sudo systemctl restart oranolio
```

---

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/oranolio956/flipperflipper/issues
- Documentation: See `PREMIUM_QUALITY_ASSURANCE.md`
- Health Check: `https://yourdomain.com/health/detailed`

---

## ✅ Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] Health check endpoint responding
- [ ] Admin setup completed
- [ ] Backups configured and tested
- [ ] Monitoring alerts configured
- [ ] SSL certificate auto-renewal tested
- [ ] Firewall rules verified
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on deployment

---

**Deployment Date**: _____________

**Deployed By**: _____________

**Production URL**: _____________

**Notes**: _____________
