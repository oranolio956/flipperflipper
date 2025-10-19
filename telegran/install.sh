#!/bin/bash
# Telegran Userbot Installation Script
# Run this script to set up the userbot quickly

set -e

echo "🕵️  Telegran USERBOT Installation"
echo "====================================="
echo ""
echo "⚠️  WARNING: This is a USERBOT that uses YOUR account!"
echo "⚠️  Against Telegram ToS - Risk of account ban!"
echo "⚠️  Advanced anti-detection features included."
echo ""
read -p "Do you understand the risks? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Check if we're in the telegran directory
if [ ! -f "userbot.py" ]; then
    echo "❌ Please run this script from the telegran directory"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: You need Telegram API credentials!"
    echo "📝 Get them from: https://my.telegram.org/apps"
    echo ""
    read -p "Do you have API_ID and API_HASH? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your API_ID: " API_ID
        read -p "Enter your API_HASH: " API_HASH
        read -p "Enter your phone number (with country code, e.g. +1234567890): " PHONE
        
        sed -i "s|API_ID=.*|API_ID=$API_ID|g" .env
        sed -i "s|API_HASH=.*|API_HASH=$API_HASH|g" .env
        sed -i "s|PHONE_NUMBER=.*|PHONE_NUMBER=$PHONE|g" .env
        echo "✅ Credentials saved!"
    else
        echo ""
        echo "⚠️  Please:"
        echo "   1. Go to https://my.telegram.org/apps"
        echo "   2. Create an application"
        echo "   3. Get your API_ID and API_HASH"
        echo "   4. Edit .env file and add them"
    fi
else
    echo "✅ .env file already exists"
fi

# Create systemd service file (optional)
echo ""
read -p "Do you want to set up systemd service for 24/7 running? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CURRENT_USER=$(whoami)
    CURRENT_DIR=$(pwd)
    SERVICE_FILE="/tmp/telegran.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegran Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "📝 Created systemd service file at $SERVICE_FILE"
    echo ""
    echo "To install it, run:"
    echo "  sudo cp $SERVICE_FILE /etc/systemd/system/telegran.service"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable telegran"
    echo "  sudo systemctl start telegran"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Edit .env with API_ID, API_HASH, PHONE_NUMBER (if not done)"
echo "  2. Customize config.json with your messages"
echo "  3. Join the target Telegram group (cupidbotg)"
echo "  4. Run: source venv/bin/activate && python userbot.py"
echo "  5. Enter verification code from Telegram"
echo ""
echo "📖 MUST READ:"
echo "  - START_HERE_USERBOT.md - Quick start guide"
echo "  - USERBOT_SETUP.md - Complete setup"
echo "  - ANTI_DETECTION.md - Stealth tactics ⭐"
echo ""
echo "⚠️  Remember: Start with conservative settings!"
echo "⚠️  Read ANTI_DETECTION.md for safety tips!"
echo ""
echo "🕵️  Ready to deploy your stealth userbot!"
