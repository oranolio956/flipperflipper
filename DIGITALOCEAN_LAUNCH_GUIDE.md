# 🚀 How to Launch Your Web App on DigitalOcean (Super Simple Guide)

## What You're Launching

This is a **web-based Remote Administration Tool (RAT)** called "Stitch RAT" with an enhanced web interface. It's like a control panel that runs in your web browser where you can manage remote computers.

---

## 📋 What You Need Before Starting

1. **A DigitalOcean Account** (you already have this - I can see it in your screenshot!)
2. **A credit card** (for DigitalOcean billing)
3. **10-15 minutes** of your time
4. **This code** (which you already have in `/workspace`)

---

## 🎯 Step-by-Step Instructions (Like You're 5)

### Step 1: Create a Server (Called a "Droplet" on DigitalOcean)

1. **Go to your DigitalOcean dashboard** (cloud.digitalocean.com)
2. **Click the green "Create" button** (top right)
3. **Select "Droplets"**
4. **Choose these settings:**
   - **Image**: Ubuntu 22.04 LTS (x64)
   - **Plan**: Basic
   - **CPU Options**: Regular ($6/month is fine to start)
   - **Datacenter**: Choose the one closest to you
   - **Authentication**: Choose "SSH Key" (recommended) or "Password" (easier but less secure)
   - **Hostname**: Give it a name like "my-rat-server"
5. **Click "Create Droplet"**
6. **Wait 1-2 minutes** for it to be created

### Step 2: Get Your Server's IP Address

1. After your droplet is created, you'll see it in your dashboard
2. **Copy the IP address** - it looks like: `123.456.789.012`
3. Save this somewhere - you'll need it!

### Step 3: Connect to Your Server

**On Mac/Linux:**
1. Open Terminal
2. Type: `ssh root@YOUR_IP_ADDRESS` (replace YOUR_IP_ADDRESS with the actual IP)
3. Type `yes` if asked about fingerprint
4. Enter your password (if you chose password auth)

**On Windows:**
1. Download **PuTTY** (a program to connect to servers)
2. Open PuTTY
3. Enter your IP address
4. Click "Connect"
5. Login as "root"

### Step 4: Upload Your Code to the Server

**Option A: Using Git (Recommended)**
```bash
# On your server, type these commands one by one:
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git elite-rat
cd elite-rat
```

**Option B: Manual Upload**
1. On your local computer, compress the `/workspace` folder into a ZIP file
2. Use **FileZilla** (free FTP program) or **SCP** to upload the ZIP
3. On server: `unzip workspace.zip -d /opt/elite-rat`

### Step 5: Install Required Software

On your server, run this **magic command** that installs everything:

```bash
# Update system
apt update && apt upgrade -y

# Install Python and required packages
apt install -y python3 python3-pip python3-venv git nginx ufw

# Create a working directory
cd /opt/elite-rat

# Create a Python virtual environment (isolated space for your app)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt
```

### Step 6: Configure Your App

Create a settings file:

```bash
# Create environment file
nano /opt/elite-rat/.env
```

Paste this (press `Ctrl+Shift+V` to paste):

```bash
# Admin Login
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=ChangeThisToSomethingSecure123!

# Server Settings
STITCH_HOST=0.0.0.0
STITCH_PORT=5000
STITCH_DEBUG=false

# Security
STITCH_SECRET_KEY=your-super-secret-random-key-change-this

# Enable file logging
STITCH_ENABLE_FILE_LOGGING=true
STITCH_LOG_LEVEL=INFO
```

**Important:** 
- Change `STITCH_ADMIN_PASSWORD` to your own secure password!
- Change `STITCH_SECRET_KEY` to something random

To save and exit:
- Press `Ctrl + X`
- Press `Y` 
- Press `Enter`

### Step 7: Set Up Firewall (Security)

```bash
# Enable firewall
ufw allow 22/tcp      # SSH - so you can connect
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 5000/tcp    # Your web app
ufw --force enable    # Turn on firewall
```

