# Ubuntu VPS Deployment Guide for Enhanced Stitch

## 🚨 IMPORTANT LEGAL DISCLAIMER
This tool is for authorized penetration testing and red team exercises only. Ensure you have explicit written permission before deployment. Unauthorized use is illegal.

---

## 🖥️ VPS Requirements & Recommendations

### Minimum VPS Specifications
```
CPU: 1 vCPU (2+ recommended for multiple sessions)
RAM: 1GB (2GB+ recommended)
Storage: 20GB SSD
Network: Unmetered bandwidth
OS: Ubuntu 20.04 LTS or newer
```

### Recommended VPS Providers
- **DigitalOcean**: Good performance, reasonable pricing
- **Vultr**: Fast deployment, multiple locations
- **Linode**: Reliable, good documentation
- **AWS EC2**: Enterprise-grade (more expensive)

---

## 🔧 Initial VPS Setup

### 1. Secure SSH Access
```bash
# Change default SSH port (security through obscurity)
sudo nano /etc/ssh/sshd_config
# Change: Port 22 → Port 2222 (or another non-standard port)
# Add: PermitRootLogin no
# Add: PasswordAuthentication no (after setting up SSH keys)

# Restart SSH service
sudo systemctl restart ssh

# Set up SSH key authentication (from your local machine)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
ssh-copy-id -p 2222 username@your-vps-ip
```

### 2. Configure Firewall
```bash
# Install and configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2222/tcp  # SSH (your custom port)
sudo ufw allow 4433/tcp  # Stitch bind port
sudo ufw allow 4455/tcp  # Stitch listen port
sudo ufw enable

# Check firewall status
sudo ufw status verbose
```

### 3. System Updates & Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-tk python3-dev \
    build-essential libssl-dev libffi-dev git screen tmux \
    xvfb x11-utils

# Install Python packages
pip3 install pycrypto requests colorama
```

---

## 🛡️ Security Hardening

### 1. Network Security
```bash
# Install fail2ban (protection against brute force)
sudo apt install fail2ban

# Configure fail2ban for SSH
sudo nano /etc/fail2ban/jail.local
```

Add this configuration:
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
```

```bash
# Start and enable fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### 2. Hide Server Identity
```bash
# Install nginx as reverse proxy (optional but recommended)
sudo apt install nginx

# Basic nginx configuration to hide server details
sudo nano /etc/nginx/nginx.conf
# Add in http block:
# server_tokens off;
```

### 3. Process Security
```bash
# Create dedicated user for Stitch (don't run as root)
sudo useradd -m -s /bin/bash stitch-user
sudo usermod -aG sudo stitch-user

# Set up directory permissions
sudo mkdir -p /opt/stitch
sudo chown stitch-user:stitch-user /opt/stitch
```

---

## 📁 Stitch Installation & Configuration

### 1. Deploy Stitch to VPS
```bash
# Switch to stitch user
sudo su - stitch-user

# Create installation directory
mkdir -p /opt/stitch
cd /opt/stitch

# Copy your enhanced Stitch files here
# (Use scp, rsync, or git clone)
```

### 2. Configure Stitch for VPS Environment
```bash
# Navigate to Stitch directory
cd /opt/stitch

# Set up virtual display for GUI components
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &

# Make Xvfb start automatically
echo 'export DISPLAY=:99' >> ~/.bashrc
echo 'Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &' >> ~/.bashrc
```

### 3. Initial Stitch Configuration
```bash
# Run Stitch for initial setup
python3 main.py

# In Stitch console, configure for VPS:
stitch> # This will create initial config files

# Exit and edit configuration manually if needed
```

---

## 🌐 Network Configuration

### 1. Configure Stitch Listener
When generating payloads, use these settings:

**Bind Configuration:**
- Bind to host: `0.0.0.0` (all interfaces)
- Bind port: `4433`

**Listen Configuration:**
- Connect to host: `YOUR_VPS_IP`
- Connect port: `4455`

### 2. Domain Setup (Recommended)
```bash
# If you have a domain, point it to your VPS
# This makes payloads less suspicious than raw IP addresses

# Example DNS records:
# A record: meeting.yourdomain.com → YOUR_VPS_IP
# A record: conference.yourdomain.com → YOUR_VPS_IP
```

### 3. SSL/TLS Setup (Optional but Recommended)
```bash
# Install certbot for Let's Encrypt certificates
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate (if using domain)
sudo certbot --nginx -d meeting.yourdomain.com
```

---

## 🚀 Deployment Scripts

### 1. Stitch Startup Script
Create `/opt/stitch/start-stitch.sh`:
```bash
#!/bin/bash
cd /opt/stitch
export DISPLAY=:99

# Start virtual display if not running
if ! pgrep -x "Xvfb" > /dev/null; then
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
fi

