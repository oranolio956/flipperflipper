# 🤖 GitHub Actions Automated Deployment

## Overview

This sets up **automatic deployment** to your VPS whenever you push code to GitHub!

---

## 🚀 Setup Instructions

### Step 1: Add Secrets to GitHub

1. **Go to your GitHub repository:**
   - Visit: https://github.com/oranolio956/flipperflipper

2. **Navigate to Settings:**
   - Click "Settings" tab
   - Click "Secrets and variables" → "Actions"

3. **Add Repository Secrets:**
   Click "New repository secret" and add these:

   **Secret Name:** `VPS_HOST`  
   **Value:** `50.21.187.77`

   **Secret Name:** `VPS_USER`  
   **Value:** `root`

   **Secret Name:** `VPS_PASSWORD`  
   **Value:** `tCY8Oswl`

### Step 2: Enable GitHub Actions

The workflow file is already created at `.github/workflows/deploy.yml`

### Step 3: Test Automatic Deployment

1. **Make any change to your code**
2. **Push to GitHub:**
   ```bash
   ./simple_github_upload.sh
   ```
3. **Watch the deployment:**
   - Go to your GitHub repository
   - Click "Actions" tab
   - See the deployment in progress!

---

## 🎯 How It Works

**Automatic Triggers:**
- ✅ Every time you push to the deployment branch
- ✅ Manual trigger from GitHub Actions tab

**What It Does:**
1. 🔄 Pulls latest code to VPS
2. 📦 Updates Python dependencies  
3. 🔄 Restarts services
4. ✅ Verifies deployment

---

## 📊 Monitoring Deployments

### View Deployment Status:
1. Go to: https://github.com/oranolio956/flipperflipper/actions
2. Click on any deployment to see logs
3. Green ✅ = Success, Red ❌ = Failed

### Manual Deployment:
1. Go to Actions tab
2. Click "Deploy to VPS" workflow
3. Click "Run workflow"
4. Click "Run workflow" button

---

## 🛠️ Workflow Features

- **🔒 Secure**: Uses encrypted secrets
- **📝 Logging**: Full deployment logs
- **✅ Verification**: Checks if services are running
- **🔄 Automatic**: Deploys on every push
- **📱 Manual**: Can trigger manually

---

## 🎉 Benefits

- **Zero-Touch Deployment**: Push code → Automatic deployment
- **Always Up-to-Date**: VPS stays in sync with GitHub
- **Deployment History**: See all deployments in Actions tab
- **Error Notifications**: Get notified if deployment fails

Your VPS will now automatically update every time you push code to GitHub! 🚀