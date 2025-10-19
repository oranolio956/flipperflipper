# 🚂 DEPLOY TO RAILWAY.APP - EASIEST ANONYMOUS HOSTING

## ⚡ **5-MINUTE DEPLOYMENT**

Railway is **THE BEST** option for you:
- ✅ Super easy (like Replit)
- ✅ 100% anonymous (crypto payment)
- ✅ 24/7 uptime guaranteed
- ✅ No technical knowledge needed

---

## 📋 **WHAT YOU NEED**

1. ✅ Temp email address (for signup)
2. ✅ $5 in Bitcoin/Ethereum (optional, for paid plan)
3. ✅ 5 minutes of time

---

## 🎯 **STEP-BY-STEP GUIDE**

### **STEP 1: Create Anonymous Account (2 minutes)**

#### **Get Temp Email:**
```
Go to: https://temp-mail.org
Copy your temporary email address
(e.g., random123@tempmail.com)
```

#### **Sign Up:**
```
1. Go to: https://railway.app
2. Click "Start a New Project"
3. Click "Login" > "Email"
4. Enter your temp email
5. Check temp-mail.org for verification code
6. Enter code
7. ✅ Account created!
```

**No name, phone, or payment needed yet!**

---

### **STEP 2: Prepare Your Code (3 minutes)**

#### **On Your Computer:**

```bash
cd /workspace/telegran

# Create Railway config
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python3 userbot.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

# Create Procfile (Railway needs this)
echo "worker: python3 userbot.py" > Procfile

# Create runtime.txt (specify Python version)
echo "python-3.11" > runtime.txt

# Create .railwayignore (don't upload these)
cat > .railwayignore << 'EOF'
__pycache__/
*.pyc
*.session
*.session-journal
userbot_data.json
backups/
alerts.log
*.log
.git/
EOF
```

---

### **STEP 3: Upload to Railway (2 minutes)**

#### **Option A: Web Upload (Easiest - No CLI)**

```
1. In Railway dashboard, click "New Project"
2. Click "Deploy from GitHub repo"
3. Click "Deploy without GitHub" (anonymous!)
4. Click "Empty Project"
5. Click "Add Service" > "Empty Service"
6. In the service, click "Settings"
7. Click "Source" > "Upload"
8. Drag your entire /workspace/telegran folder
9. Wait 30 seconds for upload
10. ✅ Code uploaded!
```

#### **Option B: Railway CLI (Faster if you know terminal)**

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Or on Windows:
# Download from: https://github.com/railwayapp/cli/releases

# Login
railway login
# (Opens browser, click Allow)

# In your telegran folder
cd /workspace/telegran

# Initialize project
railway init

# Name it: telegran-userbot

# Link to project
railway link

# Upload everything
railway up

# ✅ Code uploaded!
```

---

### **STEP 4: Set Environment Variables (2 minutes)**

#### **In Railway Dashboard:**

```
1. Click your service
2. Click "Variables" tab
3. Click "Add Variable"
4. Add these one by one:

Variable Name: API_ID
Value: your_api_id_from_telegram

Variable Name: API_HASH
Value: your_api_hash_from_telegram

Variable Name: PHONE_NUMBER
Value: +1234567890

5. Click "Add" for each
6. ✅ Variables saved!
```

---

### **STEP 5: Deploy! (1 minute)**

```
1. Go to "Deployments" tab
2. Click "Deploy"
3. Watch the logs
4. Wait for "Deployment successful" ✅
5. Your bot is now running 24/7!
```

---

### **STEP 6: First Login (ONE TIME ONLY)**

**Important:** Your bot needs to login to Telegram once.

#### **View Logs:**
```
1. In Railway, click your service
2. Click "Logs" tab
3. You'll see: "Enter code:"
```

#### **Problem:** You can't interact with Railway logs!

#### **Solution: Use Local Login First**

```bash
# On your computer, run this ONCE:
cd /workspace/telegran
python3 userbot.py

# It will ask for login code
# Enter the code from Telegram
# ✅ Session file created: userbot_session.session
```

#### **Upload Session File:**
```bash
# Option A: Via Railway CLI
railway run python3 -c "print('Session ready')"
# This uploads your local session

# Option B: Manual upload
# In Railway dashboard:
1. Click "Settings"
2. Click "Volumes"
3. Click "Add Volume"
4. Mount path: /app
5. Upload userbot_session.session file
```

**Alternative: Use Railway Shell**
```
1. In Railway, click your service
2. Click "Settings" > "Deploy"
3. Enable "Public URL" (temporarily)
4. SSH into it:
   railway run bash
5. Run: python3 userbot.py
6. Enter login code
7. Exit
8. Disable "Public URL"
```

---

### **STEP 7: Verify It's Working**

#### **Check Logs:**
```
1. Go to "Logs" tab
2. You should see:
   ✅ "Connected to Telegram"
   ✅ "Joined target group"
   ✅ "Userbot ready and listening..."
