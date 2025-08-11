# 🚀 Deploy ProxyAssessmentTool to the Cloud (FREE)

This guide will help you deploy your proxy tool to the cloud using:
- **Vercel** for Frontend (Free)
- **Render** for Backend (Free)

## **Prerequisites**
- GitHub account (free at github.com)
- Vercel account (free at vercel.com)
- Render account (free at render.com)

## **Quick Deploy (15 minutes)**

### **Step 1: Prepare Your Code**

```bash
# Make deployment script executable
chmod +x deploy-vercel-render.sh

# Run the deployment wizard
./deploy-vercel-render.sh
```

## **Manual Deploy Steps**

### **Step 1: Create GitHub Repository**

1. Go to https://github.com/new
2. Create a new repository named `proxy-assessment-tool`
3. Make it public (or private if you have GitHub Pro)
4. Don't initialize with README

In your terminal:
```bash
cd /workspace
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/proxy-assessment-tool.git
git branch -M main
git push -u origin main
```

### **Step 2: Deploy Frontend to Vercel**

**Option A: Using Vercel CLI**
```bash
npm install -g vercel
cd frontend
vercel
# Follow prompts, accept defaults
vercel --prod
```

**Option B: Using Vercel Dashboard**
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Select `frontend` as the root directory
4. Click Deploy

Your frontend will be available at: `https://your-project.vercel.app`

### **Step 3: Deploy Backend to Render**

1. Go to https://dashboard.render.com/new/web
2. Connect your GitHub account
3. Select your repository
4. Configure:
   - **Name**: proxy-assessment-backend
   - **Region**: Oregon (US West)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     cd backend && pip install -r requirements.txt && mkdir -p geoip && curl -L "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb" -o geoip/GeoLite2-City.mmdb
     ```
   - **Start Command**: 
     ```bash
     cd backend && python proxy_tester.py
     ```

5. Add Environment Variables:
   - `PYTHON_VERSION` = `3.11.0`
   - `PORT` = `8000`
   - `CORS_ORIGINS` = `https://your-project.vercel.app` (your Vercel URL)

6. Click "Create Web Service"

Your backend will be available at: `https://proxy-assessment-backend.onrender.com`

### **Step 4: Update Frontend with Backend URL**

1. In `frontend/index.html`, update line 731:
   ```javascript
   : 'https://proxy-assessment-backend.onrender.com';  // Your Render URL
   ```

2. Redeploy frontend:
   ```bash
   cd frontend
   vercel --prod
   ```

## **Alternative: One-Click Deploy**

### **Deploy to Vercel**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/proxy-assessment-tool&root-directory=frontend)

### **Deploy to Render**
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/proxy-assessment-tool)

## **Free Tier Limitations**

### **Vercel Free Tier**
- ✅ Unlimited websites
- ✅ 100GB bandwidth/month
- ✅ Automatic HTTPS
- ✅ Global CDN

### **Render Free Tier**
- ✅ 750 hours/month
- ⚠️ Spins down after 15 min inactivity
- ⚠️ First request takes 30-60s to wake
- ✅ Automatic HTTPS
- ✅ 100GB bandwidth/month

## **Testing Your Deployment**

1. Open your Vercel URL
2. Click "Auto-Discover Proxies"
3. Watch proxies being discovered!
4. Click "Start Testing" to validate them

**Note**: First API call will be slow (30-60s) as Render wakes up.

## **Troubleshooting**

### **CORS Errors**
Make sure `CORS_ORIGINS` environment variable in Render matches your Vercel URL.

### **WebSocket Issues**
Free Render tier doesn't support WebSockets. The app will fallback to polling.

### **Slow First Request**
This is normal on Render free tier. Consider upgrading to keep service always-on.

## **Upgrade Options**

### **Better Performance**
- **Render Starter**: $7/month (no sleep, better performance)
- **Railway**: Alternative with $5 free credit/month
- **Fly.io**: Alternative with generous free tier

### **Custom Domain**
Both Vercel and Render support custom domains on free tier!

## **Next Steps**

1. ⭐ Star the repository on GitHub
2. 🔔 Watch for updates
3. 🐛 Report issues
4. 🚀 Share with others!

---

**Congratulations! Your ProxyAssessmentTool is now live on the internet!** 🎉