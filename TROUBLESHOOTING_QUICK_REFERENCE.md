# 🔧 Quick Troubleshooting Reference Guide

## 🚨 Common Issues and Instant Fixes

---

## Issue 1: Can't Connect to VPS

### Symptoms:
- `Connection refused` or timeout when trying to SSH

### Quick Fix:
```bash
# Check IONOS Cloud Panel firewall - make sure port 22 is open
# Then try:
ssh -v root@YOUR_VPS_IP

# If using key:
ssh -i ~/.ssh/your_key root@YOUR_VPS_IP
```

---

## Issue 2: Application Won't Start

### Symptoms:
- Service fails to start
- Error in systemd logs

### Quick Check:
```bash
# Check service status
sudo systemctl status elite-rat

# View detailed logs
sudo journalctl -u elite-rat -n 100 --no-pager

# Check if Python environment is correct
cd /opt/elite-rat
source venv/bin/activate
python --version

# Test manually
cd /opt/elite-rat
source venv/bin/activate
python web_app_real.py
```

### Common Fixes:
```bash
# Fix 1: Reinstall dependencies
cd /opt/elite-rat
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Fix 2: Check file permissions
sudo chown -R eliteuser:eliteuser /opt/elite-rat
chmod -R 755 /opt/elite-rat

# Fix 3: Create missing directories
mkdir -p /opt/elite-rat/data
mkdir -p /opt/elite-rat/logs
mkdir -p /opt/elite-rat/keys

# Fix 4: Check .env file exists
ls -la /opt/elite-rat/.env
cat /opt/elite-rat/.env

# Restart service
sudo systemctl restart elite-rat
```

---

## Issue 3: Port 5000 Already in Use

### Symptoms:
- `Address already in use` error

### Quick Fix:
```bash
# Find process using port 5000
sudo lsof -i :5000

# Or
sudo netstat -tulpn | grep 5000

# Kill the process (replace PID)
sudo kill -9 PID

# Or kill all related processes
sudo pkill -f "gunicorn"
sudo pkill -f "web_app_real"

# Restart service
sudo systemctl restart elite-rat
```

---

## Issue 4: 502 Bad Gateway (Nginx Error)

### Symptoms:
- Nginx shows 502 error
- Can't access application through domain

### Quick Fix:
```bash
# Check if application is running
sudo systemctl status elite-rat

# Check if app is listening on port 5000
curl http://localhost:5000

# Check Nginx configuration
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/elite-rat-error.log

# Restart both services
sudo systemctl restart elite-rat
sudo systemctl restart nginx
```

---

## Issue 5: SSL Certificate Errors

### Symptoms:
- Browser shows SSL warning
- Certificate expired

### Quick Fix:
```bash
# For Let's Encrypt - check certificates
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Force renew
sudo certbot renew --force-renewal

# Restart Nginx
sudo systemctl restart nginx

# For self-signed - regenerate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout /opt/elite-rat/ssl/key.pem \
    -out /opt/elite-rat/ssl/cert.pem

sudo systemctl restart nginx
```

---

## Issue 6: Database Errors

### Symptoms:
- "Database is locked" error
- "Table doesn't exist" error

### Quick Fix:
```bash
# Check database file
ls -la /opt/elite-rat/data/elite.db

# Fix permissions
sudo chown eliteuser:eliteuser /opt/elite-rat/data/elite.db
chmod 644 /opt/elite-rat/data/elite.db

# If database is corrupted, backup and recreate
mv /opt/elite-rat/data/elite.db /opt/elite-rat/data/elite.db.backup
# Restart application (will create new database)
sudo systemctl restart elite-rat
```

---

## Issue 7: Can't Login to Web Interface

### Symptoms:
- Incorrect username/password
- Login page not loading

### Quick Fix:
```bash
# Check credentials in .env
cat /opt/elite-rat/.env | grep ADMIN

# Update credentials
nano /opt/elite-rat/.env
# Change STITCH_ADMIN_USER and STITCH_ADMIN_PASSWORD

# Restart application
sudo systemctl restart elite-rat

# Clear browser cache and try again
```

---

## Issue 8: Firewall Blocking Access

### Symptoms:
- Can SSH but can't access web application
- Connection timeout on HTTP/HTTPS

### Quick Fix:
```bash
# Check UFW status
sudo ufw status verbose

# Enable required ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# Check if ports are listening
sudo netstat -tulpn | grep -E '(80|443|5000)'

# IMPORTANT: Also check IONOS Cloud Panel firewall
# Log into IONOS → VPS → Firewall → Add rules for ports 80, 443
```

---

## Issue 9: Out of Memory

### Symptoms:
- Application crashes randomly
- OOM (Out of Memory) killer messages

### Quick Fix:
```bash
# Check memory usage
free -h

# Check which processes are using memory
ps aux --sort=-%mem | head

# Reduce Gunicorn workers
sudo nano /etc/systemd/system/elite-rat.service
# Change --workers 4 to --workers 2

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart elite-rat

# Add swap space (if needed)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Issue 10: Git Push/Pull Fails

### Symptoms:
- Can't pull updates from GitHub
- Authentication fails

### Quick Fix:
```bash
# Check if SSH key is added
ssh-add -l

# If not, add it
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Test GitHub connection
ssh -T git@github.com

# If still failing, check remote URL
cd /opt/elite-rat
git remote -v

# Update to SSH URL if using HTTPS
git remote set-url origin git@github.com:USERNAME/REPO.git
```

---

## Issue 11: DNS Not Resolving

### Symptoms:
- Domain doesn't point to VPS
- DNS_PROBE_FINISHED_NXDOMAIN error

### Quick Fix:
```bash
# Check DNS propagation
nslookup your-domain.com

# Check if domain points to correct IP
dig your-domain.com

