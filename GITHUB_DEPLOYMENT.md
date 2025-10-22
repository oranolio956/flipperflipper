# 🚀 GitHub VPS Deployment - One Command Installation

## ✨ Super Simple Terminal-Only Deployment

You can now deploy your Stitch RAT to your VPS using **just one command** directly from GitHub!

---

## 🎯 What to Type in Your VPS Terminal

### Step 1: Connect to Your VPS
```bash
ssh root@50.21.187.77
# Password: tCY8Oswl
```

### Step 2: Run the One-Liner Installation
```bash
curl -sSL https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh | bash
```

**That's it!** 🎉 Your entire Stitch RAT system will be automatically deployed!

---

## 📋 What the Script Does Automatically

✅ **System Updates** - Updates Ubuntu packages  
✅ **Dependencies** - Installs Python, Nginx, Redis, etc.  
✅ **Code Download** - Clones latest code from GitHub  
✅ **Environment Setup** - Creates virtual environment  
✅ **SSL Certificates** - Auto-generates HTTPS certificates  
✅ **Firewall Config** - Secures your VPS  
✅ **Service Setup** - Creates systemd services  
✅ **Security Hardening** - Configures fail2ban, rate limiting  
✅ **Management Tools** - Installs helper commands  

---

## 🔐 Access Information

After deployment completes:

- **🌐 Web Interface**: https://50.21.187.77
- **👤 Admin Login**: admin / StitchRAT_SecurePass_2025!
- **🔌 RAT Server Port**: 4040 (for payload connections)
- **⚙️ Plesk Panel**: https://50.21.187.77:8443

---

## 🛠️ Management Commands

Once deployed, you can use these commands on your VPS:

```bash
# Check system status
stitchrat-status

# Restart all services
stitchrat-restart

# Update from GitHub
stitchrat-update

# View live logs
journalctl -u stitchrat -f
```

---

## 🔄 Updating Your Application

To update with the latest code from GitHub:

```bash
stitchrat-update
```

Or manually:
```bash
cd /opt/stitchrat
git pull origin cursor/setup-and-manage-vps-with-plesk-1813
/opt/stitchrat/venv/bin/pip install -r requirements.txt --upgrade
systemctl restart stitchrat
```

---

## 🔧 Advanced Configuration

### Custom GitHub Repository

If you want to use your own fork, edit the script variables:

```bash
# Download and edit the script
curl -sSL https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh > deploy.sh

# Edit these lines:
GITHUB_USER="YOUR_GITHUB_USERNAME"
GITHUB_REPO="YOUR_REPO_NAME"
GITHUB_BRANCH="your-branch-name"

# Run the modified script
chmod +x deploy.sh
./deploy.sh
```

### Environment Variables

After deployment, customize settings in `/opt/stitchrat/.env`:

```bash
nano /opt/stitchrat/.env
# Edit configuration as needed
systemctl restart stitchrat
```

---

## 🚨 Security Features Included

- **🔥 Firewall**: UFW configured with minimal ports
- **🛡️ fail2ban**: Protects against brute force attacks
- **🔒 SSL/TLS**: Auto-generated HTTPS certificates
- **⚡ Rate Limiting**: Nginx rate limiting on login/API
- **🔐 Secure Headers**: HSTS, XSS protection, etc.
- **👤 User Isolation**: Runs as dedicated user account
- **📝 Logging**: Comprehensive logging and rotation

---

## 🐛 Troubleshooting

### If the installation fails:

1. **Check you're running as root**:
   ```bash
   whoami  # Should show 'root'
   ```

2. **Check internet connectivity**:
   ```bash
   curl -I https://github.com
   ```

3. **Check system resources**:
   ```bash
   df -h    # Check disk space
   free -h  # Check memory
   ```

4. **View installation logs**:
   ```bash
   journalctl -xe
   ```

### If services won't start:

```bash
# Check service status
systemctl status stitchrat
systemctl status nginx
systemctl status redis-server

# Check logs
journalctl -u stitchrat -n 50
```

### If SSL certificates are missing:

```bash
# Regenerate certificates
rm -rf /opt/stitchrat/certs
systemctl restart stitchrat
sleep 10
systemctl restart nginx
```

---

## 📊 System Requirements

Your VPS specs are perfect:
- ✅ **Ubuntu 24.04** - Fully supported
- ✅ **1GB RAM** - Sufficient for small-medium operations
- ✅ **1 vCore** - Adequate processing power
- ✅ **10GB SSD** - Enough storage space

---

## ⚠️ Legal Disclaimer

**IMPORTANT**: This is a penetration testing tool for authorized security testing only.

- ✅ Only use on systems you own
- ✅ Only use with explicit written permission
- ✅ Follow all applicable laws and regulations
- ❌ Never use for unauthorized access
- ❌ Never use for malicious purposes

---

## 🎉 Success!

Once the script completes, you'll see:

```
🎉 Deployment successful! Access your RAT at: https://50.21.187.77
```

Your Stitch RAT is now fully operational and ready for authorized penetration testing!

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs with `journalctl -u stitchrat -f`
3. Ensure your VPS has internet connectivity
4. Verify you're running as root user

The deployment script is designed to be robust and handle most common issues automatically.