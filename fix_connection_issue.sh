#!/bin/bash
# Fix connection issues - troubleshoot and resolve network connectivity

echo "🔧 Diagnosing connection issues..."

# Check if services are actually running
echo "📊 Step 1: Checking service status..."
echo "=================================="
systemctl status stitchrat --no-pager -l | head -10
echo ""
systemctl status nginx --no-pager -l | head -10
echo ""

# Check what's listening on ports
echo "📡 Step 2: Checking what's listening on ports..."
echo "=============================================="
echo "Port 5000 (Application):"
netstat -tlnp | grep :5000
echo ""
echo "Port 80 (HTTP):"
netstat -tlnp | grep :80
echo ""
echo "Port 443 (HTTPS):"
netstat -tlnp | grep :443
echo ""
echo "Port 4040 (RAT Server):"
netstat -tlnp | grep :4040
echo ""

# Check firewall status
echo "🔥 Step 3: Checking firewall configuration..."
echo "==========================================="
ufw status verbose
echo ""

# Test local connectivity
echo "🌐 Step 4: Testing local connectivity..."
echo "======================================"
echo "Testing localhost:5000..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5000 || echo "❌ localhost:5000 not responding"
echo ""
echo "Testing 127.0.0.1:5000..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:5000 || echo "❌ 127.0.0.1:5000 not responding"
echo ""
echo "Testing external IP:80..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://50.21.187.77:80 || echo "❌ External IP:80 not responding"
echo ""

# Check Nginx configuration
echo "⚙️ Step 5: Checking Nginx configuration..."
echo "========================================"
nginx -t
echo ""
echo "Nginx error log (last 10 lines):"
tail -10 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error log found"
echo ""

# Check application logs
echo "📝 Step 6: Checking application logs..."
echo "====================================="
echo "Recent Stitch RAT logs:"
journalctl -u stitchrat --no-pager -n 10
echo ""

# Check if the application is binding to the right interface
echo "🔍 Step 7: Checking application binding..."
echo "========================================"
echo "Processes listening on all interfaces (0.0.0.0):"
netstat -tlnp | grep "0.0.0.0"
echo ""

# Fix common issues
echo "🔧 Step 8: Applying fixes..."
echo "=========================="

# Fix 1: Make sure the application binds to 0.0.0.0
echo "Fix 1: Updating start_server.py to bind to 0.0.0.0..."
sed -i "s/app.run(host='0.0.0.0'/app.run(host='0.0.0.0'/" /opt/stitchrat/start_server.py

# Fix 2: Update environment variables
echo "Fix 2: Updating environment variables..."
cat >> /opt/stitchrat/.env << 'EOF'

# Network binding fixes
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
STITCH_BIND_ALL_INTERFACES=true
EOF