# Start Stitch
python3 main.py
```

```bash
chmod +x /opt/stitch/start-stitch.sh
```

### 2. Systemd Service (Auto-start on boot)
Create `/etc/systemd/system/stitch.service`:
```ini
[Unit]
Description=Stitch C2 Server
After=network.target

[Service]
Type=simple
User=stitch-user
WorkingDirectory=/opt/stitch
Environment=DISPLAY=:99
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1024x768x24
ExecStart=/usr/bin/python3 main.py
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
```

---

## 📊 Monitoring & Logging

### 1. Log Management
```bash
# Create log rotation for Stitch logs
sudo nano /etc/logrotate.d/stitch
```

Add:
```
/opt/stitch/Logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 stitch-user stitch-user
}
```

### 2. System Monitoring
```bash
# Install htop for system monitoring
sudo apt install htop

# Monitor Stitch processes
ps aux | grep python3
netstat -tlnp | grep :4433
netstat -tlnp | grep :4455
```

### 3. Connection Logging
Create `/opt/stitch/monitor-connections.sh`:
```bash
#!/bin/bash
while true; do
    echo "$(date): Active connections:" >> /opt/stitch/connection.log
    netstat -an | grep :4433 >> /opt/stitch/connection.log
    netstat -an | grep :4455 >> /opt/stitch/connection.log
    echo "---" >> /opt/stitch/connection.log
    sleep 300  # Log every 5 minutes
done
```

---

## 🔒 Operational Security (OpSec)

### 1. VPS Provider Considerations
- **Use cryptocurrency** for payment if possible
- **Avoid providers requiring extensive KYC**
- **Consider offshore providers** for additional privacy
- **Use VPN** when accessing VPS management panels

### 2. Traffic Obfuscation
```bash
# Consider using domain fronting or CDN services
# Route traffic through Cloudflare or similar services
# Use common ports (80, 443, 8080) instead of custom ports
```

### 3. Data Security
```bash
# Encrypt sensitive data on disk
sudo apt install ecryptfs-utils

# Create encrypted directory for sensitive files
mkdir /opt/stitch/encrypted
sudo mount -t ecryptfs /opt/stitch/encrypted /opt/stitch/encrypted
```

---

## 📋 Pre-Deployment Checklist

### System Security
- [ ] SSH key authentication configured
- [ ] Default SSH port changed
- [ ] Firewall (UFW) configured and enabled
- [ ] Fail2ban installed and configured
- [ ] System fully updated
- [ ] Non-root user created for Stitch

### Stitch Configuration
- [ ] All dependencies installed (Python3, tkinter, crypto libraries)
- [ ] Virtual display (Xvfb) working
- [ ] Stitch starts without errors
- [ ] Payload generation tested
- [ ] Network ports accessible (4433, 4455)

### Network Setup
- [ ] Firewall rules allow Stitch ports
- [ ] Domain DNS configured (if using domain)
- [ ] SSL certificates installed (if using HTTPS)
- [ ] Network connectivity tested

### Monitoring
- [ ] Log rotation configured
- [ ] System monitoring tools installed
- [ ] Connection logging script created
- [ ] Systemd service configured (optional)

---

## 🚨 Important Security Notes

### 1. Legal Compliance
- **Only use on systems you own or have explicit permission to test**
- **Document all authorized testing activities**
- **Follow responsible disclosure practices**
- **Comply with local and international laws**

### 2. Operational Security
- **Use VPN when accessing VPS**
- **Regularly rotate SSH keys**
- **Monitor for unauthorized access attempts**
- **Keep detailed logs of all activities**
- **Have incident response plan ready**

### 3. Data Protection
- **Encrypt all sensitive data**
- **Regularly backup important files**
- **Implement secure data destruction procedures**
- **Follow data retention policies**

---

## 🔧 Troubleshooting Common Issues

### 1. GUI Issues on Headless Server
```bash
# If GUI components fail:
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
python3 -c "import tkinter; print('GUI OK')"
```

### 2. Port Binding Issues
```bash
# Check if ports are in use:
sudo netstat -tlnp | grep :4433
sudo netstat -tlnp | grep :4455

# Kill processes using ports if needed:
sudo fuser -k 4433/tcp
sudo fuser -k 4455/tcp
```

### 3. Permission Issues
```bash
# Fix file permissions:
sudo chown -R stitch-user:stitch-user /opt/stitch
chmod +x /opt/stitch/*.py
```

---

## 📞 Support & Resources

### Log Locations
- Stitch logs: `/opt/stitch/Logs/`
- System logs: `/var/log/syslog`
- SSH logs: `/var/log/auth.log`
- UFW logs: `/var/log/ufw.log`

### Useful Commands
```bash
# Check Stitch status
systemctl status stitch

# View Stitch logs
tail -f /opt/stitch/Logs/stitch.log

# Monitor network connections
watch 'netstat -an | grep :4433'

# Check system resources
htop
df -h
free -h
```

This deployment guide ensures your enhanced Stitch C2 server is properly secured, monitored, and ready for authorized penetration testing activities.