# IONOS DNS Setup:
# 1. Log into IONOS Control Panel
# 2. Go to Domains → Your Domain → DNS Settings
# 3. Add A Record:
#    Host: @ → Points to: YOUR_VPS_IP
#    Host: www → Points to: YOUR_VPS_IP
# 4. Wait 15-30 minutes for propagation
```

---

## Issue 12: Nginx Won't Start

### Symptoms:
- Nginx service failed
- Port conflict errors

### Quick Fix:
```bash
# Check Nginx configuration
sudo nginx -t

# If syntax error, check config file
sudo nano /etc/nginx/sites-available/elite-rat

# Check if another service is using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx

# If still failing, check if Apache is running
sudo systemctl stop apache2
sudo systemctl disable apache2
```

---

## 📊 Essential Monitoring Commands

### Check Everything Status:
```bash
# All services
sudo systemctl status elite-rat nginx fail2ban

# All ports
sudo netstat -tulpn | grep -E '(22|80|443|5000)'

# Disk space
df -h

# Memory
free -h

# CPU and processes
htop
```

### View All Logs:
```bash
# Application logs
sudo journalctl -u elite-rat -f

# Nginx access logs
sudo tail -f /var/log/nginx/elite-rat-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/elite-rat-error.log

# System logs
sudo tail -f /var/log/syslog

# Application error logs
tail -f /opt/elite-rat/logs/error.log
```

### Test Connections:
```bash
# Test local application
curl http://localhost:5000

# Test Nginx locally
curl http://localhost

# Test external domain
curl https://your-domain.com

# Test with headers
curl -I https://your-domain.com

# Test SSL
openssl s_client -connect your-domain.com:443
```

---

## 🔄 Quick Restart Everything

```bash
# Complete restart sequence
sudo systemctl stop elite-rat
sudo systemctl stop nginx
sudo systemctl start nginx
sudo systemctl start elite-rat

# Check status
sudo systemctl status elite-rat nginx

# View logs
sudo journalctl -u elite-rat -n 20
```

---

## 🧹 Clean Up and Reset

### If everything is broken, reset:
```bash
# Stop services
sudo systemctl stop elite-rat
sudo systemctl stop nginx

# Remove old virtual environment
cd /opt/elite-rat
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Fix permissions
sudo chown -R $USER:$USER /opt/elite-rat

# Restart services
sudo systemctl daemon-reload
sudo systemctl start elite-rat
sudo systemctl start nginx
```

---

## 🆘 Emergency Recovery

### Complete System Reset:
```bash
# Backup critical data first
cp /opt/elite-rat/.env ~/env.backup
cp /opt/elite-rat/data/elite.db ~/database.backup

# Stop services
sudo systemctl stop elite-rat nginx

# Remove and re-clone
sudo rm -rf /opt/elite-rat
sudo mkdir -p /opt/elite-rat
sudo chown -R $USER:$USER /opt/elite-rat
cd /opt/elite-rat
git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git .

# Restore .env
cp ~/env.backup /opt/elite-rat/.env

# Recreate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Restore database
cp ~/database.backup /opt/elite-rat/data/elite.db

# Restart everything
sudo systemctl daemon-reload
sudo systemctl start elite-rat nginx
```

---

## 📞 Get Help

### Gather Information for Support:
```bash
# Create diagnostic report
cat > ~/diagnostic_report.txt << EOF
=== System Info ===
$(uname -a)
$(lsb_release -a)

=== Service Status ===
$(sudo systemctl status elite-rat --no-pager)

=== Recent Logs ===
$(sudo journalctl -u elite-rat -n 50 --no-pager)

=== Nginx Status ===
$(sudo systemctl status nginx --no-pager)

=== Port Status ===
$(sudo netstat -tulpn | grep -E '(80|443|5000)')

=== Disk Space ===
$(df -h)

=== Memory ===
$(free -h)

=== Firewall ===
$(sudo ufw status verbose)
EOF

# View report
cat ~/diagnostic_report.txt
```

---

## 🎯 Performance Issues

### Application is Slow:
```bash
# Check resource usage
htop

# Increase workers (if you have memory)
sudo nano /etc/systemd/system/elite-rat.service
# Change --workers 4 to --workers 8

# Enable caching in Nginx
sudo nano /etc/nginx/sites-available/elite-rat
# Add under server block:
# proxy_cache_valid 200 1h;
# proxy_cache_bypass $http_pragma $http_authorization;

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart elite-rat nginx
```

---

## ✅ Health Check Script

Create a health check script:

```bash
cat > /opt/elite-rat/health_check.sh << 'EOF'
#!/bin/bash
echo "=== Elite RAT Health Check ==="
echo ""

# Check service
if systemctl is-active --quiet elite-rat; then
    echo "✅ Service: Running"
else
    echo "❌ Service: Not Running"
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: Running"
else
    echo "❌ Nginx: Not Running"
fi

# Check port 5000
if sudo lsof -i :5000 > /dev/null 2>&1; then
    echo "✅ Port 5000: Listening"
else
    echo "❌ Port 5000: Not Listening"
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✅ Disk: ${DISK_USAGE}% used"
else
    echo "⚠️  Disk: ${DISK_USAGE}% used (Getting full!)"
fi

# Check memory
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
if [ $MEM_USAGE -lt 80 ]; then
    echo "✅ Memory: ${MEM_USAGE}% used"
else
    echo "⚠️  Memory: ${MEM_USAGE}% used (Getting high!)"
fi

echo ""
echo "=== End Health Check ==="
EOF

chmod +x /opt/elite-rat/health_check.sh
```

Run health check:
```bash
/opt/elite-rat/health_check.sh
```

---

**Remember: Most issues can be solved by checking logs first!**

```bash
sudo journalctl -u elite-rat -f
```
