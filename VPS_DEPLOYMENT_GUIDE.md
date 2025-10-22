# 🚀 Complete Ubuntu VPS Deployment Guide - IONOS
**Elite RAT Framework Deployment on Ubuntu Server**

---

## ⚠️ LEGAL WARNING
This software is for **AUTHORIZED SECURITY TESTING ONLY**. You must have explicit written permission before deploying. Unauthorized use is illegal and unethical.

---

## 📋 Prerequisites

### What You Need Before Starting:
1. **IONOS VPS** with Ubuntu 20.04 or 22.04
2. **SSH Access** to your VPS (root or sudo user)
3. **Domain Name** (optional but recommended for SSL)
4. **GitHub Account** with repository access

---

## PART 1: Initial VPS Setup & Security

### Step 1: Connect to Your VPS via SSH

```bash
# Replace YOUR_VPS_IP with your actual IONOS VPS IP address
ssh root@YOUR_VPS_IP
```

### Step 2: Update System Packages

```bash
# Update package lists
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y build-essential wget curl git vim ufw fail2ban
```

### Step 3: Create a Non-Root User (Security Best Practice)

```bash
# Create new user (replace 'eliteuser' with your preferred username)
sudo adduser eliteuser

# Add user to sudo group
sudo usermod -aG sudo eliteuser

# Switch to new user
su - eliteuser
```

### Step 4: Configure Firewall (UFW)

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (CRITICAL - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application port (5000 for development, can remove later)
sudo ufw allow 5000/tcp

# Check firewall status
sudo ufw status verbose
```

### Step 5: Secure SSH Configuration

```bash
# Backup SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH config (recommended: disable root login)
sudo vim /etc/ssh/sshd_config
```

**Add/modify these lines:**
```
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
```

```bash
# Restart SSH service
sudo systemctl restart sshd
```

---

## PART 2: Install Python & Dependencies

### Step 6: Install Python 3.9+ and Pip

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Verify installation
python3 --version
pip3 --version

# Install additional build dependencies
sudo apt install -y libssl-dev libffi-dev python3-setuptools
```

### Step 7: Install System Dependencies

```bash
# Install dependencies for various Python packages
sudo apt install -y \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    libsqlite3-dev

# Install Node.js (if needed for frontend assets)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## PART 3: Clone Repository from GitHub

### Step 8: Set Up Git and SSH Keys

```bash
# Generate SSH key for GitHub (press Enter for defaults)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add SSH key to agent
ssh-add ~/.ssh/id_ed25519

# Display public key (copy this to GitHub)
cat ~/.ssh/id_ed25519.pub
```

**Add the SSH key to GitHub:**
1. Go to GitHub.com → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste your public key and save

### Step 9: Clone the Repository

```bash
# Create application directory
sudo mkdir -p /opt/elite-rat
sudo chown -R $USER:$USER /opt/elite-rat
cd /opt/elite-rat

# Clone repository (replace with your actual repo URL)
git clone git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git .

# Verify files
ls -la
```

---

## PART 4: Application Setup

### Step 10: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 11: Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn python-dotenv gevent gevent-websocket

# Verify installations
pip list
```

### Step 12: Configure Application Settings

```bash
# Create .env file for environment variables
nano /opt/elite-rat/.env
```

**Add the following to .env file:**
```bash
# Server Configuration
FLASK_APP=web_app_real.py
FLASK_ENV=production
FLASK_DEBUG=false

# C2 Configuration
ELITE_C2_HOST=your-domain.com
ELITE_C2_PORT=443
ELITE_C2_PROTOCOL=https

# Security Credentials (CHANGE THESE!)
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=YOUR_SUPER_SECURE_PASSWORD_HERE
STITCH_SECRET_KEY=$(openssl rand -hex 32)

# Encryption Key (generate with: openssl rand -hex 32)
ELITE_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Database
DATABASE_PATH=/opt/elite-rat/data/elite.db

# Optional Settings
ELITE_BEACON_INTERVAL=60
ELITE_ENABLE_EVASION=true
```

```bash
# Save and exit (Ctrl+X, Y, Enter)

# Make sure data directory exists
mkdir -p /opt/elite-rat/data
mkdir -p /opt/elite-rat/logs
mkdir -p /opt/elite-rat/keys
mkdir -p /opt/elite-rat/generated
```

### Step 13: Update config.yaml

```bash
# Edit configuration file
nano /opt/elite-rat/config.yaml
```

**Update these critical values:**
```yaml
c2:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 4444
  auth_token: "GENERATE_WITH_openssl_rand_hex_32"

webapp:
  host: "0.0.0.0"
  port: 5000
  secret_key: "GENERATE_WITH_openssl_rand_hex_32"
  admin_user: "admin"
  admin_password: "YOUR_SECURE_PASSWORD"

database:
  type: "sqlite"
  path: "/opt/elite-rat/data/elite.db"
```

---

## PART 5: SSL Certificate Setup

### Step 14: Install Certbot for Let's Encrypt SSL

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate SSL certificate (replace your-domain.com)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
```

**OR Generate Self-Signed Certificate (for testing):**

```bash
# Create SSL directory
sudo mkdir -p /opt/elite-rat/ssl

# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout /opt/elite-rat/ssl/key.pem \
    -out /opt/elite-rat/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Set permissions
sudo chown -R $USER:$USER /opt/elite-rat/ssl
chmod 600 /opt/elite-rat/ssl/key.pem
chmod 644 /opt/elite-rat/ssl/cert.pem
```

---

## PART 6: Nginx Reverse Proxy Setup

### Step 15: Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/elite-rat
```

**Add this Nginx configuration:**
```nginx
# Upstream Flask application
upstream flask_app {
    server 127.0.0.1:5000;
}

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Or for self-signed:
    # ssl_certificate /opt/elite-rat/ssl/cert.pem;
    # ssl_certificate_key /opt/elite-rat/ssl/key.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size
    client_max_body_size 100M;

    # Proxy Settings
    location / {
        proxy_pass http://flask_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeouts
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
    }

    # WebSocket support for Socket.IO
    location /socket.io/ {
        proxy_pass http://flask_app/socket.io/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Static files (if applicable)
    location /static/ {
        alias /opt/elite-rat/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Logging
    access_log /var/log/nginx/elite-rat-access.log;
    error_log /var/log/nginx/elite-rat-error.log;
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/elite-rat /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx to start on boot
sudo systemctl enable nginx
```

---

## PART 7: Create Systemd Service

### Step 16: Set Up Systemd Service for Auto-Start

```bash
# Create systemd service file
sudo nano /etc/systemd/system/elite-rat.service
```

**Add this service configuration:**
```ini
[Unit]
Description=Elite RAT Web Application
After=network.target

[Service]
Type=simple
User=eliteuser
Group=eliteuser
WorkingDirectory=/opt/elite-rat
Environment="PATH=/opt/elite-rat/venv/bin"
Environment="FLASK_ENV=production"

# Load environment variables from .env file
EnvironmentFile=/opt/elite-rat/.env

# Start with Gunicorn for production
ExecStart=/opt/elite-rat/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --worker-class gevent \
    --timeout 300 \
    --access-logfile /opt/elite-rat/logs/access.log \
    --error-logfile /opt/elite-rat/logs/error.log \
    --log-level info \
    web_app_real:app

# Restart policy
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable elite-rat

# Start the service
sudo systemctl start elite-rat

# Check service status
sudo systemctl status elite-rat

# View logs
sudo journalctl -u elite-rat -f
```

---

## PART 8: Monitoring & Maintenance

### Step 17: Set Up Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/elite-rat
```

**Add this configuration:**
```
/opt/elite-rat/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 eliteuser eliteuser
    sharedscripts
    postrotate
        systemctl reload elite-rat > /dev/null 2>&1 || true
    endscript
}
```

### Step 18: Install Monitoring Tools

```bash
# Install htop for process monitoring
sudo apt install -y htop

