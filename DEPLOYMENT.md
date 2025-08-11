# ProxyAssessmentTool - Production Deployment Guide

## 🚀 Quick Start (Development)

```bash
# Clone the repository
git clone https://github.com/oranolio956/flipperflipper.git
cd flipperflipper

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Run the backend
python proxy_tester.py

# Open frontend/index.html in your browser
```

## 🐳 Production Deployment with Docker

### 1. Prerequisites
- Docker and Docker Compose installed
- Domain name (for HTTPS)
- Server with at least 2GB RAM

### 2. Deploy with Docker Compose

```bash
# Clone the repository
git clone https://github.com/oranolio956/flipperflipper.git
cd flipperflipper/backend

# Create .env file
cat > .env << EOF
DB_PASSWORD=your_secure_password
GRAFANA_PASSWORD=your_grafana_password
API_DOMAIN=your-domain.com
EOF

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

### 3. Access Services
- **API**: http://localhost:8000
- **Frontend**: http://localhost:80
- **Grafana**: http://localhost:3000 (admin/your_password)
- **Prometheus**: http://localhost:9090

## ☁️ Cloud Deployment Options

### AWS EC2 Deployment

```bash
# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium or larger)

# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# 4. Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 5. Clone and deploy
git clone https://github.com/oranolio956/flipperflipper.git
cd flipperflipper/backend
sudo docker compose up -d
```

### DigitalOcean Deployment

```bash
# 1. Create Droplet (Ubuntu 22.04, 2GB RAM minimum)

# 2. SSH into droplet
ssh root@your-droplet-ip

# 3. Run setup script
curl -fsSL https://raw.githubusercontent.com/oranolio956/flipperflipper/main/setup.sh | bash
```

### Google Cloud Run Deployment

```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/proxy-tester

# 2. Deploy to Cloud Run
gcloud run deploy proxy-tester \
  --image gcr.io/YOUR_PROJECT/proxy-tester \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi
```

## 🔧 Configuration

### Backend Configuration
Edit `backend/config.py`:

```python
# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Redis Settings
REDIS_URL = "redis://localhost:6379"

# Database Settings
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/proxydb"

# Security
SECRET_KEY = "your-secret-key"
CORS_ORIGINS = ["https://your-domain.com"]
```

### Frontend Configuration
Edit `frontend/index.html`:

```javascript
const API_URL = 'https://api.your-domain.com';
```

## 🔒 SSL/HTTPS Setup

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Nginx Configuration

Create `/etc/nginx/sites-available/proxy-tester`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        root /var/www/proxy-tester;
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check API health
curl https://api.your-domain.com/health

# Check Docker containers
docker ps
docker-compose logs -f backend

# Check system resources
htop
docker stats
```

### Backup Database
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U proxyuser proxydb > backup.sql

# Restore
docker-compose exec -T postgres psql -U proxyuser proxydb < backup.sql
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check CORS settings
   - Ensure nginx is configured for WebSocket
   - Check firewall rules

2. **Slow Performance**
   - Increase worker count in Dockerfile
   - Add more Redis memory
   - Use connection pooling

3. **GeoIP Not Working**
   - Download fresh GeoIP database
   - Check file permissions

### Debug Mode
```bash
# Run backend in debug mode
docker-compose run --rm backend python proxy_tester.py --debug

# Check logs
docker-compose logs -f backend | grep ERROR
```

## 🎯 Production Best Practices

1. **Security**
   - Use strong passwords
   - Enable firewall (ufw)
   - Regular security updates
   - Use fail2ban for SSH

2. **Performance**
   - Enable Redis persistence
   - Use CDN for frontend
   - Implement rate limiting
   - Monitor resource usage

3. **Reliability**
   - Set up health checks
   - Configure auto-restart
   - Use monitoring (Grafana)
   - Regular backups

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/oranolio956/flipperflipper/issues
- Documentation: https://docs.your-domain.com