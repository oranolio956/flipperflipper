# 🚀 ProxyAssessmentTool - Quick Start Guide

## **Option 1: Fastest Local Deployment (2 minutes)**

### **Requirements**
- Python 3.7+
- 4GB RAM minimum
- Linux/macOS/Windows with WSL2

### **Deploy Now**
```bash
# 1. Clone repository (or use existing)
cd /workspace

# 2. Make deployment script executable
chmod +x deploy.sh

# 3. Deploy locally
./deploy.sh local
```

### **Access**
- 🌐 **Main App**: http://localhost:8080
- 📊 **Analytics Dashboard**: http://localhost:8080/analytics_dashboard.html
- 🔧 **API Docs**: http://localhost:8000/docs

## **Option 2: Docker Deployment (5 minutes)**

### **Requirements**
- Docker & Docker Compose
- 8GB RAM recommended

### **Deploy with Docker**
```bash
# 1. Deploy with Docker
./deploy.sh docker

# 2. Wait for services to start
# Check status: docker-compose -f docker-compose.production.yml ps
```

### **Access**
- 🌐 **App**: http://localhost
- 📊 **Grafana**: http://localhost:3000 (admin/admin)
- 📈 **Prometheus**: http://localhost:9090

## **Option 3: Cloud Deployment (10 minutes)**

### **Requirements**
- VPS with Ubuntu 20.04+
- 2GB+ RAM
- SSH access

### **Deploy to Cloud**
```bash
# 1. Set deployment variables
export DEPLOY_HOST=your-server.com
export DEPLOY_USER=ubuntu

# 2. Deploy
./deploy.sh cloud

# 3. Setup domain (optional)
# Point your domain to server IP
# SSL will be auto-configured
```

## **Testing the Deployment**

### **1. Test Proxy Discovery**
1. Open http://localhost:8080
2. Click "🔍 Auto-Discover Proxies"
3. Watch as proxies are discovered from multiple sources

### **2. Test Proxy Validation**
1. Discovered proxies appear in the list
2. Click "Start Testing" to validate them
3. Real-time results appear with:
   - ✅ Working status
   - 🌍 Geographic location
   - ⚡ Response time
   - 🔒 Anonymity level

### **3. View Analytics**
1. Open http://localhost:8080/analytics_dashboard.html
2. See real-time charts:
   - Performance over time
   - Geographic distribution
   - Response time histogram
   - Top performing proxies

## **Manual Testing (Without UI)**

### **Test Backend API Directly**
```bash
# 1. Discover proxies
curl http://localhost:8000/discover

# 2. Test a single proxy
curl -X POST http://localhost:8000/test/single \
  -H "Content-Type: application/json" \
  -d '{"ip": "1.2.3.4", "port": 8080, "protocol": "socks5"}'

# 3. Get analytics
curl http://localhost:8000/analytics
```

## **Troubleshooting**

### **Backend Won't Start**
```bash
# Check logs
tail -f logs/backend.log

# Install missing dependencies
cd backend && pip3 install -r requirements.txt

# Check port 8000 is free
lsof -i :8000
```

### **Frontend Issues**
```bash
# Check frontend is running
ps aux | grep "http.server"

# Restart frontend
cd frontend && python3 -m http.server 8080
```

### **Redis Connection Failed**
```bash
# Install Redis (optional, will use memory cache if not available)
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server --daemonize yes
```

## **Production Best Practices**

### **1. Use Environment Variables**
```bash
# Create .env file
cat > backend/.env << EOF
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/proxydb
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

### **2. Enable HTTPS**
```bash
# For cloud deployment
sudo certbot --nginx -d yourdomain.com
```

### **3. Set Resource Limits**
```yaml
# In docker-compose.production.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## **Advanced Features**

### **1. Enable SIEM Integration**
```python
# In backend/config.py
SIEM_CONNECTORS = {
    'splunk': {
        'enabled': True,
        'hec_url': 'https://splunk.company.com:8088',
        'hec_token': 'your-token'
    }
}
```

### **2. Configure Proxy Providers**
```python
# In backend/config.py
PROXY_PROVIDERS = {
    'brightdata': {
        'customer_id': 'your-id',
        'api_token': 'your-token'
    }
}
```

### **3. Enable ML Predictions**
```bash
# The ML model will auto-train after collecting enough data
# View predictions in the analytics dashboard
```

## **Performance Tuning**

### **For High Volume (1000+ proxies/minute)**
```bash
# 1. Increase worker threads
# In backend/proxy_tester.py
MAX_WORKERS = 100  # Default is 50

# 2. Enable connection pooling
# Already configured in Redis/PostgreSQL

# 3. Use dedicated Redis
docker run -d --name redis-proxy -p 6379:6379 redis:7-alpine
```

## **Monitoring**

### **View Real-time Metrics**
- **Grafana**: http://localhost:3000
  - Default dashboard shows:
    - Proxy success rates
    - Response times
    - Geographic distribution
    - System resources

### **Check Logs**
```bash
# All logs
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
```

## **Stop & Cleanup**

```bash
# Stop all services
./deploy.sh stop

# Remove Docker volumes (careful - deletes data!)
docker-compose -f docker-compose.production.yml down -v

# Clean logs
rm -rf logs/*
```

## **Need Help?**

1. **Check logs first**: `logs/backend.log`
2. **API Documentation**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/health

---

**🎉 You're now running a production-grade proxy assessment tool!**