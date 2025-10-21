#!/bin/bash
# Quick fix for Nginx SSL configuration error

echo "Fixing Nginx SSL configuration..."

# Fix the Nginx configuration
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

# Test nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    
    # Continue with the rest of the deployment
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
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    echo "Starting services..."
    systemctl daemon-reload
    systemctl enable stitchrat
    systemctl enable nginx

    # Start the application first (it will generate SSL certs)
    systemctl start stitchrat
    
    echo "Waiting for SSL certificates to be generated..."
    sleep 15
    
    # Now start Nginx
    systemctl start nginx
    
    echo "Creating management scripts..."
    cat > /usr/local/bin/stitchrat-status << 'EOF'
#!/bin/bash
echo "=== Stitch RAT System Status ==="
echo "Application Service:"
systemctl status stitchrat --no-pager -l
echo ""
echo "Nginx Service:"
systemctl status nginx --no-pager -l
echo ""
echo "Recent Logs:"
journalctl -u stitchrat --no-pager -n 10
EOF

    cat > /usr/local/bin/stitchrat-restart << 'EOF'
#!/bin/bash
echo "Restarting Stitch RAT services..."
systemctl restart stitchrat
sleep 5
systemctl restart nginx
echo "Services restarted."
EOF

    chmod +x /usr/local/bin/stitchrat-status
    chmod +x /usr/local/bin/stitchrat-restart

    echo ""
    echo "🎉 DEPLOYMENT COMPLETED!"
    echo ""
    echo "🌐 Web Interface: https://50.21.187.77"
    echo "👤 Login: admin"
    echo "🔑 Password: StitchRAT_SecurePass_2025!"
    echo ""
    echo "Checking final status..."
    sleep 3
    stitchrat-status
    
else
    echo "❌ Nginx configuration still has errors. Please check manually."
fi
EOF