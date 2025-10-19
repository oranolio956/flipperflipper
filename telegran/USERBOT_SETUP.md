# 🕵️ Telegran Userbot Setup Guide

## ⚠️ IMPORTANT - READ THIS FIRST!

This is a **USERBOT** - it uses YOUR personal Telegram account to send messages automatically.

### Risks & Warnings:
- ⚠️ **Against Telegram ToS** - Automation with user accounts is not officially allowed
- ⚠️ **Account ban risk** - Telegram may suspend your account if detected
- ⚠️ **Use at your own risk** - No guarantees of safety
- ✅ **Stealth features included** - Advanced anti-detection built-in

### Why Use This?
- ✅ Messages look like YOU sent them (not a bot)
- ✅ No "BOT" badge
- ✅ Works in groups without admin access
- ✅ More natural appearance

---

## 🚀 Quick Setup (15 Minutes)

### Step 1: Get Telegram API Credentials (5 min)

1. **Go to https://my.telegram.org/apps**
2. **Log in** with your phone number
3. **Create new application:**
   - App title: `Telegran Userbot`
   - Short name: `telegran`
   - Platform: `Desktop`
   - Description: `Personal automation tool`
4. **Copy these values:**
   - `API_ID` - A number (e.g., 12345678)
   - `API_HASH` - A long string (e.g., abcdef1234567890...)

⚠️ **KEEP THESE SECRET!** Never share API credentials!

---

### Step 2: Install Dependencies (3 min)

```bash
cd telegran

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

---

### Step 3: Configure (2 min)

```bash
# Copy example config
cp .env.example .env

# Edit .env file
nano .env
```

Add your credentials:
```bash
API_ID=12345678
API_HASH=your_hash_from_telegram_org
PHONE_NUMBER=+1234567890
```

**Phone format:** Include country code (e.g., +1 for USA, +44 for UK)

---

### Step 4: First Login (5 min)

```bash
# Run the userbot
python userbot.py
```

**You'll be prompted:**
1. Enter your phone number (if not in .env)
2. Enter the code sent to your Telegram
3. If 2FA enabled, enter your password

**This only happens once!** Session is saved for future runs.

---

### Step 5: Join Target Group

The userbot will monitor any groups YOU are in. To target Cupidbot:

1. Join https://t.me/cupidbotg (if not already)
2. Edit `config.json` and set:
   ```json
   "target_group": "cupidbotg"
   ```
3. Restart the userbot

---

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "welcome_messages": [
    "Hey {username}! Welcome! 👋",
    "Hi {username}! Great to have you here! 😊"
  ],
  "help_messages": [
    "Hey {username}! What do you need help with?",
    "Hi {username}! I can help - what's up?"
  ],
  "stealth": {
    "welcome_delay_min": 45,
    "welcome_delay_max": 180,
    "max_messages_per_hour": 8,
    "response_probability": 0.85
  }
}
```

---

## 🕵️ Stealth Features (Anti-Detection)

Built-in features to avoid Telegram detection:

### 1. **Random Delays**
- Welcome: 45-180 seconds (varies each time)
- Help responses: 10-60 seconds
- Makes timing unpredictable

### 2. **Typing Indicators**
- Shows "typing..." before sending (2-5 seconds)
- Simulates human behavior
- Telegram sees you as actively typing

### 3. **Rate Limiting**
- Max 8 messages per hour
- Max 50 messages per day
- Prevents spam flags

### 4. **Response Probability**
- Only responds to 85% of triggers
- Sometimes "misses" messages (like a human)
- More natural pattern

### 5. **Time-Based Activity**
- More active 8 AM - 11 PM
- Reduced activity at night (30% response rate)
- Mimics human sleep patterns

### 6. **Message Variations**
- Multiple message templates
- Random selection each time
- Never sends exact same message repeatedly

### 7. **Cooldown Periods**
- Won't message same user for 24 hours
- Prevents harassment appearance
- Respects user space

### 8. **Human Patterns**
- Sometimes waits longer
- Sometimes responds faster
- Unpredictable = harder to detect

---

## 🛡️ Additional Safety Tips

### 1. **Start Slow**
```json
"stealth": {
  "max_messages_per_hour": 3,  // Very conservative
  "response_probability": 0.5  // Only 50% of triggers
}
```

### 2. **Monitor First Week**
- Watch for any warnings from Telegram
- Check if account functionality changes
- Be ready to stop if issues arise

### 3. **Don't Overuse**
- Not 24/7 for first few weeks
- Run during your normal active hours only
- Gradually increase usage

### 4. **Mix with Real Usage**
- Use your account normally too
- Send manual messages
- Don't ONLY use automation

