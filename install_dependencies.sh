#!/bin/bash
# Oranolio RAT - Dependency Installation Script

echo "🚀 Installing Oranolio RAT Dependencies..."
echo "=========================================="

# Update package lists
echo "📦 Updating package lists..."
sudo apt-get update -qq

# Install Python3 and pip if not already installed
echo "🐍 Installing Python3 and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev

# Create virtual environment (optional but recommended)
echo "📁 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup database
echo "🗄️  Setting up database..."
python3 create_email_tables.py
python3 create_mfa_tables.py

echo ""
echo "✅ Installation Complete!"
echo "========================="
echo "🚀 To start the system:"
echo "   python3 start_system_fixed.py"
echo ""
echo "📱 Web Interface: http://localhost:5000"
echo "🔌 Stitch Server: localhost:4040"
echo "📧 Test Email: brooketogo98@gmail.com"
echo ""