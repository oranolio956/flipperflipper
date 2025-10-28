# 📋 Pre-Deployment Checklist - IONOS VPS

## Before You Start Deployment

Complete this checklist to ensure smooth deployment of your web application on IONOS VPS.

---

## ✅ IONOS Account & VPS Setup

### 1. IONOS VPS Access
- [ ] I have purchased/activated an IONOS VPS
- [ ] I know my VPS IP address: `___________________`
- [ ] I have root SSH access credentials
- [ ] VPS is running Ubuntu 20.04 or 22.04
- [ ] VPS has at least 2GB RAM
- [ ] VPS has at least 20GB disk space

### 2. SSH Access Test
```bash
# Test SSH connection (replace with your IP)
ssh root@YOUR_VPS_IP
```
- [ ] SSH connection successful
- [ ] I can run sudo commands

---

## ✅ Domain Setup (If Using Custom Domain)

### 3. Domain Configuration
- [ ] I have a domain name: `___________________`
- [ ] Domain is registered (IONOS or elsewhere)
- [ ] I have access to domain DNS settings

### 4. DNS Records
In your IONOS Control Panel or domain registrar:
- [ ] Added A Record: `@` → `YOUR_VPS_IP`
- [ ] Added A Record: `www` → `YOUR_VPS_IP`
- [ ] Waited 15-30 minutes for DNS propagation

Test DNS propagation:
```bash
# Run from your local machine
nslookup your-domain.com
dig your-domain.com
```
- [ ] Domain resolves to correct IP

---

## ✅ GitHub Repository Access

### 5. GitHub Setup
- [ ] I have a GitHub account
- [ ] Repository is created/exists
- [ ] I know my repository URL: `git@github.com:_____/_____`
- [ ] Repository contains all necessary files:
  - [ ] `requirements.txt`
  - [ ] `web_app_real.py` or main application file
  - [ ] `config.yaml`
  - [ ] Other required files

### 6. GitHub SSH Key
- [ ] I have generated SSH key on my local machine
- [ ] SSH public key is added to GitHub account
- [ ] Can clone repository using SSH

Test GitHub access:
```bash
# Run from your local machine
ssh -T git@github.com
# Should see: "Hi username! You've successfully authenticated..."
```

---

## ✅ Security Preparations

### 7. Credentials Ready
- [ ] Strong admin password chosen: `___________________` (write down securely)
- [ ] Strong database password chosen (if applicable)
- [ ] Non-root username decided: `___________________` (default: eliteuser)

### 8. Security Keys to Generate
You'll need to generate these during deployment:
- [ ] Flask secret key (will use: `openssl rand -hex 32`)
- [ ] Encryption key (will use: `openssl rand -hex 32`)
- [ ] Auth token (will use: `openssl rand -hex 32`)

---

## ✅ IONOS Cloud Panel Configuration

### 9. IONOS Firewall Rules
Login to IONOS Cloud Panel → Your VPS → Firewall

Add these rules:
- [ ] Port 22 (SSH) - TCP - Allow from: Your IP or Anywhere
- [ ] Port 80 (HTTP) - TCP - Allow from: Anywhere
- [ ] Port 443 (HTTPS) - TCP - Allow from: Anywhere

**Screenshot saved:** Yes / No

---

## ✅ Local Machine Preparations

### 10. Local Tools Installed
On your local machine (Windows/Mac/Linux):
- [ ] SSH client installed and working
- [ ] Git installed (for repository management)
- [ ] Text editor (VS Code, Sublime, etc.)
- [ ] Browser ready for testing

### 11. Documentation Ready
- [ ] `VPS_DEPLOYMENT_GUIDE.md` downloaded or accessible
- [ ] `QUICK_DEPLOY_COMMANDS.sh` ready
- [ ] `TROUBLESHOOTING_QUICK_REFERENCE.md` accessible
- [ ] This checklist printed or on second monitor

---

## ✅ Knowledge Check

### 12. Basic Understanding
- [ ] I understand this is for authorized security testing only
- [ ] I have legal authorization to deploy this application
- [ ] I understand basic Linux commands (cd, ls, nano, etc.)
- [ ] I know how to use SSH
- [ ] I understand basic networking concepts
- [ ] I can read and follow command-line instructions

### 13. Time Allocation
- [ ] I have allocated 1-2 hours for initial deployment
- [ ] I have uninterrupted time to complete deployment
- [ ] I have backup plan if deployment takes longer

---

## ✅ Emergency Contacts & Support

### 14. Support Resources
- [ ] IONOS support contact info saved
- [ ] GitHub repository owner contact (if not you)
- [ ] Backup communication method available
- [ ] System administrator contact (if applicable)

