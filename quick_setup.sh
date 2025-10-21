#!/bin/bash
# Stitch Web Interface - Quick Setup Script for VPS
# This script automates the setup process for easy deployment

set -e  # Exit on any error

echo "🚀 Stitch Web Interface - Quick VPS Setup"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Step 1: Update system
print_step "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install dependencies
print_step "2. Installing system dependencies..."
sudo apt install python3 python3-pip python3-venv git curl nginx ufw -y

# Step 3: Install Python dependencies
print_step "3. Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Step 4: Create logs directory
print_step "4. Creating directories..."
mkdir -p logs
mkdir -p data

# Step 5: Setup environment file
print_step "5. Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env .env.example 2>/dev/null || true
    
    # Generate random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    cat > .env << EOF
# Stitch Web Interface Environment Configuration
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=stitch2024secure
STITCH_SECRET_KEY=${SECRET_KEY}

# Server Configuration
STITCH_HOST=0.0.0.0
STITCH_PORT=5000
STITCH_DEBUG=false

# Security Settings
STITCH_BEHIND_PROXY=false
STITCH_ENABLE_HTTPS=false
STITCH_MAX_LOGIN_ATTEMPTS=5
STITCH_LOGIN_LOCKOUT_MINUTES=15

# Logging
STITCH_LOG_LEVEL=INFO
STITCH_LOG_FILE=logs/stitch.log
EOF

    print_status "Created .env file with default configuration"
else
    print_status ".env file already exists, skipping creation"
fi

# Step 6: Setup firewall
print_step "6. Configuring firewall..."
sudo ufw allow 22      # SSH
sudo ufw allow 5000    # Stitch web interface
sudo ufw --force enable

# Step 7: Test the application
print_step "7. Testing application..."
python3 -c "from web_app_real import app; print('✅ Application test successful')" || {
    print_error "Application test failed. Check dependencies."
    exit 1
}

# Step 8: Create systemd service (optional)
read -p "Do you want to create a systemd service for auto-start? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "8. Creating systemd service..."
    
    sudo tee /etc/systemd/system/stitch.service > /dev/null << EOF
[Unit]
Description=Stitch Web Interface
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 $(pwd)/start_stitch_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable stitch
    
    print_status "Systemd service created and enabled"
    
    read -p "Start the service now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start stitch
        print_status "Service started successfully"
    fi
else
    print_status "Skipping systemd service creation"
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")

# Final instructions
echo
echo "🎉 Setup Complete!"
echo "=================="
echo
print_status "Stitch Web Interface has been set up successfully!"
echo
echo "📍 Access Information:"
echo "   URL: http://${SERVER_IP}:5000"
echo "   Username: admin"
echo "   Password: stitch2024secure"
echo
print_warning "IMPORTANT SECURITY STEPS:"
echo "1. Change the default password in .env file"
echo "2. Set STITCH_ADMIN_PASSWORD to a strong password (12+ characters)"
echo "3. Consider setting up SSL/HTTPS for production use"
echo
echo "🚀 Start Commands:"
echo "   Manual start: python3 start_stitch_web.py"
echo "   Background:   nohup python3 start_stitch_web.py > logs/stitch.log 2>&1 &"
if systemctl is-enabled stitch &>/dev/null; then
echo "   Service:      sudo systemctl start stitch"
fi
echo
echo "📋 Useful Commands:"
echo "   View logs:    tail -f logs/stitch.log"
echo "   Check status: curl http://localhost:5000"
echo "   Stop service: sudo systemctl stop stitch"
echo
print_status "Setup completed successfully! 🎉"