```

#### **Test in Telegram:**
```
1. Have someone join your target group
2. Check Railway logs
3. You should see: "✅ Welcomed [username]"
```

---

## 💰 **PAYMENT (OPTIONAL - FOR 24/7)**

Railway free trial gives you **500 hours** (about 20 days).

After that, you need to pay.

### **Pay Anonymously with Crypto:**

```
1. In Railway, click Settings (gear icon)
2. Click "Billing"
3. Click "Add Credits"
4. Choose payment method: "Cryptocurrency"
5. Choose amount: $10 (lasts 1 month)
6. Copy the crypto address
7. Send Bitcoin or Ethereum
8. Wait 10 minutes for confirmation
9. ✅ Credits added!
```

**No name, address, or card needed!**

### **Pricing:**
```
- Free: $0 (500 hours trial)
- Hobby: $5/month (unlimited usage)
- Pro: $20/month (more resources)

Recommended: Hobby ($5/month)
```

---

## 🎛️ **RAILWAY DASHBOARD GUIDE**

### **Important Sections:**

#### **1. Logs**
- Real-time bot activity
- Errors and warnings
- Message sending confirmations

#### **2. Metrics**
- CPU usage
- Memory usage
- Network usage

#### **3. Variables**
- Your API_ID, API_HASH, PHONE_NUMBER
- Can change anytime

#### **4. Deployments**
- Deploy new versions
- Rollback to previous versions

#### **5. Settings**
- Restart policy
- Auto-sleep (disable this!)
- Custom domain (optional)

---

## ⚙️ **IMPORTANT SETTINGS**

### **Keep Bot Running 24/7:**

```
1. Click "Settings"
2. Scroll to "Sleep"
3. Make sure "Never sleep" is selected
4. ✅ Bot stays on!
```

### **Auto-Restart on Crash:**

```
Already configured in railway.json:
- restartPolicyType: "ON_FAILURE"
- restartPolicyMaxRetries: 10

If bot crashes, Railway restarts it automatically!
```

---

## 🔧 **UPDATING YOUR BOT**

### **Method 1: Re-upload (Web)**
```
1. Edit your code locally
2. Go to Railway > Settings > Source
3. Click "Upload"
4. Drag updated telegran folder
5. Wait 30 seconds
6. ✅ Updated!
```

### **Method 2: Railway CLI**
```bash
cd /workspace/telegran
# Make your changes
railway up
# ✅ Updated!
```

---

## 🐛 **TROUBLESHOOTING**

### **Problem: "Deployment Failed"**
```
Solution:
1. Check logs for error
2. Common issues:
   - Missing requirements.txt
   - Missing Procfile
   - Wrong Python version

Fix:
1. Make sure requirements.txt exists
2. Make sure Procfile has: worker: python3 userbot.py
3. Make sure runtime.txt has: python-3.11
```

### **Problem: "Module not found"**
```
Solution:
Add to requirements.txt:
cryptography==41.0.7

Then re-deploy.
```

### **Problem: "Login code needed"**
```
Solution:
1. Login locally first (see Step 6)
2. Upload session file
3. Re-deploy
```

### **Problem: "Bot not responding"**
```
Solution:
1. Check logs for errors
2. Verify environment variables set
3. Verify session file uploaded
4. Check if bot sleeping (Settings > Sleep > Never)
```

---

## 🎯 **COMPLETE CHECKLIST**

Before you start:
- [ ] Temp email ready
- [ ] API_ID and API_HASH from Telegram
- [ ] Phone number ready
- [ ] Code prepared (Procfile, railway.json)

Deployment:
- [ ] Railway account created
- [ ] Code uploaded
- [ ] Environment variables set
- [ ] Deployed successfully
- [ ] Login completed (session file)
- [ ] Logs show "Userbot ready"
- [ ] Test message sent successfully

Optional:
- [ ] Payment added (crypto)
- [ ] Sleep disabled
- [ ] Auto-restart enabled
- [ ] Monitoring set up

---

## 🚀 **YOU'RE READY!**

**Total time: 5-10 minutes**

**Steps:**
1. Sign up Railway (temp email)
2. Upload code
3. Set variables
4. Deploy
5. Login once
6. Pay with crypto (optional, after 20 days)

**Done! Bot runs 24/7 anonymously!**

---

## 💡 **TIPS**

### **Stay Anonymous:**
- ✅ Use temp email
- ✅ Pay with crypto (Bitcoin/Ethereum)
- ✅ Don't add real name
- ✅ Don't connect GitHub
- ✅ Use VPN when accessing Railway

### **Save Money:**
- Small project = $5/month is enough
- Monitor usage in Metrics tab
- Disable features you don't use

### **Security:**
- Don't enable "Public URL" unless needed
- Keep session file secret
- Use strong API_HASH

---

## 📞 **RAILWAY SUPPORT**

If you need help:
- Discord: https://discord.gg/railway
- Docs: https://docs.railway.app
- Status: https://status.railway.app

---

**🎉 EASIEST ANONYMOUS DEPLOYMENT - READY IN 5 MINUTES! 🎉**
