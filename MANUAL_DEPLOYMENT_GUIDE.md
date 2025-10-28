# 🚀 FlipperFlipper - Complete Manual Deployment Guide for Ubuntu VPS

## 📋 What You're Deploying

**FlipperFlipper** is a Python-based Remote Administration Tool (RAT) / C2 Server with:
- C2 Server (Port 5555) - receives connections from agents/payloads
- Web Dashboard (Port 5000) - manage agents, generate payloads, view data
- SSL/TLS encryption
- Auto-update system
- Systemd service for automatic startup

---

## ⚙️ STEP 1: Initial VPS Setup & Update

First, connect to your Ubuntu VPS and update the system.

```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Update package lists
apt-get update

# Upgrade installed packages (optional but recommended)
apt-get upgrade -y
```

**What this does:** Updates the package database and upgrades existing packages to latest versions.

---

## 📦 STEP 2: Install System Dependencies

Install all required system packages:

```bash
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    openssl \
    screen \
    tmux \
    curl \
    wget \
    net-tools \
    build-essential \
    libssl-dev \
    libffi-dev \
    ufw
```

**What each package does:**
- `python3` - Python runtime (version 3.x)
- `python3-pip` - Python package installer
- `python3-venv` - Virtual environment support
- `python3-dev` - Python development headers (needed for compiling packages)
- `git` - Version control to clone repository
- `openssl` - SSL certificate generation
- `screen`/`tmux` - Terminal multiplexers (useful for running processes)
- `curl`/`wget` - Download tools
- `net-tools` - Network utilities (netstat, ifconfig)
- `build-essential` - C compiler and build tools (needed for some Python packages)
- `libssl-dev`/`libffi-dev` - Development libraries for cryptography
- `ufw` - Uncomplicated Firewall

---

## 📥 STEP 3: Clone the Repository

Create installation directory and clone the project:

```bash
# Create installation directory
mkdir -p /opt/elite_rat

# Clone the repository
git clone https://github.com/oranolio956/flipperflipper.git /opt/elite_rat

# Navigate to the directory
cd /opt/elite_rat

# Verify files are present
ls -la
```

**What this does:** 
- Creates `/opt/elite_rat` directory (standard location for optional software)
- Clones the GitHub repository into that directory
- Lists files to confirm successful clone

---

## 🐍 STEP 4: Create Python Virtual Environment

Create an isolated Python environment to avoid conflicts:

```bash
# Navigate to installation directory
cd /opt/elite_rat

# Create virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
which python
# Should output: /opt/elite_rat/venv/bin/python
```

**What this does:**
- Creates isolated Python environment in `venv/` directory
- Activating it ensures all packages install locally, not system-wide
- Prevents version conflicts with other Python applications

---

## 📚 STEP 5: Install Python Dependencies

Install required Python packages:

```bash
# Make sure venv is activated (you should see (venv) in prompt)
source /opt/elite_rat/venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements from requirements.txt
pip install -r requirements.txt

# Verify installations
pip list
```

**What this does:**
- Upgrades pip to latest version
- Installs all Python packages listed in `requirements.txt`:
  - **flask** - Web framework for dashboard
  - **flask-socketio** - WebSocket support for real-time updates
  - **cryptography** - Encryption/decryption
  - **pyyaml** - Configuration file parsing
  - **pillow** - Image processing (screenshots)
  - **psutil** - System monitoring
  - **requests** - HTTP client

**Alternative:** If you encounter issues, install packages manually:

```bash
pip install flask flask-socketio flask-cors cryptography pyyaml pyjwt pillow dnspython psutil requests python-engineio python-socketio python-dotenv colorama
```

---

## 🔒 STEP 6: Generate SSL Certificates

Create self-signed SSL certificates for secure HTTPS:

```bash
# Create certificates directory
mkdir -p /opt/elite_rat/certs

# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -newkey rsa:4096 -nodes \
    -out /opt/elite_rat/certs/server.crt \
    -keyout /opt/elite_rat/certs/server.key \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Secure the private key
chmod 600 /opt/elite_rat/certs/server.key

# Verify certificates were created
ls -la /opt/elite_rat/certs/
```