# Install monitoring
sudo apt install -y netdata

# Enable netdata
sudo systemctl enable netdata
sudo systemctl start netdata

# Access at: http://YOUR_VPS_IP:19999
```

---

## PART 9: Final Testing & Verification

### Step 19: Test the Application

```bash
# Check if application is running
sudo systemctl status elite-rat

# Check if port is listening
sudo netstat -tulpn | grep 5000

# Check Nginx
sudo systemctl status nginx

# Test local connection
curl -I http://localhost:5000

# Test external connection
curl -I https://your-domain.com
```

### Step 20: View Logs for Troubleshooting

```bash
# Application logs
tail -f /opt/elite-rat/logs/error.log
tail -f /opt/elite-rat/logs/access.log

# Systemd logs
sudo journalctl -u elite-rat -n 100 --no-pager

# Nginx logs
sudo tail -f /var/log/nginx/elite-rat-error.log
sudo tail -f /var/log/nginx/elite-rat-access.log
```

---

## PART 10: Common Commands Reference

### Application Management

```bash
# Start application
sudo systemctl start elite-rat

# Stop application
sudo systemctl stop elite-rat

# Restart application
sudo systemctl restart elite-rat

# View status
sudo systemctl status elite-rat

# View live logs
sudo journalctl -u elite-rat -f

# Restart Nginx
sudo systemctl restart nginx
```

### Git Updates

```bash
# Navigate to app directory
cd /opt/elite-rat

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart application
sudo systemctl restart elite-rat
```

### Firewall Management

```bash
# View firewall status
sudo ufw status numbered

# Allow port
sudo ufw allow PORT_NUMBER/tcp