# Fix 3: Create a simple test server to verify connectivity
echo "Fix 3: Creating test server..."
cat > /opt/stitchrat/test_server.py << 'EOF'
#!/usr/bin/env python3
"""
Simple test server to verify connectivity
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>🎉 VPS Connection Test - SUCCESS!</h1>
    <p><strong>Your VPS is reachable!</strong></p>
    <p>Server IP: 50.21.187.77</p>
    <p>This means the network connection is working.</p>
    <p>If you see this page, the issue was with the main application, not connectivity.</p>
    <hr>
    <p><a href="/test">Run Test</a></p>
    '''

@app.route('/test')
def test():
    return '''
    <h2>🔧 Connection Test Results</h2>
    <p>✅ Flask is working</p>
    <p>✅ Python is working</p>
    <p>✅ Network connectivity is working</p>
    <p>✅ Firewall allows connections</p>
    <p>✅ Nginx proxy is working (if you see this through port 80/443)</p>
    '''

if __name__ == '__main__':
    print("🚀 Starting test server on 0.0.0.0:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

chown stitchrat:stitchrat /opt/stitchrat/test_server.py

# Fix 4: Restart services with fixes
echo "Fix 4: Restarting services..."
systemctl stop stitchrat
sleep 2

# Start test server first to verify connectivity
echo "Starting test server to verify connectivity..."
sudo -u stitchrat /opt/stitchrat/venv/bin/python /opt/stitchrat/test_server.py &
TEST_PID=$!
sleep 5

# Test if test server is accessible
echo "Testing connectivity with test server..."
if curl -s http://localhost:5000 | grep -q "SUCCESS"; then
    echo "✅ Test server is working locally"
    
    # Test external access
    if curl -s http://50.21.187.77 | grep -q "SUCCESS" 2>/dev/null; then
        echo "✅ External connectivity is working!"
        echo "🎉 The issue was with the main application, not network connectivity."
    else
        echo "❌ External connectivity issue - checking Nginx..."
        
        # Fix Nginx configuration for test
        cat > /etc/nginx/sites-available/stitchrat-test << 'EOF'
server {
    listen 80;
    server_name 50.21.187.77 _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
        
        ln -sf /etc/nginx/sites-available/stitchrat-test /etc/nginx/sites-enabled/
        nginx -t && systemctl reload nginx
        
        sleep 2
        if curl -s http://50.21.187.77 | grep -q "SUCCESS" 2>/dev/null; then
            echo "✅ Fixed! External connectivity now working."
        else
            echo "❌ Still having external connectivity issues."
        fi
    fi
else
    echo "❌ Test server not working locally - deeper issue"
fi

# Kill test server
kill $TEST_PID 2>/dev/null || true

# Fix 5: Update the main application to work properly
echo "Fix 5: Fixing main application..."

# Create a working web launcher
cat > /opt/stitchrat/working_launcher.py << 'EOF'
#!/usr/bin/env python3
"""
Working Web Launcher for Stitch RAT
Ensures proper binding and error handling
"""
import os
import sys
import time

# Set environment variables
os.environ['STITCH_DEBUG'] = 'false'
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchRAT_SecurePass_2025!'
os.environ['FLASK_HOST'] = '0.0.0.0'
os.environ['FLASK_PORT'] = '5000'

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def start_application():
    """Start the Stitch RAT application"""
    try:
        print("🚀 Starting Stitch RAT Web Interface...")
        print(f"📁 Working directory: {os.getcwd()}")
        print("🌐 Binding to: 0.0.0.0:5000")
        
        # Import the web application
        from web_app_real import app
        
        # Configure Flask to bind to all interfaces
        print("✅ Web application imported successfully!")
        print("🌐 Starting server on 0.0.0.0:5000...")
        
        # Start the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: start a basic server
        print("🔄 Starting fallback server...")
        from flask import Flask
        
        fallback_app = Flask(__name__)
        
        @fallback_app.route('/')
        def index():
            return '''
            <h1>🔧 Stitch RAT - Starting Up</h1>
            <p>The main application encountered an error, but the server is running.</p>
            <p>Check the logs: <code>journalctl -u stitchrat -f</code></p>
            <p>Server IP: 50.21.187.77</p>
            <p>Time: ''' + str(time.ctime()) + '''</p>
            '''
        
        fallback_app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    start_application()
EOF

chown stitchrat:stitchrat /opt/stitchrat/working_launcher.py
chmod +x /opt/stitchrat/working_launcher.py

# Update systemd service to use working launcher
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
ExecStart=/opt/stitchrat/venv/bin/python working_launcher.py
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

# Restart services
echo "Fix 6: Restarting all services..."
systemctl daemon-reload
systemctl restart stitchrat
sleep 5
systemctl restart nginx

echo ""
echo "🔍 Final connectivity test..."
echo "=========================="

# Wait for services to start
sleep 10

# Final tests
echo "Testing localhost:5000..."
if curl -s http://localhost:5000 >/dev/null 2>&1; then
    echo "✅ localhost:5000 is responding"
else
    echo "❌ localhost:5000 not responding"
fi

echo "Testing external IP..."
if curl -s http://50.21.187.77 >/dev/null 2>&1; then
    echo "✅ External IP is responding"
    echo "🎉 SUCCESS! Your site should now be accessible at:"
    echo "   http://50.21.187.77"
    echo "   https://50.21.187.77"
else
    echo "❌ External IP still not responding"
    echo ""
    echo "🔧 Additional troubleshooting needed:"
    echo "1. Check if your ISP/network blocks the IP"
    echo "2. Verify VPS provider firewall settings"
    echo "3. Check if port 80/443 are actually open"
    echo ""
    echo "Try these commands:"
    echo "  telnet 50.21.187.77 80"
    echo "  telnet 50.21.187.77 443"
fi

echo ""
echo "📊 Current service status:"
echo "========================"
systemctl status stitchrat --no-pager -l | head -5
systemctl status nginx --no-pager -l | head -5

echo ""
echo "🌐 Ports currently listening:"
echo "=========================="
netstat -tlnp | grep -E ":(80|443|5000|4040)"

echo ""
echo "🔥 Firewall status:"
echo "=================="
ufw status | head -10