**What this does:**
- Creates `certs/` directory for SSL certificates
- Generates RSA 4096-bit self-signed certificate
- Sets restrictive permissions on private key (only root can read)
- Certificate info: Country=US, State=State, etc. (can be modified)

**Note:** Browsers will show "insecure" warning for self-signed certs - this is normal.

---

## 🔧 STEP 7: Create Startup Script

Create a script to start the C2 server and web interface:

```bash
cat > /opt/elite_rat/start_server.py << 'EOF'
#!/usr/bin/env python3
"""
Elite RAT Startup Script
Starts both C2 server and web interface
"""
import os
import sys
import time
import threading

# Add workspace to path
sys.path.insert(0, '/opt/elite_rat')

# Set environment variables
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'EliteC2Password123!'
os.environ['ELITE_C2_HOST'] = '0.0.0.0'
os.environ['ELITE_C2_PORT'] = '5555'
os.environ['ELITE_WEB_PORT'] = '5000'

def start_c2_server():
    """Start the C2 server for agent connections"""
    try:
        from Core.c2_server import SecureC2Server
        
        server = SecureC2Server(
            host='0.0.0.0',  # Listen on all network interfaces
            port=5555,
            use_ssl=True,
            cert_file='/opt/elite_rat/certs/server.crt',
            key_file='/opt/elite_rat/certs/server.key'
        )
        
        print("[+] C2 Server starting on port 5555...")
        server.start()
    except Exception as e:
        print(f"[-] C2 Server error: {e}")
        import traceback
        traceback.print_exc()

def start_web_server():
    """Start the web dashboard interface"""
    try:
        from Core.web_api import app, init_app
        
        # Initialize the Flask app
        init_app()
        
        print("[+] Web interface starting on port 5000...")
        app.run(
            host='0.0.0.0',  # Accessible from any IP
            port=5000,
            ssl_context=('/opt/elite_rat/certs/server.crt', 
                        '/opt/elite_rat/certs/server.key'),
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"[-] Web server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("ELITE RAT C2 SERVER")
    print("=" * 60)
    print(f"[+] Starting services...")
    print(f"[+] Web Interface: https://0.0.0.0:5000")
    print(f"[+] C2 Server: 0.0.0.0:5555")
    print("=" * 60)
    
    # Start C2 server in background thread
    c2_thread = threading.Thread(target=start_c2_server, daemon=True)
    c2_thread.start()
    
    # Wait for C2 to initialize
    time.sleep(2)
    
    # Start web server (blocking - runs in main thread)
    start_web_server()
EOF

# Make it executable
chmod +x /opt/elite_rat/start_server.py
```

**What this does:**
- Creates Python script that starts both servers simultaneously
- C2 server runs in background thread (for agent connections)
- Web server runs in main thread (for dashboard access)
- Sets default credentials: admin / EliteC2Password123!

---

## 🧪 STEP 8: Test Manual Startup (Optional but Recommended)

Before creating the service, test if everything works:

```bash
# Make sure you're in the directory
cd /opt/elite_rat

# Activate virtual environment
source venv/bin/activate

# Run the server manually
python start_server.py
```

**What to expect:**
- Should see startup messages
- "Web interface starting on port 5000..."
- "C2 Server starting on port 5555..."

**Test access:**
- Open browser: `https://YOUR_VPS_IP:5000`
- Login: admin / EliteC2Password123!

**To stop:** Press `Ctrl+C`

**If errors occur:**
- Check Python import errors
- Verify all dependencies installed: `pip list`
- Check logs for specific errors

---

## 🚀 STEP 9: Configure Firewall

Allow necessary ports through the firewall:

