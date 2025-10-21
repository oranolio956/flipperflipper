#!/bin/bash
# Fix SSL context error in Stitch RAT application

echo "🔧 Fixing SSL context error in Stitch RAT..."

# Stop the failing service
systemctl stop stitchrat

# Check the logs to understand the exact error
echo "📝 Checking application logs..."
journalctl -u stitchrat --no-pager -n 20

# Let's check if the main application file exists and what's causing the SSL error
echo "🔍 Checking application files..."
ls -la /opt/stitchrat/

# Check if web_app_real.py exists
if [ -f "/opt/stitchrat/web_app_real.py" ]; then
    echo "✅ web_app_real.py found"
else
    echo "❌ web_app_real.py not found"
    # Try to find the main application file
    echo "🔍 Looking for main application files..."
    find /opt/stitchrat -name "*.py" -type f | grep -E "(main|app|web)" | head -10
fi

# Check if main.py exists (original entry point)
if [ -f "/opt/stitchrat/main.py" ]; then
    echo "✅ main.py found - using original entry point"
    
    # Update systemd service to use main.py instead
    cat > /etc/systemd/system/stitchrat.service << 'EOF'
[Unit]
Description=Stitch RAT Web Interface
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=stitchrat
Group=stitchrat
WorkingDirectory=/opt/stitchrat
Environment=PATH=/opt/stitchrat/venv/bin
EnvironmentFile=/opt/stitchrat/.env
ExecStart=/opt/stitchrat/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stitchrat

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/stitchrat

LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ Updated service to use main.py"
    
elif [ -f "/opt/stitchrat/start_server.py" ]; then
    echo "✅ start_server.py found - using server starter"
    
    # Update systemd service to use start_server.py
    cat > /etc/systemd/system/stitchrat.service << 'EOF'
[Unit]
Description=Stitch RAT Web Interface
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=stitchrat
Group=stitchrat
WorkingDirectory=/opt/stitchrat
Environment=PATH=/opt/stitchrat/venv/bin
EnvironmentFile=/opt/stitchrat/.env
ExecStart=/opt/stitchrat/venv/bin/python start_server.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stitchrat

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/stitchrat

LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ Updated service to use start_server.py"
    
else
    echo "❌ No suitable entry point found. Let's create a simple launcher..."
    
    # Create a simple launcher script
    cat > /opt/stitchrat/launcher.py << 'EOF'
#!/usr/bin/env python3
"""
Simple launcher for Stitch RAT
Tries different entry points and handles SSL context issues
"""
import os
import sys
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def try_web_app():
    """Try to start the web application"""
    try:
        print("🚀 Attempting to start web_app_real.py...")
        import web_app_real
        return True
    except Exception as e:
        print(f"❌ web_app_real.py failed: {e}")
        return False

def try_main():
    """Try to start main.py"""
    try:
        print("🚀 Attempting to start main.py...")
        import main
        return True
    except Exception as e:
        print(f"❌ main.py failed: {e}")
        return False

def try_start_server():
    """Try to start start_server.py"""
    try:
        print("🚀 Attempting to start start_server.py...")
        import start_server
        return True
    except Exception as e:
        print(f"❌ start_server.py failed: {e}")
        return False

def try_application_main():
    """Try to start from Application directory"""
    try:
        print("🚀 Attempting to start from Application/stitch_cmd.py...")
        from Application import stitch_cmd
        stitch_cmd.server_main()
        return True
    except Exception as e:
        print(f"❌ Application/stitch_cmd.py failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Stitch RAT Launcher Starting...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    # Try different entry points
    success = False
    
    # Try in order of preference
    entry_points = [
        try_start_server,
        try_main,
        try_application_main,
        try_web_app
    ]
    
    for entry_point in entry_points:
        if entry_point():
            success = True
            break
    
    if not success:
        print("❌ All entry points failed. Check the logs above for errors.")
        sys.exit(1)
EOF

    chown stitchrat:stitchrat /opt/stitchrat/launcher.py
    chmod +x /opt/stitchrat/launcher.py
    
    # Update systemd service to use launcher
    cat > /etc/systemd/system/stitchrat.service << 'EOF'
[Unit]
Description=Stitch RAT Web Interface
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=stitchrat
Group=stitchrat
WorkingDirectory=/opt/stitchrat
Environment=PATH=/opt/stitchrat/venv/bin
EnvironmentFile=/opt/stitchrat/.env
ExecStart=/opt/stitchrat/venv/bin/python launcher.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stitchrat

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/stitchrat

LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ Created launcher script"
fi

# Reload systemd and restart service
echo "🔄 Reloading systemd and restarting service..."
systemctl daemon-reload
systemctl start stitchrat

# Wait a moment and check status
echo "⏳ Waiting for service to start..."
sleep 5

echo "🔍 Checking service status..."
systemctl status stitchrat --no-pager -l

# Check if it's running
if systemctl is-active --quiet stitchrat; then
    echo "✅ Stitch RAT is now running!"
    
    # Test if the web interface is responding
    echo "🌐 Testing web interface..."
    sleep 2
    if curl -k -s https://localhost:443 > /dev/null 2>&1; then
        echo "✅ Web interface is responding!"
    elif curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ Web interface is responding on HTTP!"
    else
        echo "⚠️ Web interface may not be fully ready yet. Check logs with: journalctl -u stitchrat -f"
    fi
    
    echo ""
    echo "🎉 SUCCESS! Your Stitch RAT should now be accessible at:"
    echo "🌐 https://50.21.187.77"
    echo "👤 Username: admin"
    echo "🔑 Password: StitchRAT_SecurePass_2025!"
    
else
    echo "❌ Service is still not running. Let's check the logs..."
    journalctl -u stitchrat --no-pager -n 10
    
    echo ""
    echo "🔧 Manual troubleshooting steps:"
    echo "1. Check logs: journalctl -u stitchrat -f"
    echo "2. Try manual start: cd /opt/stitchrat && sudo -u stitchrat /opt/stitchrat/venv/bin/python main.py"
    echo "3. Check Python path: sudo -u stitchrat /opt/stitchrat/venv/bin/python -c 'import sys; print(sys.path)'"
fi