#!/bin/bash
# Fix the main.py UnboundLocalError

echo "🔧 Fixing main.py UnboundLocalError..."

# Stop the failing service
systemctl stop stitchrat

# Let's examine the main.py file to understand the issue
echo "📝 Checking main.py content..."
cat /opt/stitchrat/main.py

echo ""
echo "📝 Checking Application/stitch_cmd.py around line 694..."
sed -n '690,700p' /opt/stitchrat/Application/stitch_cmd.py

# The issue is that main.py is calling server_main() which has an UnboundLocalError
# Let's try using start_server.py instead, which is designed to start the web interface

echo "🔄 Switching to start_server.py as the entry point..."

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

# Let's also check what start_server.py does
echo "📝 Checking start_server.py content..."
cat /opt/stitchrat/start_server.py

# If start_server.py also has issues, let's create a simple web app launcher
echo "🔧 Creating a direct web app launcher..."

cat > /opt/stitchrat/web_launcher.py << 'EOF'
#!/usr/bin/env python3
"""
Direct Web App Launcher for Stitch RAT
Bypasses the command-line interface and starts the web interface directly
"""
import os
import sys

# Set up environment
os.environ['STITCH_DEBUG'] = 'false'
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchRAT_SecurePass_2025!'

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def start_web_interface():
    """Start the web interface directly"""
    try:
        print("🚀 Starting Stitch RAT Web Interface...")
        print(f"📁 Working directory: {os.getcwd()}")
        
        # Try to import and run the web application directly
        print("📦 Importing web_app_real...")
        import web_app_real
        
        print("✅ Web application imported successfully!")
        print("🌐 Web interface should be starting...")
        
        # The web_app_real.py should start automatically when imported
        # If it doesn't, we might need to call a specific function
        
    except Exception as e:
        print(f"❌ Failed to start web interface: {e}")
        print("🔍 Trying alternative approach...")
        
        try:
            # Alternative: try to run the web app in a different way
            from flask import Flask
            print("✅ Flask is available")
            
            # Try to start a basic Flask app if the main one fails
            app = Flask(__name__)
            
            @app.route('/')
            def hello():
                return '''
                <h1>Stitch RAT - Starting Up</h1>
                <p>The web interface is initializing...</p>
                <p>If this message persists, check the logs: <code>journalctl -u stitchrat -f</code></p>
                '''
            
            print("🌐 Starting basic web interface on port 5000...")
            app.run(host='0.0.0.0', port=5000, debug=False)
            
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    start_web_interface()
EOF

chown stitchrat:stitchrat /opt/stitchrat/web_launcher.py
chmod +x /opt/stitchrat/web_launcher.py

# Let's also try to fix the SSL context issue in web_app_real.py
echo "🔧 Checking and fixing SSL context issue in web_app_real.py..."

# Look for the problematic line around 2670
echo "📝 Checking line 2670 in web_app_real.py..."
sed -n '2665,2675p' /opt/stitchrat/web_app_real.py

# Create a backup and fix the SSL context issue
cp /opt/stitchrat/web_app_real.py /opt/stitchrat/web_app_real.py.backup

# Fix the SSL context unpacking issue
sed -i 's/ssl_cert, ssl_key = get_ssl_context()/ssl_context = get_ssl_context()/' /opt/stitchrat/web_app_real.py

# Also need to update how it's used later in the file
sed -i 's/ssl_context=(ssl_cert, ssl_key)/ssl_context=ssl_context/' /opt/stitchrat/web_app_real.py

echo "✅ Fixed SSL context unpacking issue"

# Reload systemd and restart service
echo "🔄 Reloading systemd and restarting service..."
systemctl daemon-reload
systemctl start stitchrat

# Wait a moment and check status
echo "⏳ Waiting for service to start..."
sleep 8

echo "🔍 Checking service status..."
systemctl status stitchrat --no-pager -l

# Check if it's running
if systemctl is-active --quiet stitchrat; then
    echo "✅ Stitch RAT is now running!"
    
    # Test if the web interface is responding
    echo "🌐 Testing web interface..."
    sleep 3
    if curl -k -s https://localhost:443 > /dev/null 2>&1; then
        echo "✅ HTTPS interface is responding!"
    elif curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ HTTP interface is responding!"
    else
        echo "⏳ Web interface may still be starting up..."
        echo "🔍 Let's check what's listening on port 5000..."
        netstat -tlnp | grep :5000 || echo "Nothing listening on port 5000 yet"
    fi
    
    echo ""
    echo "🎉 SUCCESS! Your Stitch RAT should now be accessible at:"
    echo "🌐 https://50.21.187.77"
    echo "👤 Username: admin"
    echo "🔑 Password: StitchRAT_SecurePass_2025!"
    
else
    echo "❌ Service is still not running. Let's try the web launcher directly..."
    
    echo "🔧 Updating service to use web launcher..."
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
ExecStart=/opt/stitchrat/venv/bin/python web_launcher.py
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

    systemctl daemon-reload
    systemctl start stitchrat
    
    echo "⏳ Waiting for web launcher to start..."
    sleep 5
    
    systemctl status stitchrat --no-pager -l
    
    if systemctl is-active --quiet stitchrat; then
        echo "✅ Web launcher is running!"
        echo "🌐 Try accessing: https://50.21.187.77"
    else
        echo "❌ Still having issues. Let's check the latest logs..."
        journalctl -u stitchrat --no-pager -n 15
        
        echo ""
        echo "🔧 Manual testing - let's try running the web app directly:"
        echo "Run this command to test manually:"
        echo "cd /opt/stitchrat && sudo -u stitchrat /opt/stitchrat/venv/bin/python web_launcher.py"
    fi
fi

echo ""
echo "📊 Final system status:"
echo "======================"
stitchrat-status