```bash
# Allow SSH (important - don't lock yourself out!)
ufw allow 22/tcp comment 'SSH Access'

# Allow web interface
ufw allow 5000/tcp comment 'Elite RAT Web Dashboard'

# Allow C2 server
ufw allow 5555/tcp comment 'Elite RAT C2 Server'

# Enable firewall
ufw --force enable

# Check firewall status
ufw status numbered
```

**What this does:**
- Opens port 22 (SSH - so you can still connect)
- Opens port 5000 (Web Dashboard)
- Opens port 5555 (C2 Server for agents)
- Enables firewall
- All other ports remain blocked by default

**Important:** Make sure SSH (22) is allowed before enabling firewall!

---

## 🔄 STEP 10: Create Systemd Service (Auto-Start on Boot)

Create a systemd service so the server starts automatically:

```bash
cat > /etc/systemd/system/elite_rat.service << 'EOF'
[Unit]
Description=Elite RAT C2 Server
After=network.target
Documentation=https://github.com/oranolio956/flipperflipper

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elite_rat
Environment="PATH=/opt/elite_rat/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/elite_rat/venv/bin/python /opt/elite_rat/start_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/elite_rat.log
StandardError=append:/var/log/elite_rat_error.log

# Security settings
NoNewPrivileges=false
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

**What each section does:**

**[Unit]**
- `Description` - Human-readable service name
- `After=network.target` - Start after network is available

**[Service]**
- `Type=simple` - Standard foreground process
- `User=root` - Run as root (required for some features)
- `WorkingDirectory` - Set current directory
- `Environment` - Add virtual environment to PATH
- `ExecStart` - Command to run
- `Restart=always` - Auto-restart on crash
- `RestartSec=10` - Wait 10 seconds before restarting
- `StandardOutput/Error` - Log locations

**[Install]**
- `WantedBy=multi-user.target` - Start on normal boot

---

## ▶️ STEP 11: Enable and Start the Service

```bash
# Reload systemd to recognize new service
systemctl daemon-reload

# Enable service (auto-start on boot)
systemctl enable elite_rat

# Start the service now
systemctl start elite_rat

# Check service status
systemctl status elite_rat

# View live logs
journalctl -u elite_rat -f
```

**What this does:**
- Reloads systemd configuration
- Enables service to start on boot
- Starts the service immediately
- Shows current status
- Follows logs in real-time (Ctrl+C to exit)

**Status indicators:**
- `Active: active (running)` = ✅ Working!
- `Active: failed` = ❌ Check logs: `journalctl -u elite_rat -n 50`

---

## 🌐 STEP 12: Access the Dashboard

Get your VPS public IP and access the dashboard:

```bash
# Get your public IP
curl ifconfig.me

# Or
curl ipinfo.io/ip
```

**Access URLs:**
- Web Dashboard: `https://YOUR_VPS_IP:5000`
- C2 Server: `YOUR_VPS_IP:5555` (agents connect here)

**Default Login:**
- Username: `admin`
- Password: `EliteC2Password123!`

**⚠️ IMPORTANT:** Change the default password immediately after first login!

---

## 🔄 STEP 13: Setup Auto-Updates from GitHub (Optional)

Create a script to automatically pull updates from GitHub:

```bash
cat > /opt/elite_rat/auto_update.sh << 'EOF'
#!/bin/bash
# Auto-update script for Elite RAT

INSTALL_DIR="/opt/elite_rat"
SERVICE_NAME="elite_rat"
LOG_FILE="/var/log/elite_rat_update.log"

cd $INSTALL_DIR

# Fetch latest from GitHub
git fetch origin main > /dev/null 2>&1

# Compare local and remote versions
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Update detected - pulling changes..." | tee -a $LOG_FILE
    
    # Stop service
    systemctl stop $SERVICE_NAME
    
    # Stash any local changes
    git stash > /dev/null 2>&1
    
    # Pull updates
    git pull origin main
    
    # Update Python dependencies
    source venv/bin/activate
    pip install -q --upgrade -r requirements.txt 2>/dev/null || true
    
    # Restart service
    systemctl start $SERVICE_NAME
    
    echo "[$(date)] Update complete - service restarted" | tee -a $LOG_FILE
else
    echo "[$(date)] No updates available" >> $LOG_FILE
fi
EOF

# Make executable
chmod +x /opt/elite_rat/auto_update.sh

# Test the script
/opt/elite_rat/auto_update.sh
```

