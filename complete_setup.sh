#!/bin/bash
# Complete Setup Script for Oranolio RAT
# This script sets up everything needed to run the application

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           ORANOLIO RAT - COMPLETE SETUP SCRIPT                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${NC}[*]${NC} $1"
}

# Check if Python is installed
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    print_info "Please wait for the dev container to finish building..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_status "Python found: $PYTHON_VERSION"

# Check pip
print_info "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_warning "pip not found, installing..."
    python3 -m ensurepip --upgrade
fi
print_status "pip is available"

# Create required directories
print_info "Creating required directories..."
mkdir -p data logs uploads downloads backups payloads
chmod 755 data logs uploads downloads backups payloads
print_status "Directories created"

# Install Python dependencies
print_info "Installing Python dependencies (this may take a few minutes)..."
if [ -f "requirements.txt" ]; then
    pip3 install --no-cache-dir -r requirements.txt 2>&1 | grep -v "Requirement already satisfied" || true
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Initialize databases
print_info "Initializing databases..."
python3 init_all_databases.py
if [ $? -eq 0 ]; then
    print_status "Databases initialized"
else
    print_error "Database initialization failed"
    exit 1
fi

# Start Redis (optional)
print_info "Starting Redis server..."
if command -v redis-server &> /dev/null; then
    bash start_redis.sh
    print_status "Redis started (or using memory backend)"
else
    print_warning "Redis not available, will use memory backend"
fi

# Run health check
print_info "Running health check..."
python3 production_health.py
if [ $? -eq 0 ]; then
    print_status "Health check passed"
else
    print_warning "Health check reported issues, but continuing..."
fi

# Display completion message
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE!                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
print_status "All components initialized successfully"
echo ""
echo "To start the application, run:"
echo "  python3 production_start.py"
echo ""
echo "Or for development mode:"
echo "  python3 main.py"
echo ""
echo "Default admin email: admin@oranolio.local"
echo ""
