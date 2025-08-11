#!/bin/bash

# ProxyAssessmentTool - Deploy to Vercel + Render
# Free tier deployment script

set -e

echo "🚀 ProxyAssessmentTool Cloud Deployment"
echo "======================================"
echo "Frontend → Vercel (Free)"
echo "Backend → Render (Free)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check for required tools
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v git &> /dev/null; then
        echo "❌ Git is required"
        echo "Install: https://git-scm.com/downloads"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo "❌ Node.js/npm is required for Vercel CLI"
        echo "Install: https://nodejs.org/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Requirements satisfied${NC}"
}

# Install CLIs
install_clis() {
    echo "📦 Installing deployment CLIs..."
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        echo "Installing Vercel CLI..."
        npm install -g vercel
    fi
    
    echo -e "${GREEN}✅ CLIs ready${NC}"
}

# Deploy Frontend to Vercel
deploy_frontend() {
    echo -e "\n${BLUE}🌐 Deploying Frontend to Vercel...${NC}"
    
    cd frontend
    
    # Initialize Vercel project
    echo "Initializing Vercel project..."
    vercel --yes
    
    # Deploy to production
    echo "Deploying to production..."
    FRONTEND_URL=$(vercel --prod --yes)
    
    echo -e "${GREEN}✅ Frontend deployed to: $FRONTEND_URL${NC}"
    
    # Save URL
    echo "$FRONTEND_URL" > ../frontend-url.txt
    
    cd ..
}

# Prepare backend for Render
prepare_backend() {
    echo -e "\n${BLUE}🔧 Preparing Backend for Render...${NC}"
    
    # Update frontend URL in render.yaml
    if [ -f "frontend-url.txt" ]; then
        FRONTEND_URL=$(cat frontend-url.txt)
        # Update CORS origins in render.yaml
        sed -i.bak "s|https://proxy-assessment-tool.vercel.app|$FRONTEND_URL|g" render.yaml
    fi
    
    # Create .gitignore if needed
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << EOF
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv
logs/
*.log
.DS_Store
node_modules/
dist/
build/
*.egg-info/
.coverage
.pytest_cache/
EOF
    fi
    
    echo -e "${GREEN}✅ Backend prepared${NC}"
}

# Deploy to Render
deploy_backend() {
    echo -e "\n${BLUE}🚀 Deploying Backend to Render...${NC}"
    
    echo -e "${YELLOW}Steps to deploy on Render:${NC}"
    echo ""
    echo "1. Go to: https://dashboard.render.com/new"
    echo "2. Connect your GitHub account"
    echo "3. Select 'New Web Service'"
    echo "4. Connect this repository"
    echo "5. Use these settings:"
    echo "   - Name: proxy-assessment-backend"
    echo "   - Region: Oregon (US West)"
    echo "   - Branch: main"
    echo "   - Root Directory: ."
    echo "   - Runtime: Python 3"
    echo "   - Build Command: cd backend && pip install -r requirements.txt"
    echo "   - Start Command: cd backend && python proxy_tester.py"
    echo ""
    echo "6. Add Environment Variables:"
    echo "   - PYTHON_VERSION = 3.11.0"
    echo "   - PORT = 8000"
    
    if [ -f "frontend-url.txt" ]; then
        FRONTEND_URL=$(cat frontend-url.txt)
        echo "   - CORS_ORIGINS = $FRONTEND_URL"
    fi
    
    echo ""
    echo "7. Click 'Create Web Service'"
    echo ""
    echo -e "${YELLOW}Alternatively, use render.yaml:${NC}"
    echo "1. Push this code to GitHub"
    echo "2. Go to: https://dashboard.render.com/select-repo?type=blueprint"
    echo "3. Connect your repository"
    echo "4. Render will auto-detect render.yaml"
    echo ""
    
    # Get backend URL
    read -p "Enter your Render backend URL (e.g., https://proxy-assessment-backend.onrender.com): " BACKEND_URL
    
    # Update frontend with backend URL
    update_frontend_backend_url "$BACKEND_URL"
}

# Update frontend with actual backend URL
update_frontend_backend_url() {
    local BACKEND_URL=$1
    
    echo -e "\n${BLUE}🔄 Updating frontend with backend URL...${NC}"
    
    cd frontend
    
    # Update index.html
    sed -i.bak "s|https://proxy-assessment-backend.onrender.com|$BACKEND_URL|g" index.html
    
    # Update analytics dashboard
    sed -i.bak "s|http://localhost:8000|$BACKEND_URL|g" analytics_dashboard.html
    
    # Set environment variable in Vercel
    echo "Setting backend URL in Vercel..."
    vercel env add BACKEND_URL production < <(echo "$BACKEND_URL")
    
    # Redeploy frontend
    echo "Redeploying frontend with updated backend URL..."
    vercel --prod --yes
    
    cd ..
    
    echo -e "${GREEN}✅ Frontend updated with backend URL${NC}"
}

# Create GitHub repository
create_github_repo() {
    echo -e "\n${BLUE}📁 Preparing GitHub repository...${NC}"
    
    if [ ! -d ".git" ]; then
        git init
        git add .
        git commit -m "Initial commit - ProxyAssessmentTool"
    fi
    
    echo -e "${YELLOW}Steps to create GitHub repository:${NC}"
    echo "1. Go to: https://github.com/new"
    echo "2. Create a new repository (public or private)"
    echo "3. Don't initialize with README"
    echo "4. Run these commands:"
    echo ""
    echo "   git remote add origin https://github.com/YOUR_USERNAME/proxy-assessment-tool.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    
    read -p "Press Enter after pushing to GitHub..."
}

# Main deployment flow
main() {
    check_requirements
    install_clis
    
    echo -e "\n${YELLOW}📌 Deployment Steps:${NC}"
    echo "1. Deploy frontend to Vercel"
    echo "2. Create GitHub repository"
    echo "3. Deploy backend to Render"
    echo "4. Update frontend with backend URL"
    echo ""
    
    read -p "Ready to start? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Step 1: Deploy frontend
    deploy_frontend
    
    # Step 2: Create GitHub repo
    create_github_repo
    
    # Step 3: Prepare and deploy backend
    prepare_backend
    deploy_backend
    
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
    echo ""
    echo "📝 Summary:"
    
    if [ -f "frontend-url.txt" ]; then
        echo "Frontend URL: $(cat frontend-url.txt)"
    fi
    
    echo ""
    echo "⚡ Quick Test:"
    echo "1. Open your frontend URL"
    echo "2. Click 'Auto-Discover Proxies'"
    echo "3. Watch real-time proxy discovery!"
    echo ""
    echo -e "${YELLOW}Note: Render free tier spins down after 15 minutes of inactivity.${NC}"
    echo "First request may take 30-60 seconds to wake up."
}

# Run main
main