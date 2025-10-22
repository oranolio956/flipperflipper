# 🚀 Free Email Setup Guide

Complete guide to set up **FREE** email verification without paid services like Mailjet.

## 🎯 **Available Free Methods**

### 1. **Gmail SMTP (Recommended)**
- ✅ **100% Free**
- ✅ **Reliable delivery**
- ✅ **Professional appearance**

### 2. **Outlook/Hotmail SMTP**
- ✅ **100% Free**
- ✅ **Microsoft reliability**
- ✅ **Good deliverability**

### 3. **Telegram Bot**
- ✅ **100% Free**
- ✅ **Instant delivery**
- ✅ **Mobile-friendly**

### 4. **Discord Webhook**
- ✅ **100% Free**
- ✅ **Rich formatting**
- ✅ **Real-time notifications**

### 5. **Webhook.site**
- ✅ **100% Free**
- ✅ **No setup required**
- ✅ **Perfect for testing**

---

## 🔧 **Setup Instructions**

### **Method 1: Gmail SMTP (Easiest)**

1. **Create Gmail Account** (if you don't have one)
   - Go to [gmail.com](https://gmail.com)
   - Create a new account

2. **Enable 2-Factor Authentication**
   - Go to Google Account settings
   - Security → 2-Step Verification
   - Enable it

3. **Generate App Password**
   - Google Account → Security → App passwords
   - Select "Mail" and "Other"
   - Enter "Stitch RAT" as app name
   - Copy the 16-character password

4. **Set Environment Variables**
   ```bash
   export FROM_EMAIL="your-gmail@gmail.com"
   export GMAIL_APP_PASSWORD="your-16-char-app-password"
   export FROM_NAME="Your App Name"
   ```

5. **Test the Setup**
   ```bash
   python3 test_server.py
   ```

### **Method 2: Outlook SMTP**

1. **Create Outlook Account**
   - Go to [outlook.com](https://outlook.com)
   - Create new account

2. **Set Environment Variables**
   ```bash
   export FROM_EMAIL="your-email@outlook.com"
   export OUTLOOK_PASSWORD="your-outlook-password"
   export FROM_NAME="Your App Name"
   ```

### **Method 3: Telegram Bot**

1. **Create Telegram Bot**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot`
   - Follow instructions to get bot token

2. **Get Chat ID**
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

3. **Set Environment Variables**
   ```bash
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```

### **Method 4: Discord Webhook**

1. **Create Discord Webhook**
   - Go to your Discord server
   - Server Settings → Integrations → Webhooks
   - Create New Webhook
   - Copy webhook URL

2. **Set Environment Variables**
   ```bash
   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
   ```

### **Method 5: Webhook.site (Testing)**

1. **Get Webhook URL**
   - Visit [webhook.site](https://webhook.site)
   - Copy your unique URL

2. **Set Environment Variables**
   ```bash
   export WEBHOOK_SITE_URL="https://webhook.site/your-unique-id"
   ```

---

## ⚙️ **Complete Setup Script**

Create a `.env` file with your chosen method:

```bash
# .env file
USE_FREE_EMAIL=true
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Your App Name

# Choose ONE method below:

# Gmail SMTP (Recommended)
GMAIL_APP_PASSWORD=your-16-char-app-password

# OR Outlook SMTP
# OUTLOOK_PASSWORD=your-outlook-password

# OR Telegram Bot
# TELEGRAM_BOT_TOKEN=your-bot-token
# TELEGRAM_CHAT_ID=your-chat-id

# OR Discord Webhook
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# OR Webhook.site (Testing)
# WEBHOOK_SITE_URL=https://webhook.site/your-unique-id
```

---

## 🚀 **Quick Start**

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   python3 create_email_tables.py
   python3 create_mfa_tables.py
   ```

3. **Set Environment Variables**
   ```bash
   # Copy the .env file above and fill in your details
   cp .env.example .env
   nano .env
   ```

4. **Start the Application**
   ```bash
   python3 web_app_real.py
   ```

5. **Test Login**
   - Visit `http://localhost:5000`
   - Enter your email
   - Check your chosen method for verification code

---

## 🔄 **Fallback System**

The system automatically tries methods in this order:
1. Gmail SMTP
2. Outlook SMTP  
3. Telegram Bot
4. Discord Webhook
5. Webhook.site

If one fails, it automatically tries the next method.

---

## 📱 **Mobile Setup**

### **For Telegram:**
1. Install Telegram app
2. Message your bot
3. Codes will appear instantly

### **For Discord:**
1. Install Discord app
2. Join your server
3. Codes will appear in the webhook channel

### **For Email:**
1. Use any email app
2. Check inbox/spam folder
3. Codes arrive within seconds

---

## 🛠️ **Troubleshooting**

### **Gmail Issues:**
- Make sure 2FA is enabled
- Use App Password, not regular password
- Check if "Less secure apps" is disabled

### **Outlook Issues:**
- Enable SMTP authentication
- Check if account is locked
- Try app password instead

### **Telegram Issues:**
- Verify bot token is correct
- Make sure you messaged the bot first
- Check chat ID is correct

### **Discord Issues:**
- Verify webhook URL is correct
- Check if webhook is enabled
- Make sure bot has permissions

---

## 🎨 **Customization**

### **Email Templates:**
Edit `free_email_manager.py` to customize:
- Email subject
- Email content
- HTML formatting
- Branding

### **Telegram Messages:**
Customize the message format in the `_send_via_telegram` method.

### **Discord Embeds:**
Modify the embed structure in `_send_via_discord` method.

---

## 🔒 **Security Notes**

- **Never commit** your `.env` file to git
- **Use App Passwords** instead of main passwords
- **Rotate credentials** regularly
- **Monitor usage** for suspicious activity

---

## 📊 **Method Comparison**

| Method | Setup Time | Reliability | Delivery Speed | Mobile Friendly |
|--------|------------|-------------|----------------|-----------------|
| Gmail SMTP | 5 min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Outlook SMTP | 3 min | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Telegram | 2 min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Discord | 1 min | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Webhook.site | 30 sec | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎯 **Recommended Setup**

For **production use**:
1. **Primary:** Gmail SMTP
2. **Backup:** Telegram Bot
3. **Testing:** Webhook.site

For **development/testing**:
1. **Primary:** Webhook.site
2. **Backup:** Telegram Bot

---

## 🆘 **Need Help?**

If you encounter issues:
1. Check the logs in `logs/` directory
2. Verify environment variables are set
3. Test each method individually
4. Check network connectivity

The system will automatically fallback to working methods, so you don't need to worry about single points of failure!