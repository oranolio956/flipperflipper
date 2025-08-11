#!/bin/bash

echo "🚀 Preparing Full-Stack Deployment for Netlify"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create deployment directory
DEPLOY_DIR="netlify-deploy"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

echo -e "${BLUE}📁 Setting up deployment structure...${NC}"

# Copy frontend files
cp -r frontend/* $DEPLOY_DIR/
cp netlify.toml $DEPLOY_DIR/

# Copy Netlify functions
cp -r netlify $DEPLOY_DIR/

# Install function dependencies
echo -e "${BLUE}📦 Installing function dependencies...${NC}"
cd $DEPLOY_DIR/netlify/functions
npm install --production
cd ../../..

# Create a README for deployment
cat > $DEPLOY_DIR/README.md << 'EOF'
# ProxyAssessmentTool - Full Stack Deployment

This is a complete proxy assessment tool with:
- Frontend: Modern web interface
- Backend: Netlify Functions (serverless)

## Features
- Automatic proxy discovery from multiple sources
- Real-time proxy testing
- Geolocation and fraud detection
- Mobile proxy detection
- Export functionality

## Deployment
1. Drag this folder to Netlify Drop
2. Or use Netlify CLI: `netlify deploy --prod`

## API Endpoints (via Netlify Functions)
- `/.netlify/functions/discover` - Discover proxies
- `/.netlify/functions/test` - Test individual proxy
- `/.netlify/functions/scan` - Intelligent scanning
- `/.netlify/functions/stats` - Get statistics
EOF

# Create deployment instructions
cat > deploy-instructions.txt << 'EOF'
🎉 DEPLOYMENT READY!
===================

Your full-stack Proxy Assessment Tool is ready for deployment.

Option 1: Netlify Drop (Easiest - No Account Needed)
---------------------------------------------------
1. Open https://app.netlify.com/drop in your browser
2. Drag the 'netlify-deploy' folder to the browser window
3. Wait for deployment (usually 30-60 seconds)
4. Your app will be live at a random URL!

Option 2: Netlify CLI (More Control)
------------------------------------
1. Install Netlify CLI: npm install -g netlify-cli
2. Run: cd netlify-deploy && netlify deploy --prod
3. Follow the prompts to create/link a site

Option 3: GitHub Integration
---------------------------
1. Push this code to a GitHub repository
2. Connect the repo to Netlify
3. Set build settings:
   - Build command: (leave empty)
   - Publish directory: frontend
   - Functions directory: netlify/functions

🔥 What You Get:
- Frontend hosted on Netlify's global CDN
- Backend API via serverless functions
- Automatic HTTPS
- No server management
- Scales automatically

📝 Notes:
- Free tier includes 125k function requests/month
- Functions have 10 second timeout
- No WebSocket support (using polling instead)

EOF

# Create deployment archive
echo -e "${BLUE}📦 Creating deployment archive...${NC}"
cd $DEPLOY_DIR
zip -r ../proxy-tool-netlify-deploy.zip . -x "*.DS_Store" "*/node_modules/*" > /dev/null
cd ..

echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo -e "${YELLOW}📁 Files created:${NC}"
echo "  - netlify-deploy/ (ready to drag to Netlify)"
echo "  - proxy-tool-netlify-deploy.zip (backup archive)"
echo "  - deploy-instructions.txt (detailed instructions)"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
cat deploy-instructions.txt

# Show folder size
FOLDER_SIZE=$(du -sh netlify-deploy | cut -f1)
echo ""
echo -e "${GREEN}📊 Deployment size: $FOLDER_SIZE${NC}"