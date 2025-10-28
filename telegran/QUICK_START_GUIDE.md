# Quick Start Guide - Telegran Bot

## 🎯 Get Your Bot Running in 30 Minutes

This guide will help you deploy a basic version of the Telegran bot quickly.

---

## Prerequisites

1. **Python 3.10+** installed
2. **Telegram Account** 
3. **Admin access** to Cupidbot group or test group
4. **Basic command line** knowledge

---

## Step 1: Get Bot Token (5 minutes)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "Cupidbot Greeter")
4. Choose a username (e.g., "cupidbot_greeter_bot")
5. **Copy the bot token** - you'll need this!

```
Example token: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## Step 2: Add Bot to Your Group (2 minutes)

1. Go to your Telegram group (Cupidbot)
2. Click group name → Administrators → Add Administrator
3. Search for your bot username
4. Give it these permissions:
   - ✅ Delete messages
   - ✅ Ban users
   - ✅ Invite users via link
   - ✅ Manage chat

---

## Step 3: Set Up Project (5 minutes)

```bash
# Navigate to telegran folder
cd telegran

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install python-telegram-bot python-dotenv aiosqlite
```

---

## Step 4: Configuration (3 minutes)

Create a `.env` file in the `telegran` folder:

```bash
# telegran/.env
BOT_TOKEN=your_bot_token_here
GROUP_ID=  # Leave empty for now, bot will detect it
ADMIN_ID=your_telegram_user_id  # Optional
```

To get your user ID:
- Message @userinfobot on Telegram
- It will reply with your user ID

---

## Step 5: Run the Bot (2 minutes)

```bash
# Make sure you're in telegran folder and venv is activated
cd telegran
python bot.py
```

You should see:
```
✅ Bot started successfully!
🤖 Bot username: @your_bot_username
📡 Listening for new members...
```

---

## Step 6: Test It! (5 minutes)

### Test New Member Welcome:
1. Invite a friend (or use another account)
2. Have them join the group
3. Bot should welcome them after 30 seconds

### Test Help Detection:
1. Send a message with "help" in your group
2. Bot should respond with help info

---

## 🎨 Customize Messages

Edit `config.json` in the `telegran` folder:

```json
{
  "welcome_message": "👋 Welcome {username} to Cupidbot! We're here to help you connect and find love! ❤️",
  "help_message": "💬 Hi {username}! Need help? Check out:\n\n📚 Guide: t.me/cupidbot/guide\n💬 Support: @admin",
  "welcome_delay": 30,
  "cooldown_hours": 24
}
```

---

## 🔄 Keep Bot Running 24/7

### Option 1: Using `screen` (Linux)
```bash
screen -S telegran
cd /path/to/telegran
source venv/bin/activate
python bot.py

# Press Ctrl+A then D to detach
# To reattach: screen -r telegran
```

### Option 2: Using `systemd` service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/telegran.service

# Add this content:
[Unit]
Description=Telegran Welcome Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/telegran
Environment="PATH=/path/to/telegran/venv/bin"
ExecStart=/path/to/telegran/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable telegran
sudo systemctl start telegran

# Check status
sudo systemctl status telegran
```

### Option 3: Cloud Server (Recommended)
Deploy to:
- **DigitalOcean** ($5/month droplet)
- **AWS EC2** (Free tier available)
- **Google Cloud** (Free tier available)
- **Heroku** (Free tier with limitations)

---

## 📊 Monitor Your Bot

### Check logs:
```bash
# View last 50 lines
tail -n 50 telegran.log

# Live monitoring
tail -f telegran.log
```

### Check if bot is running:
```bash
ps aux | grep bot.py
```

### Restart bot:
```bash
# If using systemd
sudo systemctl restart telegran

# If using screen
screen -r telegran  # Then Ctrl+C and restart
```

---

## 🐛 Common Issues

### Issue: "Unauthorized" error
**Solution**: Check your bot token in `.env` file

### Issue: Bot doesn't respond
**Solution**: 
1. Make sure bot is admin in group
2. Check bot has proper permissions
3. Verify bot is running: `ps aux | grep bot.py`

### Issue: Bot crashes frequently  
**Solution**: Check logs for errors: `tail -n 100 telegran.log`

### Issue: Messages not sending
**Solution**: 
1. Check Telegram API rate limits
2. Verify group privacy settings
3. Ensure bot isn't restricted

---

## 🎓 Next Steps

Once basic bot is running:

1. ✅ Monitor performance for 24 hours
2. ✅ Adjust message templates based on feedback
3. ✅ Add more detection keywords
4. ✅ Implement analytics tracking
5. ✅ Add admin controls
6. ✅ Scale to multiple groups

---

## 📞 Need Help?

- Check the full [VISION_AND_ROADMAP.md](./VISION_AND_ROADMAP.md)
- Review bot logs for errors
- Test in a small test group first
- Start simple, add features gradually

---

## ⚡ Quick Commands Reference

```bash
# Start bot
python bot.py

# Stop bot
Ctrl + C

# View logs
tail -f telegran.log

# Test bot is responding
curl https://api.telegram.org/bot<TOKEN>/getMe

# Check bot updates
curl https://api.telegram.org/bot<TOKEN>/getUpdates
```

---

**🎉 Congratulations! Your bot should now be welcoming new members and helping users automatically!**