---

## ✅ Backup & Recovery Plan

### 15. Backup Strategy
- [ ] I understand backups will be created automatically
- [ ] Backup location confirmed: `/opt/backups`
- [ ] I know how to restore from backup if needed

---

## 📝 Deployment Day Checklist

### Pre-Deployment (30 minutes before)
- [ ] All above items completed
- [ ] Fresh coffee/beverage ready ☕
- [ ] Second monitor or printed guide available
- [ ] Notepad ready for recording IPs, passwords, etc.
- [ ] Phone on silent (minimize interruptions)

### During Deployment
- [ ] Follow commands in sequence (don't skip steps)
- [ ] Read each command before executing
- [ ] Record any errors encountered
- [ ] Take notes of any warnings or issues
- [ ] Save credentials securely as generated

### Post-Deployment Testing
- [ ] Application accessible via IP
- [ ] Application accessible via domain
- [ ] Login works with credentials
- [ ] SSL certificate valid
- [ ] No errors in logs
- [ ] Firewall rules working
- [ ] Can restart services successfully

---

## 🎯 Quick Reference Info

**Record your deployment information here:**

```
=== VPS Information ===
VPS Provider: IONOS
VPS IP Address: ___________________
SSH Username: root (initially)
SSH Port: 22

=== Domain Information ===
Domain Name: ___________________
DNS Provider: ___________________

=== Repository Information ===
GitHub Username: ___________________
Repository Name: ___________________
Repository URL: ___________________

=== Application Credentials ===
Admin Username: ___________________
Admin Password: ___________________ (store securely!)
Secret Key: (generated during deployment)
Encryption Key: (generated during deployment)

=== Service Ports ===
Application Port: 5000 (internal)
HTTP Port: 80 (external)
HTTPS Port: 443 (external)
SSH Port: 22

=== Important Paths ===
Application Directory: /opt/elite-rat
Virtual Environment: /opt/elite-rat/venv
Logs Directory: /opt/elite-rat/logs
Data Directory: /opt/elite-rat/data
Nginx Config: /etc/nginx/sites-available/elite-rat
Systemd Service: /etc/systemd/system/elite-rat.service

=== Deployment Date & Time ===
Started: ___________________
Completed: ___________________
Deployed By: ___________________
```

---

## 🚨 Important Warnings

### LEGAL WARNING
- ⚠️ This application is for authorized security testing ONLY
- ⚠️ You must have explicit written permission
- ⚠️ Unauthorized use is illegal and unethical
- ⚠️ Ensure compliance with all applicable laws

### SECURITY WARNING
- 🔒 Never commit credentials to Git
- 🔒 Always use strong passwords
- 🔒 Keep .env file secure
- 🔒 Regularly update and patch system
- 🔒 Monitor logs for suspicious activity
- 🔒 Enable fail2ban for SSH protection

### TECHNICAL WARNING
- ⚙️ Test in development environment first (if possible)
- ⚙️ Backup before making changes
- ⚙️ Read all commands before executing
- ⚙️ Don't run commands you don't understand
- ⚙️ Keep deployment guide accessible
- ⚙️ Document any custom changes

---

## ✅ Final Pre-Flight Check

Before starting deployment, confirm:

- [ ] ✅ All checklist items above completed
- [ ] ✅ VPS accessible via SSH
- [ ] ✅ Domain DNS configured (if using)
- [ ] ✅ GitHub repository accessible
- [ ] ✅ Credentials prepared
- [ ] ✅ Time allocated
- [ ] ✅ Documentation ready
- [ ] ✅ Emergency contacts available
- [ ] ✅ Legal authorization confirmed

---

## 🚀 Ready to Deploy?

If all items are checked, you're ready to proceed with deployment!

**Next Steps:**
1. Open `VPS_DEPLOYMENT_GUIDE.md`
2. Have `QUICK_DEPLOY_COMMANDS.sh` ready
3. Keep `TROUBLESHOOTING_QUICK_REFERENCE.md` accessible
4. Start deployment following Step 1

---

## 📞 Need Help?

If you're stuck on any checklist item:

1. **IONOS Issues**: Contact IONOS Support
2. **GitHub Issues**: Check GitHub documentation
3. **DNS Issues**: Use online DNS checkers (whatsmydns.net)
4. **General Linux**: Google specific error messages
5. **Application Issues**: Check repository documentation

---

## 💡 Pro Tips

- Take your time - rushing leads to mistakes
- Copy commands carefully - typos cause errors
- Save credentials in a password manager
- Take screenshots of important steps
- Document any customizations you make
- Test each major step before proceeding

---

**Good luck with your deployment! 🎉**

Remember: Preparation is 80% of success!
