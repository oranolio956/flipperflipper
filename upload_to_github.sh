#!/bin/bash
# Upload Stitch RAT code to GitHub and deploy to VPS
# This script handles the complete workflow: local -> GitHub -> VPS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GITHUB_USER="oranolio956"
GITHUB_REPO="flipperflipper"
GITHUB_BRANCH="cursor/setup-and-manage-vps-with-plesk-1813"
VPS_IP="50.21.187.77"
VPS_USER="root"
VPS_PASSWORD="tCY8Oswl"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  GitHub Upload & VPS Deployment       ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Repository: https://github.com/$GITHUB_USER/$GITHUB_REPO${NC}"
echo -e "${YELLOW}Branch: $GITHUB_BRANCH${NC}"
echo -e "${YELLOW}VPS: $VPS_IP${NC}"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    git remote add origin https://github.com/$GITHUB_USER/$GITHUB_REPO.git
fi

# Check if we have the right remote
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
EXPECTED_REMOTE="https://github.com/$GITHUB_USER/$GITHUB_REPO.git"

if [ "$CURRENT_REMOTE" != "$EXPECTED_REMOTE" ]; then
    echo -e "${YELLOW}Setting correct remote repository...${NC}"
    git remote set-url origin $EXPECTED_REMOTE
fi

echo -e "${YELLOW}Step 1: Preparing code for upload...${NC}"

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# Environment variables
.env
.env.local
.env.production

# Logs
*.log
logs/
temp/
uploads/
downloads/

# SSL certificates
certs/
*.pem
*.key
*.crt

# Database
*.db
*.sqlite3

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Temporary files
*.tmp
*.temp
EOF
    echo -e "${GREEN}Created .gitignore${NC}"
fi

# Check git configuration
if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
    echo -e "${YELLOW}Setting up git configuration...${NC}"
    echo -e "${BLUE}Enter your name for git commits:${NC}"
    read -r GIT_NAME
    echo -e "${BLUE}Enter your email for git commits:${NC}"
    read -r GIT_EMAIL
    
    git config user.name "$GIT_NAME"
    git config user.email "$GIT_EMAIL"
    echo -e "${GREEN}Git configuration set${NC}"
fi

echo -e "${YELLOW}Step 2: Adding files to git...${NC}"
# Add all files except those in .gitignore
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}No changes to commit. Checking if we need to push...${NC}"
else
    echo -e "${YELLOW}Step 3: Committing changes...${NC}"
    COMMIT_MSG="Deploy Stitch RAT - $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}Commit message: $COMMIT_MSG${NC}"
    git commit -m "$COMMIT_MSG"
fi

echo -e "${YELLOW}Step 4: Pushing to GitHub...${NC}"
# Check if branch exists on remote
if git ls-remote --heads origin $GITHUB_BRANCH | grep -q $GITHUB_BRANCH; then
    echo -e "${GREEN}Branch exists on remote, pushing changes...${NC}"
    git push origin $GITHUB_BRANCH
else
    echo -e "${YELLOW}Creating new branch on remote...${NC}"
    git push -u origin $GITHUB_BRANCH
fi

echo -e "${GREEN}✅ Code successfully uploaded to GitHub!${NC}"
echo -e "${BLUE}Repository: https://github.com/$GITHUB_USER/$GITHUB_REPO/tree/$GITHUB_BRANCH${NC}"
echo ""

# Ask if user wants to deploy to VPS
echo -e "${BLUE}Do you want to deploy to your VPS now? (y/n):${NC}"
read -r DEPLOY_CHOICE

if [[ $DEPLOY_CHOICE =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Step 5: Deploying to VPS...${NC}"
    
    # Create deployment command
    DEPLOY_CMD="curl -sSL https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/github_deploy.sh | bash"
    
    echo -e "${BLUE}Connecting to VPS and running deployment...${NC}"
    echo -e "${YELLOW}VPS: $VPS_IP${NC}"
    echo -e "${YELLOW}Command: $DEPLOY_CMD${NC}"
    echo ""
    
    # Connect to VPS and run deployment
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << EOF
echo "Connected to VPS successfully!"
echo "Starting deployment from GitHub..."
$DEPLOY_CMD
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  🎉 DEPLOYMENT SUCCESSFUL! 🎉        ${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Access your application:${NC}"
        echo -e "🌐 Web Interface: ${GREEN}https://$VPS_IP${NC}"
        echo -e "👤 Login: ${GREEN}admin / StitchRAT_SecurePass_2025!${NC}"
        echo -e "🔌 RAT Server: ${GREEN}Port 4040${NC}"
        echo -e "⚙️ Plesk Panel: ${GREEN}https://$VPS_IP:8443${NC}"
        echo ""
        echo -e "${YELLOW}GitHub Repository: https://github.com/$GITHUB_USER/$GITHUB_REPO${NC}"
    else
        echo -e "${RED}❌ Deployment failed. Check the output above for errors.${NC}"
        echo -e "${YELLOW}You can manually deploy by running this on your VPS:${NC}"
        echo -e "${GREEN}$DEPLOY_CMD${NC}"
    fi
else
    echo -e "${YELLOW}Skipping VPS deployment.${NC}"
    echo -e "${BLUE}To deploy later, run this command on your VPS:${NC}"
    echo -e "${GREEN}curl -sSL https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/github_deploy.sh | bash${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary                               ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "✅ Code uploaded to GitHub"
echo -e "📂 Repository: https://github.com/$GITHUB_USER/$GITHUB_REPO"
echo -e "🌿 Branch: $GITHUB_BRANCH"
if [[ $DEPLOY_CHOICE =~ ^[Yy]$ ]]; then
    echo -e "🚀 Deployed to VPS: https://$VPS_IP"
fi
echo ""
echo -e "${GREEN}All done! 🎉${NC}"