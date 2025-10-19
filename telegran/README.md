# 🤖 Telegran - Telegram Auto-Welcome & Support Bot

An intelligent Telegram bot that automatically welcomes new members and responds to help requests in your Telegram groups.

## ✨ Features

- 👋 **Auto-Welcome**: Greets new members with customizable messages
- 💬 **Help Detection**: Automatically responds when users ask for help
- ⏰ **Smart Timing**: Configurable delays and cooldowns
- 🎨 **Rich Messages**: Support for buttons, formatting, and media
- 📊 **Analytics**: Track welcomes and help interactions
- 🛡️ **Rate Limiting**: Prevents spam and message flooding
- 🔧 **Easy Configuration**: JSON-based settings
- 📝 **Comprehensive Logging**: Track all bot activities

## 🚀 Quick Start

### 1. Get Your Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy your bot token

### 2. Install Dependencies

```bash
cd telegran
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and add your BOT_TOKEN
```

### 4. Run

```bash
python bot.py
```

### 5. Add to Your Group

1. Add your bot to the Telegram group
2. Make it an admin with these permissions:
   - Delete messages
   - Ban users
   - Invite users
   - Manage chat

## 📖 Documentation

- **[Vision & Roadmap](VISION_AND_ROADMAP.md)** - Complete feature list and development plan
- **[Quick Start Guide](QUICK_START_GUIDE.md)** - Detailed setup instructions
- **[config.json](config.json)** - Customize bot behavior

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "welcome_message": "Your custom welcome message with {username}",
  "help_message": "Your custom help response",
  "welcome_delay": 30,
  "cooldown_hours": 24,
  "help_keywords": ["help", "support", "question"],
  "enable_welcome_buttons": true
}
```

## 🎯 Commands

- `/start` - Start the bot and show info
- `/stats` - View bot statistics
- `/config` - View current configuration
- `/test_welcome` - Test welcome message
- `/test_help` - Test help message

## 📊 How It Works

1. **New Member Detection**: Bot listens for new member join events
2. **Delayed Welcome**: Waits configured seconds before welcoming
3. **Help Detection**: Monitors messages for help keywords
4. **Smart Responses**: Sends appropriate messages with cooldowns
5. **Rate Limiting**: Prevents spam with configurable cooldowns

## 🛠️ Advanced Setup

### Run 24/7 with systemd (Linux)

```bash
sudo nano /etc/systemd/system/telegran.service
```

Add:
```ini
[Unit]
Description=Telegran Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/telegran
Environment="PATH=/path/to/telegran/venv/bin"
ExecStart=/path/to/telegran/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable telegran
sudo systemctl start telegran
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

## 📈 Monitoring

View logs in real-time:
```bash
tail -f telegran.log
```

Check bot status:
```bash
systemctl status telegran  # If using systemd
ps aux | grep bot.py       # Check if running
```

## 🔒 Security Best Practices

- ✅ Never commit `.env` file (it's in `.gitignore`)
- ✅ Use environment variables for sensitive data
- ✅ Keep bot token secret
- ✅ Regularly update dependencies
- ✅ Monitor bot logs for suspicious activity

## 🐛 Troubleshooting

**Bot not responding?**
- Check bot is admin in group
- Verify bot token is correct
- Check logs: `tail -f telegran.log`

**Welcome messages not sending?**
- Verify `welcome_delay` in config
- Check bot has message permissions
- Test with `/test_welcome` command

**Help detection not working?**
- Review `help_keywords` in config.json
- Test with `/test_help` command
- Check cooldown period hasn't blocked user

## 📝 Development Roadmap

See [VISION_AND_ROADMAP.md](VISION_AND_ROADMAP.md) for:
- Planned features
- Enhancement ideas
- Advanced AI capabilities
- Multi-group support

## 🤝 Contributing

Ideas for improvements:
- Add database persistence
- Implement analytics dashboard
- Add more detection patterns
- Multi-language support
- AI-powered responses

## 📄 License

This project is open source and available for personal and commercial use.

## 💡 Support

- Check documentation in this folder
- Review logs for errors
- Test in a small group first
- Start simple, add features gradually

## 🎉 Success Metrics

Track these KPIs:
- New member engagement rate
- Help request response time
- User retention after welcome
- Message delivery success rate

---

**Built for the Cupidbot community with ❤️**

Start with the basics, monitor performance, and gradually add more features based on your needs!
