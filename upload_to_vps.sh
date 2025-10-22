#!/bin/bash
# Upload Stitch RAT code to VPS
# Run this script from your local machine where the code is located

set -e

# Configuration
VPS_IP="50.21.187.77"
VPS_USER="root"
VPS_PASSWORD="tCY8Oswl"
APP_DIR="/opt/stitchrat"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Uploading Stitch RAT to VPS          ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the Stitch RAT directory${NC}"
    echo -e "${RED}Expected files: main.py, requirements.txt${NC}"
    exit 1
fi

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo -e "${YELLOW}rsync not found, installing...${NC}"
    # Try to install rsync based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y rsync
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install rsync
    else
        echo -e "${RED}Please install rsync manually${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}Step 1: Creating archive of source code...${NC}"
# Create a temporary archive excluding unnecessary files
tar -czf /tmp/stitchrat-code.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='.DS_Store' \
    --exclude='Thumbs.db' \
    --exclude='*.log' \
    --exclude='logs/*' \
    --exclude='temp/*' \
    --exclude='uploads/*' \
    --exclude='downloads/*' \
    .

echo -e "${YELLOW}Step 2: Uploading code to VPS...${NC}"
# Upload the archive
scp -o StrictHostKeyChecking=no /tmp/stitchrat-code.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo -e "${YELLOW}Step 3: Extracting code on VPS...${NC}"
# Extract and set up on VPS
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'EOF'
# Create application directory if it doesn't exist
mkdir -p /opt/stitchrat

# Extract the code
cd /opt/stitchrat
tar -xzf /tmp/stitchrat-code.tar.gz

# Clean up
rm /tmp/stitchrat-code.tar.gz

# Set proper permissions
chown -R root:root /opt/stitchrat
chmod -R 755 /opt/stitchrat

echo "Code extraction complete!"
ls -la /opt/stitchrat/
EOF

# Clean up local temp file
rm /tmp/stitchrat-code.tar.gz

echo -e "${YELLOW}Step 4: Uploading deployment script...${NC}"
# Upload the deployment script
scp -o StrictHostKeyChecking=no deploy_to_vps.sh $VPS_USER@$VPS_IP:/opt/stitchrat/
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "chmod +x /opt/stitchrat/deploy_to_vps.sh"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Upload Complete!                      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. SSH into your VPS:"
echo -e "   ${GREEN}ssh root@$VPS_IP${NC}"
echo -e "   Password: ${GREEN}$VPS_PASSWORD${NC}"
echo ""
echo -e "2. Run the deployment script:"
echo -e "   ${GREEN}cd /opt/stitchrat${NC}"
echo -e "   ${GREEN}./deploy_to_vps.sh${NC}"
echo ""
echo -e "3. Access your application:"
echo -e "   ${GREEN}https://$VPS_IP${NC}"
echo ""
echo -e "${YELLOW}Files uploaded to: /opt/stitchrat${NC}"
echo -e "${YELLOW}Deployment script: /opt/stitchrat/deploy_to_vps.sh${NC}"