**Schedule auto-updates (runs every 5 minutes):**

```bash
# Add to root's crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/elite_rat/auto_update.sh") | crontab -

# View crontab to verify
crontab -l

# View update logs
tail -f /var/log/elite_rat_update.log
```

**What this does:**
- Checks GitHub every 5 minutes for updates
- If updates found, stops service, pulls changes, updates dependencies
- Automatically restarts service
- Logs all update activity

**To disable:** Remove the cron job with `crontab -e` and delete the line.

---

## 📊 STEP 14: Useful Management Commands

### Service Management

```bash
# Start service
systemctl start elite_rat

# Stop service
systemctl stop elite_rat

# Restart service
systemctl restart elite_rat

# Check status
systemctl status elite_rat

# Enable auto-start on boot
systemctl enable elite_rat

# Disable auto-start
systemctl disable elite_rat
```

### View Logs

```bash
# Real-time logs
journalctl -u elite_rat -f

# Last 100 lines
journalctl -u elite_rat -n 100

# Logs from last hour
journalctl -u elite_rat --since "1 hour ago"

# Logs from today
journalctl -u elite_rat --since today

# Check log files directly
tail -f /var/log/elite_rat.log
tail -f /var/log/elite_rat_error.log
```

### Manual Updates

```bash
# Navigate to directory
cd /opt/elite_rat

# Stop service
systemctl stop elite_rat

# Pull latest changes
git pull origin main

# Activate venv and update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart service
systemctl start elite_rat
```

### Check What Ports Are Listening

```bash
# Check if ports are listening
netstat -tulpn | grep -E '5000|5555'

# Or use ss command
ss -tulpn | grep -E '5000|5555'

# Check specific port
lsof -i :5000
lsof -i :5555
```

### System Resource Usage

```bash
# Check CPU and memory
htop

# Or simpler top command
top

# Check disk space
df -h

# Check memory
free -h
```

---

## 🔒 STEP 15: Security Hardening (Highly Recommended)

### Change Default Passwords

```bash
# Change Linux root password
passwd root

# Change web dashboard password (do this in the web interface)
# Login → Settings → Change Password
```

### Setup SSH Key Authentication (Disable Password Login)

```bash
# On your LOCAL machine (not VPS), generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to VPS
ssh-copy-id root@YOUR_VPS_IP

# On VPS, disable password authentication
nano /etc/ssh/sshd_config

# Find and change these lines:
# PasswordAuthentication no
# PubkeyAuthentication yes
# PermitRootLogin prohibit-password

# Restart SSH service
systemctl restart sshd
```

### Install Fail2Ban (Prevent Brute Force Attacks)

```bash
# Install fail2ban
apt-get install fail2ban -y

# Enable and start
systemctl enable fail2ban
systemctl start fail2ban

# Check status
fail2ban-client status
```

### Restrict Access to Specific IPs (Optional)

If you only access from specific IPs:

```bash
# Allow SSH only from your IP
ufw delete allow 22/tcp
ufw allow from YOUR_HOME_IP to any port 22 proto tcp

# Allow dashboard only from your IP
ufw delete allow 5000/tcp
ufw allow from YOUR_HOME_IP to any port 5000 proto tcp

# C2 port should remain open for agents
# Or restrict if agents come from known IPs
```

---

## 🐛 Troubleshooting Common Issues

### Service Won't Start

```bash
# Check detailed error logs
journalctl -u elite_rat -n 100 --no-pager

# Try running manually to see errors
cd /opt/elite_rat
source venv/bin/activate
python start_server.py
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :5000
lsof -i :5555

# Kill the process
kill -9 <PID>

# Or stop conflicting service
systemctl stop <service_name>
```

### Python Import Errors

