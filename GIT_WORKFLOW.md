# 🚀 Complete GitHub Terminal Workflow

## 📋 Overview

This guide shows you how to upload your code to GitHub and deploy to your VPS using **only terminal commands**.

---

## 🎯 Quick Start - 3 Commands

### 1. Upload to GitHub
```bash
chmod +x simple_github_upload.sh
./simple_github_upload.sh
```

### 2. Deploy to VPS
```bash
ssh root@50.21.187.77
curl -sSL https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh | bash
```

### 3. Access Your Application
```
https://50.21.187.77
```

**That's it!** 🎉

---

## 📖 Detailed Workflow

### Step 1: Prepare Your Local Environment

**Install Git** (if not already installed):
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install git

# macOS
brew install git

# Or download from: https://git-scm.com/
```

**Configure Git** (first time only):
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 2: Upload Code to GitHub

**Option A: Use the automated script**
```bash
chmod +x simple_github_upload.sh
./simple_github_upload.sh
```

**Option B: Manual Git commands**
```bash
# Initialize git repository
git init
git remote add origin https://github.com/oranolio956/flipperflipper.git

# Add files
git add .

# Commit changes
git commit -m "Deploy Stitch RAT - $(date)"

# Push to GitHub
git push -u origin cursor/setup-and-manage-vps-with-plesk-1813
```

### Step 3: Deploy to VPS

**Connect to your VPS:**
```bash
ssh root@50.21.187.77
# Password: tCY8Oswl
```

**Run the deployment:**
```bash
curl -sSL https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh | bash
```

---

## 🔐 GitHub Authentication

### Method 1: Personal Access Token (Recommended)

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"

2. **Configure Token:**
   - Name: `Stitch RAT Deployment`
   - Expiration: `90 days` (or your preference)
   - Scopes: Check `repo` (full repository access)
   - Click "Generate token"

3. **Save the Token:**
   - Copy the token (you won't see it again!)
   - Use this token as your password when git prompts for credentials

4. **Use Token in Terminal:**
   ```bash
   # When prompted for username: enter your GitHub username
   # When prompted for password: paste your token
   ```

### Method 2: SSH Keys (Advanced)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub:
# Go to https://github.com/settings/keys
# Click "New SSH key"
# Paste the public key
```

Then use SSH URL:
```bash
git remote set-url origin git@github.com:oranolio956/flipperflipper.git
```

---

## 🔄 Update Workflow

### To Update Your Code:

1. **Make changes to your code**

2. **Upload to GitHub:**
   ```bash
   ./simple_github_upload.sh
   ```

3. **Update VPS:**
   ```bash
   ssh root@50.21.187.77
   stitchrat-update
   ```

### Or manually update VPS:
```bash
ssh root@50.21.187.77
cd /opt/stitchrat
git pull origin cursor/setup-and-manage-vps-with-plesk-1813
/opt/stitchrat/venv/bin/pip install -r requirements.txt --upgrade
systemctl restart stitchrat
```

---

## 🛠️ Troubleshooting

### Git Push Fails

**Problem:** `Authentication failed`
```bash
# Solution: Use personal access token
# Go to https://github.com/settings/tokens
# Generate new token with 'repo' scope
# Use token as password when prompted
```

**Problem:** `Repository not found`
```bash
# Check remote URL
git remote -v

# Fix remote URL
git remote set-url origin https://github.com/oranolio956/flipperflipper.git
```

**Problem:** `Branch doesn't exist`
```bash
# Create and switch to branch
git checkout -b cursor/setup-and-manage-vps-with-plesk-1813

# Push with upstream
git push -u origin cursor/setup-and-manage-vps-with-plesk-1813
```

### VPS Deployment Fails

**Problem:** `Connection refused`
```bash
# Check VPS is accessible
ping 50.21.187.77

# Check SSH connection
ssh root@50.21.187.77
```

**Problem:** `Script not found`
```bash
# Verify GitHub URL
curl -I https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh
```

**Problem:** `Permission denied`
```bash
# Make sure you're root on VPS
whoami  # Should show 'root'

# Or use sudo
sudo bash -c "curl -sSL https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh | bash"
```

---

## 📁 File Structure

After setup, your workflow will be:

```
Local Machine:
├── main.py
├── requirements.txt
├── simple_github_upload.sh  ← Upload script
├── github_deploy.sh         ← Deployment script
└── ... (your code)

GitHub Repository:
└── https://github.com/oranolio956/flipperflipper
    └── cursor/setup-and-manage-vps-with-plesk-1813/
        ├── main.py
        ├── requirements.txt
        ├── github_deploy.sh
        └── ... (your code)

VPS:
└── /opt/stitchrat/
    ├── main.py
    ├── requirements.txt
    ├── venv/
    └── ... (deployed code)
```

---

## 🎯 Complete Example Session

```bash
# 1. Upload to GitHub
./simple_github_upload.sh
# Enter GitHub credentials when prompted

# 2. Deploy to VPS
ssh root@50.21.187.77
curl -sSL https://raw.githubusercontent.com/oranolio956/flipperflipper/cursor/setup-and-manage-vps-with-plesk-1813/github_deploy.sh | bash

# 3. Check deployment
stitchrat-status

# 4. Access application
# Open browser: https://50.21.187.77
# Login: admin / StitchRAT_SecurePass_2025!
```

---

## ✅ Benefits of This Workflow

- 🔄 **Version Control**: All changes tracked in Git
- 🌐 **GitHub Backup**: Code safely stored online  
- 🚀 **Easy Deployment**: One command deploys to VPS
- 🔄 **Easy Updates**: Simple update process
- 📱 **Remote Access**: Deploy from anywhere
- 🔒 **Secure**: Uses HTTPS and authentication

---

## 🎉 Success Indicators

You'll know it worked when:

1. **GitHub Upload Success:**
   ```
   ✅ Successfully uploaded to GitHub!
   Repository: https://github.com/oranolio956/flipperflipper
   ```

2. **VPS Deployment Success:**
   ```
   🎉 Deployment successful! Access your RAT at: https://50.21.187.77
   ```

3. **Application Access:**
   - Web interface loads at: https://50.21.187.77
   - Login works with: admin / StitchRAT_SecurePass_2025!

Your complete GitHub → VPS workflow is now ready! 🚀