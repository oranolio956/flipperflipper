#!/bin/bash
# Automated Deployment Script for Stitch RAT on VPS
# Run this script on your VPS after uploading the code

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="50.21.187.77"
APP_USER="stitchrat"
APP_DIR="/opt/stitchrat"
ADMIN_PASSWORD="StitchRAT_SecurePass_2025!"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stitch RAT VPS Deployment Script     ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
apt install -y python3 python3-pip python3-venv git nginx supervisor ufw
apt install -y build-essential libssl-dev libffi-dev python3-dev
apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev
apt install -y libwebp-dev tcl8.6-dev tk8.6-dev python3-tk
apt install -y redis-server htop curl wget unzip

echo -e "${YELLOW}Step 3: Creating application user and directories...${NC}"
# Create user if doesn't exist
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    echo -e "${GREEN}Created user: $APP_USER${NC}"
fi

# Create application directory
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# Create required subdirectories
sudo -u $APP_USER mkdir -p $APP_DIR/{logs,uploads,downloads,temp,certs}

echo -e "${YELLOW}Step 4: Setting up Python virtual environment...${NC}"
sudo -u $APP_USER python3 -m venv $APP_DIR/venv

echo -e "${YELLOW}Step 5: Installing Python dependencies...${NC}"
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
else
    echo -e "${RED}requirements.txt not found! Make sure you've uploaded the code first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 6: Creating environment configuration...${NC}"
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
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

echo -e "${YELLOW}Step 7: Configuring Nginx reverse proxy...${NC}"
cat > /etc/nginx/sites-available/stitchrat << 'EOF'
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

server {
    listen 80;
    server_name 50.21.187.77;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 50.21.187.77;
    
    # SSL Configuration
    ssl_certificate /opt/stitchrat/certs/cert.pem;
    ssl_private_key /opt/stitchrat/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Hide server version
    server_tokens off;
    
    # Client body size limit
    client_max_body_size 100M;
    
    # Rate limiting for login
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Static files with caching
    location /static/ {
        alias /opt/stitchrat/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000;
    }
}
EOF

# Enable the site and remove default
ln -sf /etc/nginx/sites-available/stitchrat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

echo -e "${YELLOW}Step 8: Creating systemd service...${NC}"
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

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}Step 9: Configuring firewall...${NC}"
# Configure UFW firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing

# Allow essential services
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8443/tcp comment 'Plesk'
ufw allow 4040/tcp comment 'RAT Server'

# Allow Redis (local only)
ufw allow from 127.0.0.1 to any port 6379

echo -e "${YELLOW}Step 10: Starting services...${NC}"
# Start and enable Redis
systemctl enable redis-server
systemctl start redis-server

# Reload systemd and start services
systemctl daemon-reload
systemctl enable stitchrat
systemctl enable nginx

# Start Nginx first (it will fail initially due to missing SSL certs, but that's OK)
systemctl start nginx || true

# Start the application (it will generate SSL certs)
systemctl start stitchrat

# Wait a moment for SSL certs to be generated
sleep 5

# Restart Nginx now that SSL certs exist
systemctl restart nginx

echo -e "${YELLOW}Step 11: Setting up log rotation...${NC}"
cat > /etc/logrotate.d/stitchrat << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload stitchrat
    endscript
}
EOF

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

chmod +x /usr/local/bin/stitchrat-status
chmod +x /usr/local/bin/stitchrat-restart

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!                  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access Information:${NC}"
echo -e "Web Interface: ${GREEN}https://$VPS_IP${NC}"
echo -e "Admin Username: ${GREEN}admin${NC}"
echo -e "Admin Password: ${GREEN}$ADMIN_PASSWORD${NC}"
echo -e "RAT Server Port: ${GREEN}4040${NC}"
echo -e "Plesk Panel: ${GREEN}https://$VPS_IP:8443${NC}"
echo ""
echo -e "${BLUE}Management Commands:${NC}"
echo -e "Check Status: ${GREEN}stitchrat-status${NC}"
echo -e "Restart Services: ${GREEN}stitchrat-restart${NC}"
echo -e "View Logs: ${GREEN}journalctl -u stitchrat -f${NC}"
echo ""
echo -e "${YELLOW}Important Security Notes:${NC}"
echo -e "1. Change the admin password in $APP_DIR/.env"
echo -e "2. This tool is for authorized penetration testing only"
echo -e "3. Ensure you have proper legal authorization"
echo -e "4. Consider restricting firewall access to specific IPs"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. Test the web interface at https://$VPS_IP"
echo -e "2. Generate payloads for your targets"
echo -e "3. Monitor connections and logs"
echo ""

# Final status check
echo -e "${YELLOW}Final Status Check:${NC}"
sleep 2
stitchrat-status