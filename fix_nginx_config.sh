#!/bin/bash
# Fix Nginx configuration issues

echo "🔧 Fixing Nginx configuration..."

# Stop nginx to fix the configuration
systemctl stop nginx

# Create a clean, working Nginx configuration without rate limiting zones for now
cat > /etc/nginx/sites-available/stitchrat << 'EOF'
server {
    listen 80 default_server;
    server_name 50.21.187.77 _;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Hide server version
    server_tokens off;
    
    # Client body size limit
    client_max_body_size 100M;
    
    # Main application - proxy to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Static files
    location /static/ {
        alias /opt/stitchrat/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    # Favicon
    location /favicon.ico {
        alias /opt/stitchrat/static/img/favicon.svg;
        expires 1y;
    }
}
EOF

# Remove any conflicting configurations
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/stitchrat-test

# Enable our site
ln -sf /etc/nginx/sites-available/stitchrat /etc/nginx/sites-enabled/

# Test the configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    
    # Start nginx
    systemctl start nginx
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx started successfully!"
        
        # Test connectivity
        sleep 3
        echo "🌐 Testing connectivity..."
        
        if curl -s http://50.21.187.77 >/dev/null 2>&1; then
            echo "✅ SUCCESS! Site is now accessible!"
            echo ""
            echo "🎉 Your Stitch RAT is ready!"
            echo "=========================="
            echo "🌐 URL: http://50.21.187.77"
            echo "👤 Username: admin"
            echo "🔑 Password: StitchRAT_SecurePass_2025!"
            echo ""
            echo "✨ Features:"
            echo "• Modern professional interface"
            echo "• No SSL certificate warnings"
            echo "• Glassmorphism design"
            echo "• Enterprise-grade appearance"
            echo ""
        else
            echo "❌ Still having connectivity issues"
            echo "Let's check what's actually running..."
            
            # Install net-tools for debugging
            apt install -y net-tools
            echo "Checking ports:"
            netstat -tlnp | grep -E ":(80|5000)"
        fi
    else
        echo "❌ Failed to start Nginx"
        systemctl status nginx --no-pager -l
    fi
else
    echo "❌ Nginx configuration still has errors"
    nginx -t
fi

echo ""
echo "📊 Final Status:"
echo "==============="
systemctl is-active stitchrat && echo "✅ Stitch RAT: Running" || echo "❌ Stitch RAT: Not running"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Not running"