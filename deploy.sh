#!/bin/bash

# ProxyAssessmentTool Deployment Script
# Supports local, Docker, and cloud deployment

set -e

echo "🚀 ProxyAssessmentTool Deployment"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check deployment type
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./deploy.sh [local|docker|cloud]${NC}"
    exit 1
fi

DEPLOY_TYPE=$1

# Function to check requirements
check_requirements() {
    echo "📋 Checking requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3.7+ required${NC}"
        exit 1
    fi
    
    # Check Node.js for frontend
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}⚠️  Node.js not found (optional for frontend build)${NC}"
    fi
    
    echo -e "${GREEN}✅ Requirements satisfied${NC}"
}

# Deploy locally
deploy_local() {
    echo "🏠 Deploying locally..."
    
    check_requirements
    
    # Install backend dependencies
    echo "📦 Installing backend dependencies..."
    cd backend
    pip3 install -r requirements.txt
    
    # Download GeoIP database
    echo "🌍 Downloading GeoIP database..."
    mkdir -p geoip
    if [ ! -f "geoip/GeoLite2-City.mmdb" ]; then
        curl -L "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb" \
             -o geoip/GeoLite2-City.mmdb
    fi
    
    # Start Redis (if available)
    if command -v redis-server &> /dev/null; then
        echo "🔴 Starting Redis..."
        redis-server --daemonize yes
    else
        echo -e "${YELLOW}⚠️  Redis not found - using memory cache${NC}"
    fi
    
    # Start backend
    echo "🚀 Starting backend API..."
    nohup python3 proxy_tester.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    
    # Start frontend
    echo "🌐 Starting frontend server..."
    cd ../frontend
    
    # Use Python's HTTP server
    nohup python3 -m http.server 8080 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
    
    # Save PIDs
    echo "$BACKEND_PID" > ../pids/backend.pid
    echo "$FRONTEND_PID" > ../pids/frontend.pid
    
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo ""
    echo "🌐 Frontend: http://localhost:8080"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📊 Analytics: http://localhost:8080/analytics_dashboard.html"
    echo ""
    echo "To stop: ./deploy.sh stop"
}

# Deploy with Docker
deploy_docker() {
    echo "🐳 Deploying with Docker..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker required${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose required${NC}"
        exit 1
    fi
    
    # Use production compose file
    echo "🏗️  Building containers..."
    docker-compose -f docker-compose.production.yml build
    
    echo "🚀 Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check health
    echo "🏥 Checking service health..."
    docker-compose -f docker-compose.production.yml ps
    
    echo -e "${GREEN}✅ Docker deployment complete!${NC}"
    echo ""
    echo "🌐 Frontend: http://localhost"
    echo "🔧 Backend API: http://localhost/api"
    echo "📊 Grafana: http://localhost:3000 (admin/admin)"
    echo "📈 Prometheus: http://localhost:9090"
    echo ""
    echo "To view logs: docker-compose -f docker-compose.production.yml logs -f"
    echo "To stop: docker-compose -f docker-compose.production.yml down"
}

# Deploy to cloud (using Docker on VPS)
deploy_cloud() {
    echo "☁️  Deploying to cloud..."
    
    # Check for required environment variables
    if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ]; then
        echo -e "${RED}❌ Set DEPLOY_HOST and DEPLOY_USER environment variables${NC}"
        echo "Example: export DEPLOY_HOST=your-server.com"
        echo "         export DEPLOY_USER=ubuntu"
        exit 1
    fi
    
    # Create deployment package
    echo "📦 Creating deployment package..."
    tar -czf proxy-tool-deploy.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='logs/*' \
        --exclude='*.log' \
        backend frontend docker-compose.production.yml nginx
    
    # Copy to server
    echo "📤 Uploading to server..."
    scp proxy-tool-deploy.tar.gz $DEPLOY_USER@$DEPLOY_HOST:~/
    
    # Deploy on server
    echo "🚀 Deploying on server..."
    ssh $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
        # Extract package
        tar -xzf proxy-tool-deploy.tar.gz
        
        # Install Docker if needed
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
        fi
        
        # Install Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
        
        # Deploy with Docker
        docker-compose -f docker-compose.production.yml up -d
        
        # Setup SSL with Certbot (optional)
        # sudo certbot --nginx -d $DEPLOY_HOST
EOF
    
    # Cleanup
    rm proxy-tool-deploy.tar.gz
    
    echo -e "${GREEN}✅ Cloud deployment complete!${NC}"
    echo ""
    echo "🌐 Access at: https://$DEPLOY_HOST"
    echo ""
}

# Stop deployment
stop_deployment() {
    echo "🛑 Stopping deployment..."
    
    # Stop local deployment
    if [ -f "pids/backend.pid" ]; then
        kill $(cat pids/backend.pid) 2>/dev/null || true
        rm pids/backend.pid
    fi
    
    if [ -f "pids/frontend.pid" ]; then
        kill $(cat pids/frontend.pid) 2>/dev/null || true
        rm pids/frontend.pid
    fi
    
    # Stop Docker deployment
    if [ -f "docker-compose.production.yml" ]; then
        docker-compose -f docker-compose.production.yml down 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Stopped${NC}"
}

# Create necessary directories
mkdir -p logs pids

# Execute based on command
case $DEPLOY_TYPE in
    local)
        deploy_local
        ;;
    docker)
        deploy_docker
        ;;
    cloud)
        deploy_cloud
        ;;
    stop)
        stop_deployment
        ;;
    *)
        echo -e "${RED}❌ Invalid option: $DEPLOY_TYPE${NC}"
        echo "Usage: ./deploy.sh [local|docker|cloud|stop]"
        exit 1
        ;;
esac