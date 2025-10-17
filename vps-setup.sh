#!/bin/bash
# Enhanced Stitch VPS Setup Script
# Run this script on a fresh Ubuntu VPS to prepare it for Stitch deployment

set -e

echo "🚀 Enhanced Stitch VPS Setup Script"
echo "=================================="
echo ""

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   print_status "Please run as a regular user with sudo privileges"
   exit 1
fi

# Get user input for configuration
echo "📋 Configuration Setup"
echo "====================="
read -p "Enter new SSH port (default 2222): " SSH_PORT
SSH_PORT=${SSH_PORT:-2222}

read -p "Enter Stitch bind port (default 4433): " BIND_PORT
BIND_PORT=${BIND_PORT:-4433}

read -p "Enter Stitch listen port (default 4455): " LISTEN_PORT
LISTEN_PORT=${LISTEN_PORT:-4455}

read -p "Create dedicated stitch user? (y/n): " CREATE_USER
CREATE_USER=${CREATE_USER:-y}

echo ""
print_status "Starting VPS setup with the following configuration:"
print_status "SSH Port: $SSH_PORT"
print_status "Stitch Bind Port: $BIND_PORT"
print_status "Stitch Listen Port: $LISTEN_PORT"
print_status "Create User: $CREATE_USER"
echo ""

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    git \
    screen \
    tmux \
    xvfb \
    x11-utils \
    fail2ban \
    ufw \
    htop \
    curl \
    wget \
    unzip

# Install Python packages
print_status "Installing Python packages..."
pip3 install pycrypto requests colorama

# Configure firewall
print_status "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow $SSH_PORT/tcp
sudo ufw allow $BIND_PORT/tcp
sudo ufw allow $LISTEN_PORT/tcp
sudo ufw --force enable

# Configure SSH security
print_status "Configuring SSH security..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Update SSH configuration
sudo sed -i "s/#Port 22/Port $SSH_PORT/" /etc/ssh/sshd_config
sudo sed -i "s/#PermitRootLogin yes/PermitRootLogin no/" /etc/ssh/sshd_config
sudo sed -i "s/#PasswordAuthentication yes/PasswordAuthentication yes/" /etc/ssh/sshd_config

# Configure fail2ban
print_status "Configuring fail2ban..."
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = $SSH_PORT
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Create stitch user if requested
if [[ $CREATE_USER == "y" ]]; then
    print_status "Creating stitch user..."
    sudo useradd -m -s /bin/bash stitch-user
    sudo usermod -aG sudo stitch-user
    
    # Create stitch directory
    sudo mkdir -p /opt/stitch
    sudo chown stitch-user:stitch-user /opt/stitch
    
    print_status "Stitch user created. You'll need to set a password:"
    sudo passwd stitch-user
fi

# Set up virtual display
print_status "Configuring virtual display..."
echo 'export DISPLAY=:99' >> ~/.bashrc
echo 'if ! pgrep -x "Xvfb" > /dev/null; then Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & fi' >> ~/.bashrc

# Create startup script
print_status "Creating Stitch startup script..."
sudo tee /opt/stitch/start-stitch.sh > /dev/null <<EOF
#!/bin/bash
cd /opt/stitch
export DISPLAY=:99

# Start virtual display if not running
if ! pgrep -x "Xvfb" > /dev/null; then
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
fi

# Start Stitch
python3 main.py
EOF

sudo chmod +x /opt/stitch/start-stitch.sh

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/stitch.service > /dev/null <<EOF
[Unit]
Description=Stitch C2 Server
After=network.target

[Service]
Type=simple
User=stitch-user
WorkingDirectory=/opt/stitch
Environment=DISPLAY=:99
ExecStartPre=/bin/bash -c 'if ! pgrep -x "Xvfb" > /dev/null; then /usr/bin/Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & fi'
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

# Create log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/stitch > /dev/null <<EOF
/opt/stitch/Logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 stitch-user stitch-user
}
EOF

# Create monitoring script
print_status "Creating monitoring script..."
sudo tee /opt/stitch/monitor-connections.sh > /dev/null <<EOF
#!/bin/bash
LOG_FILE="/opt/stitch/connection.log"
while true; do
    echo "\$(date): Active connections:" >> \$LOG_FILE
    netstat -an | grep :$BIND_PORT >> \$LOG_FILE
    netstat -an | grep :$LISTEN_PORT >> \$LOG_FILE
    echo "---" >> \$LOG_FILE
    sleep 300  # Log every 5 minutes
done
EOF

sudo chmod +x /opt/stitch/monitor-connections.sh

# Test virtual display
print_status "Testing virtual display..."
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
sleep 2

if python3 -c "import tkinter; print('✅ GUI test passed')" 2>/dev/null; then
    print_status "Virtual display working correctly"
else
    print_warning "Virtual display test failed - GUI components may not work"
fi

# Restart SSH service
print_status "Restarting SSH service..."
sudo systemctl restart ssh

# Final status check
print_status "Checking service status..."
sudo systemctl status ufw --no-pager
sudo systemctl status fail2ban --no-pager

echo ""
echo "🎉 VPS Setup Complete!"
echo "======================"
echo ""
print_status "Next steps:"
echo "1. Copy your enhanced Stitch files to /opt/stitch/"
echo "2. Test Stitch functionality: cd /opt/stitch && python3 main.py"
echo "3. Configure payload generation with your VPS IP"
echo "4. Enable systemd service: sudo systemctl enable stitch"
echo ""
print_warning "IMPORTANT SECURITY NOTES:"
echo "• SSH port changed to: $SSH_PORT"
echo "• Firewall enabled with ports: $SSH_PORT, $BIND_PORT, $LISTEN_PORT"
echo "• fail2ban active for SSH protection"
echo "• Update your SSH client to use port $SSH_PORT"
echo ""
print_warning "REMEMBER:"
echo "• Only use for authorized penetration testing"
echo "• Set strong passwords for all accounts"
echo "• Consider using SSH keys instead of passwords"
echo "• Monitor logs regularly for security"
echo ""
print_status "Setup log saved to: /var/log/stitch-setup.log"

# Save setup info
sudo tee /var/log/stitch-setup.log > /dev/null <<EOF
Stitch VPS Setup Completed: $(date)
SSH Port: $SSH_PORT
Bind Port: $BIND_PORT
Listen Port: $LISTEN_PORT
User Created: $CREATE_USER
EOF

echo "Setup complete! 🚀"