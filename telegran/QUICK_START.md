# 🚀 QUICK START - Super Easy Setup!

## ⚡ 3-Step Setup (5 Minutes!)

### **Step 1: Install** (2 min)
```bash
cd telegran
./install.sh
```

### **Step 2: Configure** (2 min)
```bash
python3 setup_wizard.py
```
Answer a few simple questions - that's it!

### **Step 3: Run** (1 min)
```bash
python3 userbot.py
```
Enter the code from Telegram and you're DONE! 🎉

---

## 📋 What the Wizard Does

The setup wizard makes everything automatic:

✅ **Asks for your API credentials**
  - Guides you to get them
  - Saves to .env automatically

✅ **Helps you find your target group**
  - Shows you how to get group ID
  - Validates it works

✅ **Configures your messages**
  - Simple mode: One message for everyone
  - Stealth mode: Multiple variations
  - You choose!

✅ **Sets safe rate limits**
  - Recommends conservative defaults
  - Explains the risks
  - You decide

✅ **Creates perfect config**
  - Validates everything
  - No manual editing needed
  - Just works!

---

## 🎨 Simple Mode vs Stealth Mode

### **SIMPLE MODE** (Recommended for beginners)
```
Same message for everyone
Perfect for "copy/paste all day"
Consistent branding
Easy to understand
```

**Example:**
```
Every person gets: "Hey {username}! Welcome! 👋"
```

### **STEALTH MODE** (Advanced users)
```
Multiple message variations
Looks more human
Better anti-detection
Random selection
```

**Example:**
```
Person 1: "Hey {username}! Welcome! 👋"
Person 2: "Hi {username}! Great to have you! 😊"
Person 3: "Welcome {username}! 🎉"
```

---

## 🔧 After Setup

### **Check Status:**
```bash
python3 status.py
```

Shows you:
- ✅ Configuration
- ✅ Statistics (people welcomed)
- ✅ Rate limits
- ✅ Pending welcomes
- ✅ If bot is running

### **Test Setup:**
```bash
python3 test_bot.py
```

Verifies:
- ✅ API credentials work
- ✅ Can connect to Telegram
- ✅ You're in target group
- ✅ Config is valid
- ✅ Database initialized

### **Find Group ID:**
```bash
python3 get_group_id.py
```

Lists ALL your groups with:
- Name
- ID
- Username (if public)
- Type (Group/Channel)

---

## 📊 Monitoring

### **View Logs:**
```bash
tail -f telegran.log
```

### **Check Database:**
```bash
cat userbot_data.json | python3 -m json.tool
```

### **Stop Bot:**
```bash
# Press Ctrl+C in the terminal
# Or kill process:
pkill -f userbot.py
```

---

## ⚙️ Reconfiguring

Want to change something?

### **Option 1: Run wizard again**
```bash
python3 setup_wizard.py
```
It will ask if you want to reconfigure

### **Option 2: Edit manually**
```bash
nano config.json
# Make your changes
python3 userbot.py  # Restart bot
```

---

## 🎯 Common Scenarios

### **"I want one copy/paste message"**
```bash
python3 setup_wizard.py
# Choose: Simple Mode
# Enter your exact message
# Done!
```

### **"I want it to look human"**
```bash
python3 setup_wizard.py
# Choose: Stealth Mode
# Uses multiple variations
# Random delays
# Typing indicators
```

### **"I only want to welcome, not help"**
```bash
python3 setup_wizard.py
# Enable auto-welcome: Yes
# Enable auto-help: No
# Perfect!
```

### **"I want to test first"**
```bash
# After setup wizard:
python3 test_bot.py
# Verifies everything without sending messages
```

---

## 🆘 Troubleshooting

### **"Where do I get API_ID?"**
1. Go to https://my.telegram.org/apps
2. Log in with your phone
3. Create application
4. Copy API_ID and API_HASH

### **"How do I find my group?"**
```bash
python3 get_group_id.py
# Shows all your groups
# Copy the username or ID
```

### **"Is it working?"**
```bash
python3 status.py
# Shows if bot is running
# Shows stats
```

### **"Bot not responding?"**
1. Check: `python3 status.py`
2. Check: `tail -f telegran.log`
3. Verify you're in the target group
4. Run: `python3 test_bot.py`

---

## 🎉 You're Done!

That's it! The wizard makes setup super easy.

**Total time: 5 minutes**

**What you get:**
- ✅ Fully configured bot
- ✅ Database persistence
- ✅ Pending queue
- ✅ Anti-detection
- ✅ Rate limiting
- ✅ Easy monitoring

**Commands to remember:**
```bash
python3 setup_wizard.py  # Configure
python3 test_bot.py      # Test
python3 userbot.py       # Run
python3 status.py        # Monitor
```

---

## 💡 Pro Tips

1. **Start conservative**
   - Low rate limits (3-5/hour)
   - Test in small group first
   - Increase gradually

2. **Monitor daily**
   - Check `python3 status.py`
   - Watch logs for errors
   - Verify people getting welcomed

3. **Use simple mode first**
   - Easier to understand
   - Consistent messages
   - Switch to stealth later

4. **Mix manual usage**
   - Send real messages too
   - Don't only automate
   - Looks more human

---

**Ready? Start here:**
```bash
python3 setup_wizard.py
```

🎉 **Super easy!**
