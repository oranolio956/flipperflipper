#!/bin/bash
# Telegran Bot Installation Script
# Run this script to set up the bot quickly

set -e

echo "🤖 Telegran Bot Installation"
echo "=============================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Check if we're in the telegran directory
if [ ! -f "bot.py" ]; then
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
    echo "⚠️  IMPORTANT: Edit .env and add your BOT_TOKEN from @BotFather"
    echo ""
    read -p "Do you have your bot token ready? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your bot token: " BOT_TOKEN
        sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|g" .env
        echo "✅ Bot token saved!"
    else
        echo "⚠️  Please get your token from @BotFather and add it to .env"
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
echo "  1. Edit .env and add your BOT_TOKEN (if you haven't already)"
echo "  2. Customize config.json with your messages"
echo "  3. Add bot to your Telegram group as admin"
echo "  4. Run: source venv/bin/activate && python bot.py"
echo ""
echo "📖 See README.md and QUICK_START_GUIDE.md for more details"
echo ""
echo "🚀 Ready to launch!"