### 5. **Multiple Accounts (Advanced)**
- Consider using secondary account
- Not your main personal account
- Less risk if banned

### 6. **Backup Session**
```bash
# Backup your session file
cp userbot_session.session userbot_session.backup
```

---

## 🚦 Running the Userbot

### Development (Manual):
```bash
cd telegran
source venv/bin/activate
python userbot.py
```

### Background (Screen):
```bash
screen -S telegran
cd telegran
source venv/bin/activate
python userbot.py
# Press Ctrl+A then D to detach
```

### 24/7 (systemd):
```bash
# Copy service file
sudo cp telegran.service.template /etc/systemd/system/telegran.service

# Edit paths and change:
# ExecStart to point to userbot.py instead of bot.py

sudo systemctl enable telegran
sudo systemctl start telegran
```

---

## 📊 Monitoring

### View Logs:
```bash
tail -f telegran.log
```

### Check Stats:
- Stats automatically logged every 30 minutes
- Shows: welcomes sent, help responses, message rate

### What to Watch For:
- ✅ "Showing typing..." - Working correctly
- ✅ "Human-like delay" - Stealth active
- ✅ "Skipping response" - Random probability working
- ⚠️ Too many messages per hour - Reduce limits
- ⚠️ Any Telegram errors - Stop and investigate

---

## 🔧 Troubleshooting

### "API_ID not found"
- Check .env file exists
- Verify API_ID is a number (no quotes)
- Make sure .env is in telegran folder

### "Phone number invalid"
- Include country code (e.g., +1234567890)
- No spaces or dashes
- Use international format

### "Session expired"
- Delete `userbot_session.session`
- Run `python userbot.py` again
- Re-authenticate with code

### "Not responding to messages"
- Check you're in the target group
- Verify group name in config.json
- Check logs for errors

### "Sending too many messages"
- Reduce `max_messages_per_hour`
- Increase delay values
- Lower `response_probability`

---

## 🎯 Best Practices

### DO:
✅ Start with conservative settings
✅ Monitor logs regularly
✅ Use varied message templates
✅ Let it run during your normal active hours
✅ Mix with manual usage
✅ Backup session files
✅ Test in small groups first

### DON'T:
❌ Run 24/7 from day one
❌ Send too many messages per hour
❌ Use only automation (mix with real use)
❌ Share API credentials
❌ Use on your only Telegram account (if possible)
❌ Ignore Telegram warnings/errors

---

## 📈 Optimization Tips

### Week 1: Conservative
```json
"max_messages_per_hour": 3,
"response_probability": 0.5,
"welcome_delay_max": 300  // 5 minutes
```

### Week 2-3: Moderate (if no issues)
```json
"max_messages_per_hour": 5,
"response_probability": 0.7,
"welcome_delay_max": 180  // 3 minutes
```

### Week 4+: Full (if stable)
```json
"max_messages_per_hour": 8,
"response_probability": 0.85,
"welcome_delay_max": 180
```

---

## 🆘 If Account Gets Restricted

1. **Stop userbot immediately**
   ```bash
   # Kill the process
   pkill -f userbot.py
   ```

2. **Check Telegram app for warnings**

3. **Wait 24-48 hours** before restarting

4. **Reduce settings** even further:
   ```json
   "max_messages_per_hour": 2,
   "response_probability": 0.3
   ```

5. **Consider using different account**

---

## 🔐 Security Checklist

- [ ] API credentials stored in .env (not in code)
- [ ] .env file in .gitignore
- [ ] Session file backed up
- [ ] Two-factor authentication enabled on Telegram
- [ ] Strong password on account
- [ ] Monitoring logs regularly
- [ ] Conservative rate limits set
- [ ] Testing in small group first

---

## 📞 Quick Reference

### Start userbot:
```bash
cd telegran && source venv/bin/activate && python userbot.py
```

### View logs:
```bash
tail -f telegran.log
```

### Stop userbot:
```bash
Ctrl + C  # If running in terminal
screen -r telegran  # Then Ctrl + C
```

### Update config:
```bash
nano config.json  # Edit settings
# No need to stop/start - auto-reloads
```

---

## ✅ Ready to Run!

Your stealth userbot includes:
- ✅ Random delays (45-180s for welcomes)
- ✅ Typing indicators (2-5s)
- ✅ Rate limiting (8/hour max)
- ✅ Time-based activity patterns
- ✅ Response probability (85%)
- ✅ Message variations
- ✅ Cooldown periods (24h)
- ✅ Human-like unpredictability

**Use responsibly and monitor closely! 🕵️**

---

*Remember: This is automation of a personal account. Telegram does not officially support this. Use at your own risk.*
