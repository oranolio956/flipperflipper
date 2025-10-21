#!/bin/bash
# Simple GitHub Upload Script for Stitch RAT
# Uploads code to GitHub, then provides VPS deployment command

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Upload Code to GitHub                 ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the Stitch RAT directory${NC}"
    echo -e "${RED}Expected files: main.py, requirements.txt${NC}"
    exit 1
fi

# Configuration
GITHUB_USER="oranolio956"
GITHUB_REPO="flipperflipper"
GITHUB_BRANCH="cursor/setup-and-manage-vps-with-plesk-1813"

echo -e "${YELLOW}Repository: https://github.com/$GITHUB_USER/$GITHUB_REPO${NC}"
echo -e "${YELLOW}Branch: $GITHUB_BRANCH${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Installing...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y git
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${YELLOW}Please install git: brew install git${NC}"
        exit 1
    else
        echo -e "${RED}Please install git manually${NC}"
        exit 1
    fi
fi

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    git remote add origin https://github.com/$GITHUB_USER/$GITHUB_REPO.git
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

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}Creating .gitignore file...${NC}"
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

# Node modules (if any)
node_modules/

# Build artifacts
build/
dist/
EOF
    echo -e "${GREEN}Created .gitignore${NC}"
fi

echo -e "${YELLOW}Adding files to git...${NC}"
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}No new changes to commit.${NC}"
    SKIP_COMMIT=true
else
    echo -e "${YELLOW}Committing changes...${NC}"
    COMMIT_MSG="Deploy Stitch RAT - $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}Commit message: $COMMIT_MSG${NC}"
    git commit -m "$COMMIT_MSG"
    SKIP_COMMIT=false
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$GITHUB_BRANCH" ]; then
    echo -e "${YELLOW}Switching to branch: $GITHUB_BRANCH${NC}"
    git checkout -b $GITHUB_BRANCH 2>/dev/null || git checkout $GITHUB_BRANCH
fi

echo -e "${YELLOW}Pushing to GitHub...${NC}"
echo -e "${BLUE}You may be prompted for your GitHub credentials...${NC}"

# Try to push
if git push origin $GITHUB_BRANCH; then
    echo -e "${GREEN}✅ Successfully uploaded to GitHub!${NC}"
    UPLOAD_SUCCESS=true
else
    echo -e "${YELLOW}Push failed. Trying to set upstream...${NC}"
    if git push -u origin $GITHUB_BRANCH; then
        echo -e "${GREEN}✅ Successfully uploaded to GitHub!${NC}"
        UPLOAD_SUCCESS=true
    else
        echo -e "${RED}❌ Failed to push to GitHub${NC}"
        echo -e "${YELLOW}This might be due to:${NC}"
        echo -e "1. Authentication issues (need to set up GitHub token)"
        echo -e "2. Repository doesn't exist"
        echo -e "3. No push permissions"
        echo ""
        echo -e "${BLUE}To set up GitHub authentication:${NC}"
        echo -e "1. Go to: https://github.com/settings/tokens"
        echo -e "2. Generate a new token with 'repo' permissions"
        echo -e "3. Use the token as your password when prompted"
        UPLOAD_SUCCESS=false
    fi
fi

if [ "$UPLOAD_SUCCESS" = true ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  🎉 UPLOAD SUCCESSFUL! 🎉            ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Repository: ${GREEN}https://github.com/$GITHUB_USER/$GITHUB_REPO${NC}"
    echo -e "${BLUE}Branch: ${GREEN}$GITHUB_BRANCH${NC}"
    echo ""
    echo -e "${YELLOW}Now deploy to your VPS by running this command:${NC}"
    echo ""
    echo -e "${GREEN}ssh root@50.21.187.77${NC}"
    echo -e "${GREEN}curl -sSL https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/github_deploy.sh | bash${NC}"
    echo ""
    echo -e "${BLUE}Or copy and paste this one-liner on your VPS:${NC}"
    echo -e "${GREEN}curl -sSL https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/github_deploy.sh | bash${NC}"
    echo ""
    echo -e "${YELLOW}After deployment, access your application at:${NC}"
    echo -e "${GREEN}https://50.21.187.77${NC}"
else
    echo -e "${RED}Upload failed. Please check the errors above.${NC}"
fi