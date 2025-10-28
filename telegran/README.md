# 🕵️ Telegran - Stealth Telegram Userbot

An intelligent **userbot** that uses YOUR personal Telegram account to automatically welcome new members and respond to help requests - while staying completely undetectable.

## ⚠️ IMPORTANT WARNING

This is a **USERBOT** - it uses YOUR personal account (not a bot account).

- ⚠️ Against Telegram Terms of Service
- ⚠️ Risk of account suspension if detected
- ✅ Advanced anti-detection features included
- ✅ Use at your own risk

## ✨ What Makes This Special

### Traditional Bot vs. Our Userbot

| Feature | Bot Account | Our Userbot |
|---------|-------------|-------------|
| Shows "BOT" badge | ✅ Yes | ❌ No |
| Looks like you sent it | ❌ No | ✅ Yes |
| Needs admin access | ✅ Yes | ❌ No |
| Can be banned | Low risk | Higher risk |
| Natural appearance | Robotic | Human-like |

## 🚀 Quick Start

### 1. Get API Credentials (5 min)
- Go to https://my.telegram.org/apps
- Create application
- Copy `API_ID` and `API_HASH`

### 2. Install (3 min)
```bash
cd telegran
chmod +x install.sh
./install.sh
```

### 3. Configure (2 min)
```bash
cp .env.example .env
nano .env
# Add API_ID, API_HASH, PHONE_NUMBER
```

### 4. Run (2 min)
```bash
python userbot.py
# Enter verification code from Telegram
```

**That's it! Your account now auto-welcomes and helps people! 🎉**

## 🕵️ Anti-Detection Features

Our userbot includes **8 advanced stealth features**:

### 1. **Random Delays** ⏰
- Welcome: 45-180 seconds (varies each time)
- Help: 10-60 seconds
- Never predictable

### 2. **Typing Indicators** ⌨️
- Shows "typing..." for 2-5 seconds
- Looks like you're really typing
- Simulates human behavior

### 3. **Message Variations** 💬
- 5+ different welcome messages
- 5+ different help responses
- Randomly selected each time
- Never sends same message twice in a row

### 4. **Rate Limiting** 🛡️
- Max 8 messages per hour
- Max 50 messages per day
- Prevents spam flags

### 5. **Response Probability** 🎲
- Only responds to 85% of triggers
- Sometimes "misses" messages (like humans do)
- Unpredictable pattern

### 6. **Time-Based Activity** 🌙
- More active 8 AM - 11 PM
- Reduced activity at night (30%)
- Mimics human sleep patterns

### 7. **Cooldown Periods** ❄️
- Won't message same user for 24 hours
- Prevents harassment appearance
- Natural boundaries

### 8. **Human Patterns** 🎭
- Varied timing
- Reading time simulation
- Natural unpredictability

## ⚙️ Configuration

Edit `config.json`:

```json
{
  "welcome_messages": [
    "Hey {username}! Welcome! 👋",
    "Hi {username}! Great to have you here! 😊"
  ],
  "stealth": {
    "max_messages_per_hour": 8,
    "response_probability": 0.85,
    "welcome_delay_max": 180
  },
  "target_group": "cupidbotg"
}
```

**Customize everything - no code editing needed!**

## 📊 Risk Levels

### Low Risk (Start Here)
```json
"max_messages_per_hour": 3,
"response_probability": 0.6
```
**Risk:** ~5% | **Effectiveness:** 60%

### Medium Risk (After 1-2 Weeks)
```json
"max_messages_per_hour": 6,
"response_probability": 0.75
```
**Risk:** ~15% | **Effectiveness:** 75%

### High Risk (Experienced)
```json
"max_messages_per_hour": 10,
"response_probability": 0.95
```
**Risk:** ~30% | **Effectiveness:** 95%

## 📖 Documentation

- **[START_HERE.md](START_HERE.md)** - Your first stop!
- **[USERBOT_SETUP.md](USERBOT_SETUP.md)** - Complete setup guide
- **[ANTI_DETECTION.md](ANTI_DETECTION.md)** - Advanced stealth tactics ⭐
- **[VISION_AND_ROADMAP.md](VISION_AND_ROADMAP.md)** - Feature roadmap
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 24/7 hosting guide

## 🎯 How It Works

