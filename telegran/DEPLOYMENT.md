# 🚀 Telegran Deployment Guide

Complete guide for deploying Telegran bot in production environments.

---

## 🎯 Deployment Options

### Option 1: Local Development / Testing
**Best for:** Testing and development
**Cost:** Free
**Uptime:** Manual (when your computer is on)

### Option 2: VPS / Cloud Server (Recommended)
**Best for:** Production use, 24/7 operation
**Cost:** $5-10/month
**Uptime:** 99.9%+

### Option 3: Container Platform (Docker)
**Best for:** Scalability and easy management
**Cost:** $10-20/month
**Uptime:** 99.9%+

### Option 4: Serverless (Advanced)
**Best for:** Cost optimization at scale
**Cost:** Pay-per-use (often free tier)
**Uptime:** 99.95%+

---

## 📦 Option 1: Quick Local Setup

Perfect for testing before production deployment.

```bash
# 1. Navigate to telegran folder
cd telegran

# 2. Run installation script
chmod +x install.sh
./install.sh

# 3. Start bot
source venv/bin/activate
python bot.py
```

**Keeping it running:**
```bash
# Use screen (keeps running when you disconnect)
screen -S telegran
python bot.py
# Press Ctrl+A then D to detach
# Reconnect with: screen -r telegran
```

---

## 🖥️ Option 2: VPS Deployment (DigitalOcean, AWS, etc.)

### 2.1 Choose a VPS Provider

**Recommended Providers:**
- **DigitalOcean** - $5/month, easy to use
- **Linode** - $5/month, excellent support
- **Vultr** - $5/month, global locations
- **AWS EC2** - Free tier available (12 months)
- **Google Cloud** - $300 free credit

**Minimum Requirements:**
- 1 GB RAM
- 1 CPU core
- 25 GB storage
- Ubuntu 20.04+ or Debian 11+

### 2.2 Server Setup

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git -y

# Create user for bot (security best practice)
sudo adduser telegran
sudo usermod -aG sudo telegran

# Switch to bot user
su - telegran

# Clone or upload your bot code
git clone https://github.com/your-repo/telegran.git
# OR upload via scp:
# scp -r telegran/ telegran@your-server:/home/telegran/

cd telegran

# Run installation
chmod +x install.sh
./install.sh
```

### 2.3 Configure as System Service

```bash
# Edit the service template
nano telegran.service.template

# Replace placeholders:
# YOUR_USERNAME -> telegran
# YOUR_GROUP -> telegran
# /path/to/telegran -> /home/telegran/telegran

# Copy to systemd
sudo cp telegran.service.template /etc/systemd/system/telegran.service

# Reload systemd
sudo systemctl daemon-reload

# Enable (start on boot)
sudo systemctl enable telegran

# Start the service
sudo systemctl start telegran

# Check status
sudo systemctl status telegran
```

### 2.4 Verify Deployment

```bash
# Check if bot is running
sudo systemctl status telegran

# View live logs
sudo journalctl -u telegran -f

# Check bot process
ps aux | grep bot.py
```

---

## 🐳 Option 3: Docker Deployment

### 3.1 Create Dockerfile

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 telegran && chown -R telegran:telegran /app
USER telegran

# Run bot
CMD ["python", "bot.py"]
```

### 3.2 Create docker-compose.yml

```yaml
version: '3.8'

services:
  telegran:
    build: .
    container_name: telegran-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3.3 Deploy with Docker

```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart
docker-compose restart
```

---

## ☁️ Option 4: Cloud Platform Deployment

### 4.1 Heroku Deployment

Create `Procfile`:
```
worker: python bot.py
```

Create `runtime.txt`:
```
python-3.10.12
```

Deploy:
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-telegran-bot

# Set environment variables
heroku config:set BOT_TOKEN=your_token_here

# Deploy
git push heroku main

# Scale worker
heroku ps:scale worker=1

# View logs
heroku logs --tail
```

### 4.2 Railway.app Deployment

1. Connect GitHub repository
2. Add environment variables in dashboard
3. Deploy automatically on push
4. View logs in web interface

### 4.3 Render.com Deployment

1. Connect repository
2. Choose "Background Worker" service
3. Set start command: `python bot.py`
4. Add environment variables
5. Deploy

