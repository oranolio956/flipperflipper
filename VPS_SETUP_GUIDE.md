# 🚀 Stitch Web Interface - VPS Setup Guide

## Quick Start (1-Minute Setup)

### Step 1: Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Clone repository (if not already done)
# git clone <your-repo-url>
cd /path/to/stitch

# Install Python dependencies
python3 -m pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env  # or create new .env file
nano .env

# Set your credentials:
STITCH_ADMIN_USER=your_admin_username
STITCH_ADMIN_PASSWORD=your_secure_password_12chars_min
STITCH_SECRET_KEY=your-random-secret-key
```

### Step 3: Start the Application
```bash
# Start the web interface
python3 start_stitch_web.py

# Or run in background
nohup python3 start_stitch_web.py > logs/stitch.log 2>&1 &
```

### Step 4: Access the Interface
- Open your browser to: `http://your-vps-ip:5000`
- Login with your configured credentials
- Default: `admin` / `stitch2024secure`

## 🔒 Security Configuration

### Firewall Setup
```bash
# Allow SSH and web interface
sudo ufw allow 22
sudo ufw allow 5000
sudo ufw enable
```

### SSL/HTTPS Setup (Recommended)
```bash
# Install certbot for Let's Encrypt
sudo apt install certbot -y

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Update .env file
STITCH_ENABLE_HTTPS=true
STITCH_SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
STITCH_SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### Nginx Reverse Proxy (Optional)
```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/stitch
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/stitch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Server Configuration
STITCH_HOST=0.0.0.0              # Bind address
STITCH_PORT=5000                 # Port number
STITCH_DEBUG=false               # Debug mode

# Security
STITCH_BEHIND_PROXY=false        # Set to true if using Nginx
STITCH_ENABLE_HTTPS=true         # Enable HTTPS
STITCH_MAX_LOGIN_ATTEMPTS=5      # Login attempt limit
STITCH_LOGIN_LOCKOUT_MINUTES=15  # Lockout duration

# Logging
STITCH_LOG_LEVEL=INFO            # Log level
STITCH_LOG_FILE=logs/stitch.log  # Log file path
```

### Systemd Service (Auto-start on boot)
```bash
# Create service file
sudo nano /etc/systemd/system/stitch.service
```

Add this content:
```ini
[Unit]
Description=Stitch Web Interface
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/stitch
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 start_stitch_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable stitch
sudo systemctl start stitch
sudo systemctl status stitch
```

## 🛠 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Permission denied**
   ```bash
   sudo chown -R $USER:$USER /path/to/stitch
   chmod +x start_stitch_web.py
   ```

3. **Module not found**
   ```bash
   python3 -m pip install -r requirements.txt --user
   ```

4. **SSL certificate issues**
   ```bash
   # Check certificate
   openssl x509 -in /path/to/cert.pem -text -noout
   ```

### Log Files
- Application logs: `logs/stitch.log`
- System logs: `sudo journalctl -u stitch -f`
- Nginx logs: `/var/log/nginx/error.log`

## 📱 Mobile-Friendly Interface

The login page is fully responsive and works great on:
- Desktop browsers
- Mobile devices
- Tablets
- Different screen sizes

## 🎨 Login Page Features

- Modern glassmorphism design
- Animated background
- Password visibility toggle
- Real-time form validation
- Security warnings
- Mobile-responsive layout
- Dark theme optimized

## 🔄 Updates and Maintenance

### Update the application
```bash
git pull origin main
python3 -m pip install -r requirements.txt --upgrade
sudo systemctl restart stitch  # if using systemd
```

### Backup configuration
```bash
cp .env .env.backup
tar -czf stitch-backup-$(date +%Y%m%d).tar.gz .env logs/ data/
```

## 📞 Support

If you encounter issues:
1. Check the logs: `tail -f logs/stitch.log`
2. Verify dependencies: `python3 -c "import flask; print('OK')"`
3. Test connectivity: `curl http://localhost:5000`
4. Check firewall: `sudo ufw status`

---

**⚠️ Security Note**: Always change default credentials and use HTTPS in production!