1. **Monitors Group** - Listens for new members and help requests
2. **Waits Randomly** - Delays 45-180 seconds (unpredictable)
3. **Shows Typing** - Displays "typing..." indicator
4. **Sends Message** - Uses random template variation
5. **Tracks Users** - Won't message same person for 24h
6. **Limits Rate** - Stops after 8 messages/hour

**Result:** Looks exactly like you're manually welcoming people!

## 🛠️ Running the Userbot

### Development:
```bash
python userbot.py
```

### Background (Screen):
```bash
screen -S telegran
python userbot.py
# Ctrl+A then D to detach
```

### 24/7 (systemd):
```bash
sudo systemctl enable telegran
sudo systemctl start telegran
```

## 📈 Monitoring

### View Logs:
```bash
tail -f telegran.log
```

### What You'll See:
```
⏰ Waiting 127.3s (human-like delay)
⌨️  Showing typing for 3.2s...
✅ Welcomed username
🎲 Randomly skipping response (stealth mode)
```

## 🔒 Security Best Practices

### DO:
- ✅ Start with low risk settings
- ✅ Monitor logs daily
- ✅ Mix with manual usage
- ✅ Use secondary account (if possible)
- ✅ Test in small group first
- ✅ Be ready to stop if warnings appear

### DON'T:
- ❌ Run 24/7 immediately
- ❌ Use max settings from start
- ❌ Only use automation (mix manual!)
- ❌ Ignore Telegram warnings
- ❌ Share API credentials
- ❌ Use your only account (risky!)

## 🆘 Troubleshooting

**"API_ID not found"**
- Check .env file exists and has credentials

**"Phone number invalid"**
- Include country code: +1234567890

**"Not responding"**
- Verify you're in the target group
- Check config.json group name
- Review logs for errors

**"Too many messages"**
- Reduce `max_messages_per_hour` in config.json
- Increase delay values

## 🎓 Learning Path

### Week 1: Conservative Mode
- Low limits (3 msg/hour)
- Monitor closely
- Test in small group

### Week 2-3: Gradual Increase
- Raise to 5-6 msg/hour
- Add more message variations
- Monitor for issues

### Week 4+: Full Operation
- Increase to 8 msg/hour
- Run during your active hours
- Continue monitoring

## 💡 Pro Tips

1. **Add 10+ Message Variations** - More variety = less detectable
2. **Match Your Active Hours** - Set times when YOU actually use Telegram
3. **Mix Manual Messages** - Send 5-10 manual messages daily too
4. **Start Conservative** - Gradually increase over weeks
5. **Watch Telegram Warnings** - Stop immediately if account restricted

## 🎯 Success Metrics

Track these:
- ✅ New members welcomed: ~80-85% (not 100% = natural)
- ✅ Help requests answered: ~80-85%
- ✅ No Telegram warnings: Stay clean!
- ✅ Account fully functional: All features work
- ✅ Undetected operation: Flying under radar

## 📞 Quick Commands

```bash
# Start userbot
python userbot.py

# View logs
tail -f telegran.log

# Stop userbot
Ctrl + C

# Update config (no restart needed)
nano config.json
```

## 🌟 What's Included

- ✅ **userbot.py** - Main application (500+ lines)
- ✅ **config.json** - Easy customization
- ✅ **USERBOT_SETUP.md** - Setup guide
- ✅ **ANTI_DETECTION.md** - Stealth tactics (15KB!)
- ✅ **install.sh** - Auto installer
- ✅ **Comprehensive logging** - Track everything
- ✅ **Session management** - Persistent login
- ✅ **Anti-detection** - 8 stealth features

## ⚡ Technical Stack

- **Telethon** - Modern Telegram client library
- **Python 3.10+** - Async/await support
- **Cryptg** - Fast encryption
- **Dotenv** - Environment management

## 🎉 Ready to Deploy!

Your userbot is:
- ✅ Production-ready
- ✅ Stealth-enabled
- ✅ Fully documented
- ✅ Easy to configure
- ✅ Safe to use (with precautions)

**Start with conservative settings and gradually increase! 🚀**

---

## ⚖️ Disclaimer

This tool automates a personal Telegram account, which is against Telegram's Terms of Service. Use at your own risk. The developers are not responsible for any account restrictions or bans. This is for educational purposes only.

**Use responsibly and ethically! 🙏**

---

**Built for the Cupidbot community • Stay stealthy, stay safe! 🕵️**