---

## 🔒 Security Hardening

### Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Check status
sudo ufw status
```

### SSH Key Authentication

```bash
# Generate SSH key (on your local machine)
ssh-keygen -t ed25519 -C "telegran-bot"

# Copy to server
ssh-copy-id telegran@your-server-ip

# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### Keep System Updated

```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 📊 Monitoring & Maintenance

### Log Monitoring

```bash
# View systemd logs
sudo journalctl -u telegran -f

# View bot logs
tail -f /home/telegran/telegran/telegran.log

# View last 100 lines
sudo journalctl -u telegran -n 100
```

### Health Checks

Create `healthcheck.sh`:
```bash
#!/bin/bash
if systemctl is-active --quiet telegran; then
    echo "✅ Bot is running"
    exit 0
else
    echo "❌ Bot is down, restarting..."
    systemctl restart telegran
    exit 1
fi
```

Add to crontab:
```bash
# Check every 5 minutes
*/5 * * * * /home/telegran/telegran/healthcheck.sh >> /home/telegran/health.log 2>&1
```

### Automated Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/telegran/backups"
mkdir -p $BACKUP_DIR

# Backup config and logs
tar -czf $BACKUP_DIR/telegran_backup_$DATE.tar.gz \
    /home/telegran/telegran/config.json \
    /home/telegran/telegran/.env \
    /home/telegran/telegran/telegran.log

# Keep only last 7 days
find $BACKUP_DIR -name "telegran_backup_*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
# Backup daily at 3 AM
0 3 * * * /home/telegran/telegran/backup.sh
```

---

## 🔄 Updates & Maintenance

### Update Bot Code

```bash
# Stop bot
sudo systemctl stop telegran

# Backup current version
cp -r telegran telegran.backup.$(date +%Y%m%d)

# Pull updates
cd telegran
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart bot
sudo systemctl start telegran

# Check status
sudo systemctl status telegran
```

### Rollback if Issues

```bash
# Stop bot
sudo systemctl stop telegran

# Restore backup
rm -rf telegran
mv telegran.backup.YYYYMMDD telegran

# Restart
sudo systemctl start telegran
```

---

## 📈 Performance Optimization

### Memory Usage

```bash
# Monitor memory
watch -n 5 'ps aux | grep bot.py'

# If using too much memory, restart daily:
# Add to crontab:
0 4 * * * systemctl restart telegran
```

### Database Optimization (if using)

```bash
# Vacuum SQLite database monthly
0 0 1 * * sqlite3 /home/telegran/telegran/telegran.db 'VACUUM;'
```

---

## 🆘 Troubleshooting

### Bot Won't Start

```bash
# Check service status
sudo systemctl status telegran

# Check logs
sudo journalctl -u telegran -n 50

# Check environment
cd /home/telegran/telegran
source venv/bin/activate
python bot.py  # Run manually to see errors
```

### Bot Crashes Repeatedly

```bash
# Check system resources
free -h
df -h

# Check for errors in logs
grep -i error /home/telegran/telegran/telegran.log

# Increase restart delay in service file
RestartSec=30
```

### Can't Connect to Telegram

```bash
# Check internet connectivity
ping telegram.org

# Check firewall
sudo ufw status

# Test Telegram API
curl https://api.telegram.org/botYOUR_TOKEN/getMe
```

---

## 📞 Support & Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **python-telegram-bot docs**: https://python-telegram-bot.org/
- **DigitalOcean tutorials**: https://www.digitalocean.com/community/tutorials
- **systemd docs**: https://www.freedesktop.org/software/systemd/man/

---

## ✅ Deployment Checklist

- [ ] VPS/server provisioned
- [ ] Python 3.10+ installed
- [ ] Bot code deployed
- [ ] Dependencies installed
- [ ] .env configured with BOT_TOKEN
- [ ] config.json customized
- [ ] Bot added to Telegram group as admin
- [ ] systemd service configured
- [ ] Bot started and running
- [ ] Logs monitoring working
- [ ] Firewall configured
- [ ] Automatic updates enabled
- [ ] Backup system in place
- [ ] Health checks configured
- [ ] Documentation reviewed

---

**🎉 You're ready for production! The bot should now run 24/7 reliably.**