### Step 8: Create a Service (So It Runs Forever)

```bash
# Create a service file
nano /etc/systemd/system/elite-rat.service
```

Paste this:

```ini
[Unit]
Description=Elite RAT Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elite-rat
Environment="PATH=/opt/elite-rat/venv/bin"
ExecStart=/opt/elite-rat/venv/bin/python3 /opt/elite-rat/web_app_real.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter)

Now activate the service:

```bash
# Reload systemd
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable elite-rat

# Start the service now
systemctl start elite-rat

# Check if it's running
systemctl status elite-rat
```

### Step 9: Set Up Nginx (Optional - Makes It Professional)

This puts a professional web server in front of your app:

```bash
# Create Nginx configuration
nano /etc/nginx/sites-available/elite-rat
```

Paste this:

```nginx
server {
    listen 80;
    server_name YOUR_IP_ADDRESS;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Replace `YOUR_IP_ADDRESS` with your actual IP!

Save and activate:

```bash
# Create symbolic link to enable site
ln -s /etc/nginx/sites-available/elite-rat /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

### Step 10: Access Your Web App! 🎉

1. **Open your web browser**
2. **Go to:** `http://YOUR_IP_ADDRESS` (or `http://YOUR_IP_ADDRESS:5000` if you skipped Nginx)
3. **Login with:**
   - Username: `admin`
   - Password: (whatever you set in the .env file)

---

## 🔧 Useful Commands (For Later)

**Check if your app is running:**
```bash
systemctl status elite-rat
```

**View real-time logs:**
```bash
journalctl -u elite-rat -f
```

**Restart your app:**
```bash
systemctl restart elite-rat
```

**Stop your app:**
```bash
systemctl stop elite-rat
```

**Update your code:**
```bash
cd /opt/elite-rat
git pull
systemctl restart elite-rat
```

---

## 🚨 Troubleshooting

### "Can't connect to the website"
1. Check if service is running: `systemctl status elite-rat`
2. Check firewall: `ufw status`
3. Check if port 5000 is listening: `netstat -tulpn | grep 5000`

### "Login doesn't work"
1. Check your .env file: `cat /opt/elite-rat/.env`
2. Make sure password matches what you set
3. Check logs: `journalctl -u elite-rat -n 50`

### "Service fails to start"
1. Check logs: `journalctl -u elite-rat -n 50`
2. Try running manually:
   ```bash
   cd /opt/elite-rat
   source venv/bin/activate
   python3 web_app_real.py
   ```
3. Look for error messages

---

## 🔒 Security Notes (Important!)

1. **Change default passwords immediately**
2. **Use SSH keys instead of passwords** for server access
3. **Enable HTTPS** (use Let's Encrypt - free!)
4. **Keep your server updated:** `apt update && apt upgrade`
5. **Monitor your logs regularly**
6. **This tool is for authorized testing only** - don't use it illegally!

---

## 🎓 What Actually Happened?

In simple terms:
1. ✅ You created a computer in the cloud (Droplet)
2. ✅ You installed Python and needed software
3. ✅ You uploaded your code
4. ✅ You configured it to run automatically
5. ✅ You opened it to the internet
6. ✅ Now you can access it from anywhere!

---

## 💰 Cost

- **Basic Droplet**: $6-12/month
- **You can destroy it anytime** to stop charges
- **First time users** often get $200 free credit!

---

## 🆘 Need More Help?

1. **DigitalOcean Docs**: https://docs.digitalocean.com
2. **Check logs**: Most problems show in logs
3. **Community**: DigitalOcean has great community tutorials

---

## 📚 Next Steps (After It's Running)

1. **Set up a domain name** (like `myrat.com` instead of IP address)
2. **Add HTTPS** with Let's Encrypt (free SSL certificate)
3. **Set up automated backups**
4. **Configure monitoring/alerts**
5. **Harden security** (fail2ban, etc.)

---

**That's it! You now have a live web application running on the internet!** 🎉
