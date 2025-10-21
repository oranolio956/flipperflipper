# Terminal Commands for VPS Deployment

## Quick Start - What to Type in Terminal

### Option 1: Automated Deployment (Recommended)

**Step 1: Upload your code to the VPS**
```bash
# Make the upload script executable
chmod +x upload_to_vps.sh

# Upload your code
./upload_to_vps.sh
```

**Step 2: Connect to your VPS**
```bash
ssh root@50.21.187.77
# Password: tCY8Oswl
```

**Step 3: Run the automated deployment**
```bash
cd /opt/stitchrat
./deploy_to_vps.sh
```

That's it! Your application will be running at: **https://50.21.187.77**

---

### Option 2: Manual Step-by-Step

If you prefer to do it manually, here are the commands:

**1. Connect to VPS:**
```bash
ssh root@50.21.187.77
# Password: tCY8Oswl
```

**2. Update system:**
```bash
apt update && apt upgrade -y
```

**3. Install dependencies:**
```bash
apt install -y python3 python3-pip python3-venv git nginx supervisor ufw
apt install -y build-essential libssl-dev libffi-dev python3-dev
apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev
```

**4. Create user and directories:**
```bash
useradd -m -s /bin/bash stitchrat
mkdir -p /opt/stitchrat
chown stitchrat:stitchrat /opt/stitchrat
```

**5. Upload your code** (from your local machine):
```bash
# From your local machine where the code is:
scp -r . root@50.21.187.77:/opt/stitchrat/
```

**6. Set up Python environment** (back on VPS):
```bash
su - stitchrat
cd /opt/stitchrat
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
exit
```

**7. Configure environment:**
```bash
cat > /opt/stitchrat/.env << 'EOF'
STITCH_HOST=0.0.0.0
STITCH_PORT=5000
STITCH_DEBUG=false
STITCH_SERVER_PORT=4040
STITCH_ADMIN_USER=admin
STITCH_ADMIN_PASSWORD=YourSecurePassword123!
STITCH_ENABLE_HTTPS=true
STITCH_SSL_AUTO_GENERATE=true
STITCH_SSL_CN=50.21.187.77
EOF

chown stitchrat:stitchrat /opt/stitchrat/.env
chmod 600 /opt/stitchrat/.env
```

**8. Configure firewall:**
```bash
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8443/tcp
ufw allow 4040/tcp
```

**9. Start the application:**
```bash
cd /opt/stitchrat
sudo -u stitchrat /opt/stitchrat/venv/bin/python web_app_real.py
```

---

## Management Commands

Once deployed, use these commands to manage your application:

**Check if services are running:**
```bash
stitchrat-status
```

**Restart services:**
```bash
stitchrat-restart
```

**View live logs:**
```bash
journalctl -u stitchrat -f
```

**Stop the application:**
```bash
systemctl stop stitchrat
```

**Start the application:**
```bash
systemctl start stitchrat
```

**Check application status:**
```bash
systemctl status stitchrat
```

---

## Troubleshooting Commands

**Check if ports are in use:**
```bash
netstat -tlnp | grep :5000
netstat -tlnp | grep :4040
```

**Kill processes on specific ports:**
```bash
sudo lsof -ti:5000 | xargs sudo kill -9
sudo lsof -ti:4040 | xargs sudo kill -9
```

**Check firewall status:**
```bash
ufw status verbose
```

**View system resources:**
```bash
htop
df -h
free -h
```

**Check SSL certificates:**
```bash
ls -la /opt/stitchrat/certs/
openssl x509 -in /opt/stitchrat/certs/cert.pem -text -noout
```

---

## Access Information

- **Web Interface**: https://50.21.187.77
- **Default Login**: admin / YourSecurePassword123!
- **RAT Server Port**: 4040 (for payload connections)
- **Plesk Panel**: https://50.21.187.77:8443

---

## Important Security Notes

⚠️ **CRITICAL**: This is a penetration testing tool. Only use on systems you own or have explicit written permission to test.

1. **Change the default password** in `/opt/stitchrat/.env`
2. **Restrict firewall access** to specific IPs if needed:
   ```bash
   ufw delete allow 443/tcp
   ufw allow from YOUR_IP to any port 443
   ```
3. **Monitor logs regularly** for any unauthorized access attempts
4. **Keep the system updated**:
   ```bash
   apt update && apt upgrade -y
   ```

---

## Quick Commands Summary

```bash
# Upload code (from local machine)
./upload_to_vps.sh

# Connect to VPS
ssh root@50.21.187.77

# Deploy automatically
cd /opt/stitchrat && ./deploy_to_vps.sh

# Check status
stitchrat-status

# View logs
journalctl -u stitchrat -f

# Restart if needed
stitchrat-restart
```

Your VPS (1GB RAM, 1 vCore) is sufficient for small to medium-scale operations. The application will be accessible at **https://50.21.187.77** once deployed.