# Deny port
sudo ufw deny PORT_NUMBER/tcp

# Delete rule
sudo ufw delete RULE_NUMBER

# Reload firewall
sudo ufw reload
```

---

## 🔒 Security Best Practices

### 1. Change Default Credentials
```bash
# Update .env file
nano /opt/elite-rat/.env
# Change STITCH_ADMIN_PASSWORD
```

### 2. Restrict SSH Access
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Enable fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Regular Updates
```bash
# Create update script
nano /opt/elite-rat/update.sh
```

**Add to update.sh:**
```bash
#!/bin/bash
cd /opt/elite-rat
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart elite-rat
echo "Update complete!"
```

```bash
# Make executable
chmod +x /opt/elite-rat/update.sh
```

### 4. Backup Script
```bash
# Create backup script
nano /opt/elite-rat/backup.sh
```

**Add to backup.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/elite-rat-backup-$DATE.tar.gz \
    /opt/elite-rat/data \
    /opt/elite-rat/.env \
    /opt/elite-rat/config.yaml

# Keep only last 7 backups
ls -t $BACKUP_DIR/elite-rat-backup-*.tar.gz | tail -n +8 | xargs rm -f
echo "Backup complete: $BACKUP_DIR/elite-rat-backup-$DATE.tar.gz"
```

```bash
# Make executable
chmod +x /opt/elite-rat/backup.sh

# Add to crontab for daily backups
crontab -e
# Add this line:
0 2 * * * /opt/elite-rat/backup.sh
```

---

## 🐛 Troubleshooting Guide

### Issue: Application Won't Start

```bash
# Check Python virtual environment
source /opt/elite-rat/venv/bin/activate
python --version

# Check dependencies
pip install -r requirements.txt

# Check permissions
sudo chown -R eliteuser:eliteuser /opt/elite-rat

# Check logs
sudo journalctl -u elite-rat -n 50
```

### Issue: Port Already in Use

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 PROCESS_ID

# Restart service
sudo systemctl restart elite-rat
```

### Issue: Database Errors

```bash
# Check database file
ls -la /opt/elite-rat/data/elite.db

# Fix permissions
sudo chown eliteuser:eliteuser /opt/elite-rat/data/elite.db
chmod 644 /opt/elite-rat/data/elite.db
```

### Issue: SSL Certificate Problems

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Test certificate
sudo certbot certificates

# Restart Nginx
sudo systemctl restart nginx
```

---

## 📊 Access Your Application

Once deployed, access your application at:

- **Production URL**: https://your-domain.com
- **Direct IP (dev)**: http://YOUR_VPS_IP:5000

**Default Login:**
- Username: `admin`
- Password: (as set in .env file)

---

## 🎯 IONOS-Specific Notes

### IONOS VPS Firewall (Cloud Panel)

In addition to UFW, you may need to configure IONOS Cloud Panel firewall:

1. Log into IONOS Cloud Panel
2. Navigate to your VPS
3. Go to "Firewall" settings
4. Add rules for ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)

### IONOS Domain Configuration

If using IONOS domain:

1. Go to IONOS Domain Management
2. Select your domain
3. Configure DNS Records:
   - **A Record**: `@` → `YOUR_VPS_IP`
   - **A Record**: `www` → `YOUR_VPS_IP`
4. Wait 15-30 minutes for DNS propagation

---

## ✅ Post-Deployment Checklist

- [ ] VPS updated and secured
- [ ] Firewall configured (UFW + IONOS)
- [ ] Non-root user created
- [ ] Python and dependencies installed
- [ ] Repository cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured with secure passwords
- [ ] SSL certificate generated
- [ ] Nginx configured and running
- [ ] Systemd service created and enabled
- [ ] Application running successfully
- [ ] Logs configured and rotating
- [ ] Backups scheduled
- [ ] Monitoring tools installed
- [ ] Application accessible via domain
- [ ] Login credentials work
- [ ] Fail2ban configured

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Certbot Documentation](https://certbot.eff.org/)
- [UFW Guide](https://help.ubuntu.com/community/UFW)
- [Systemd Services](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## ⚖️ Legal Reminder

**This deployment guide is provided for legitimate security testing purposes only.**

You MUST:
- ✅ Have written authorization
- ✅ Comply with all laws
- ✅ Maintain audit logs
- ✅ Use responsibly

You MUST NOT:
- ❌ Use without permission
- ❌ Access unauthorized systems
- ❌ Violate privacy laws

**Unauthorized use may result in criminal prosecution.**

---

## 📞 Support

If you encounter issues:
1. Check logs: `sudo journalctl -u elite-rat -n 100`
2. Review Nginx logs: `sudo tail -f /var/log/nginx/elite-rat-error.log`
3. Verify configurations
4. Check GitHub Issues

---

**Good luck with your deployment! 🚀**