```bash
# Reinstall dependencies
cd /opt/elite_rat
source venv/bin/activate
pip install --upgrade --force-reinstall -r requirements.txt
```

### Can't Access Dashboard

```bash
# Check if service is running
systemctl status elite_rat

# Check if ports are open
ufw status

# Check if port is listening
netstat -tulpn | grep 5000

# Try accessing locally
curl -k https://localhost:5000
```

### SSL Certificate Errors

```bash
# Regenerate certificates
rm -rf /opt/elite_rat/certs/
mkdir -p /opt/elite_rat/certs/

openssl req -x509 -newkey rsa:4096 -nodes \
    -out /opt/elite_rat/certs/server.crt \
    -keyout /opt/elite_rat/certs/server.key \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

chmod 600 /opt/elite_rat/certs/server.key

# Restart service
systemctl restart elite_rat
```

---

## 📁 Important Files and Directories

```
/opt/elite_rat/                    # Main installation directory
├── venv/                          # Python virtual environment
├── certs/                         # SSL certificates
│   ├── server.crt                 # SSL certificate
│   └── server.key                 # SSL private key
├── Core/                          # Core application modules
├── Application/                   # Application logic
├── Configuration/                 # Configuration modules
├── start_server.py               # Startup script
├── requirements.txt              # Python dependencies
├── config.yaml                   # Configuration file
└── auto_update.sh                # Auto-update script

/var/log/elite_rat.log            # Service output logs
/var/log/elite_rat_error.log      # Service error logs
/var/log/elite_rat_update.log     # Auto-update logs

/etc/systemd/system/elite_rat.service  # Systemd service file
```

---

## 🎯 Quick Reference Commands

```bash
# Service Management
systemctl start elite_rat          # Start
systemctl stop elite_rat           # Stop
systemctl restart elite_rat        # Restart
systemctl status elite_rat         # Status

# Logs
journalctl -u elite_rat -f         # Follow logs
journalctl -u elite_rat -n 100     # Last 100 lines

# Manual Update
cd /opt/elite_rat
git pull origin main
systemctl restart elite_rat

# Check Ports
netstat -tulpn | grep -E '5000|5555'

# Get Public IP
curl ifconfig.me

# Test Web Interface
curl -k https://localhost:5000
```

---

## ✅ Post-Deployment Checklist

- [ ] Service is running: `systemctl status elite_rat`
- [ ] Ports are open in firewall: `ufw status`
- [ ] Can access dashboard: `https://YOUR_IP:5000`
- [ ] Changed default password in dashboard
- [ ] Changed Linux root password
- [ ] Auto-updates configured (optional)
- [ ] SSH key authentication setup (recommended)
- [ ] Fail2ban installed (recommended)
- [ ] Bookmarked dashboard URL
- [ ] Documented credentials securely

---

## 🎉 You're Done!

Your Elite RAT C2 server is now:
- ✅ Installed and configured
- ✅ Running as a systemd service
- ✅ Auto-starts on boot
- ✅ Auto-updates from GitHub (if configured)
- ✅ Accessible via web dashboard
- ✅ Ready to receive agent connections

**Access your dashboard at:** `https://YOUR_VPS_IP:5000`

**Generate payloads** in the dashboard to create agents that connect back to your C2 server!

---

## 📖 Additional Resources

- **Project README:** `/opt/elite_rat/README.md`
- **Configuration:** `/opt/elite_rat/config.yaml`
- **VPS Guide:** `/opt/elite_rat/VPS_INSTALL_GUIDE.md`
- **GitHub Repo:** https://github.com/oranolio956/flipperflipper

---

## ⚠️ Legal Disclaimer

**This tool is for educational and authorized security testing ONLY.**

You must:
- Only use on systems you own or have explicit written permission to test
- Comply with all local, state, and federal laws
- Never use for unauthorized access or malicious purposes

The authors and contributors are not responsible for misuse of this software.

---

**Last Updated:** 2025-10-22
**Version:** 1.0
**Maintained by:** FlipperFlipper Project
