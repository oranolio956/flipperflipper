# Telegram Channel Automation Program

A comprehensive Python-based automation tool for interacting with Telegram channels, sending messages to members, and finding resources.

## 📋 What This Tool Does

✅ **Channel Access**: Connect to and interact with Telegram channels  
✅ **Member Retrieval**: Get lists of channel members (with proper permissions)  
✅ **Bulk Messaging**: Send personalized messages to multiple users  
✅ **Resource Finding**: Search channel history for specific keywords  
✅ **Active User Detection**: Find users who have recently participated  
✅ **Real-time Monitoring**: Monitor channels for new messages with keywords  
✅ **Data Export**: Save results to JSON files for further analysis  

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r telegram_requirements.txt
```

### 2. Get API Credentials
Visit https://my.telegram.org/apps and create an application to get:
- API ID
- API Hash

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Run the Example
```bash
python telegram_automation_example.py
```

## 📚 Documentation

### Main Files

| File | Description |
|------|-------------|
| `TELEGRAM_AUTOMATION_GUIDE.md` | **Comprehensive guide** with theory, examples, and best practices |
| `SETUP_INSTRUCTIONS.md` | **Step-by-step setup** instructions and troubleshooting |
| `telegram_automation_example.py` | **Working implementation** with multiple examples |
| `telegram_requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

### Read These Documents:

1. **Start Here**: `SETUP_INSTRUCTIONS.md` - Get up and running quickly
2. **Learn More**: `TELEGRAM_AUTOMATION_GUIDE.md` - Comprehensive guide with all details
3. **Code Reference**: `telegram_automation_example.py` - Working code examples

## 🎯 Key Features Explained

### 1. Search for Resources
Find messages in channel history containing specific keywords:
```python
resources = await bot.search_messages(
    channel, 
    keywords=['available', 'free', 'open'],
    limit=100
)
```

### 2. Send Bulk Messages
Send personalized messages to multiple users:
```python
message = "Hi {first_name}, [your message]"
await bot.send_bulk_messages(users, message, delay=10)
```

### 3. Find Active Users
Identify users who have recently participated:
```python
active_users = await bot.find_active_users(channel, days=7)
```

### 4. Real-time Monitoring
Monitor channel for specific keywords in real-time:
```python
await bot.monitor_channel('@channel', keywords, duration=3600)
```

## ⚠️ Important Warnings

### Legal & Ethical Considerations

1. **Terms of Service**: This tool can violate Telegram's ToS if misused
2. **Spam Prevention**: Never send unsolicited messages
3. **Rate Limits**: Always respect rate limits to avoid bans
4. **Privacy**: Follow GDPR and data protection laws
5. **Consent**: Only message users who have agreed to receive messages

### Rate Limiting

- **Minimum delay**: 5-10 seconds between messages
- **Recommended**: 10-15 seconds for safety
- **Handle errors**: Always catch `FloodWaitError`
- **Consequences**: Account ban if you exceed limits

### Security

```bash
# NEVER commit these files:
.env                    # Contains credentials
*.session              # Contains auth tokens
*.session-journal      # Session metadata
```

## 🛠️ Use Cases

### ✅ Legitimate Uses
- Automating your own community management
- Sending updates to opted-in members
- Research and data analysis (with consent)
- Personal message organization
- Monitoring for important keywords

### ❌ Prohibited Uses
- Sending spam or unsolicited messages
- Harvesting user data without consent
- Automated harassment
- Violating privacy laws
- Breaking Telegram ToS

## 📊 Example Workflow

```python
# 1. Connect to Telegram
bot = TelegramChannelBot(API_ID, API_HASH, PHONE)
await bot.connect()

# 2. Access channel
channel = await bot.get_channel('@mychannel')

# 3. Search for resources
resources = await bot.search_messages(
    channel, 
    keywords=['job', 'hiring', 'available']
)

# 4. Find active users
active_users = await bot.find_active_users(channel, days=7)

# 5. Send messages (with consent!)
message = "Hi {first_name}, we found a job for you!"
await bot.send_bulk_messages(
    active_users,
    message,
    delay=15,
    dry_run=True  # Test first!
)

# 6. Save data
bot.save_to_json(resources, 'resources.json')

# 7. Disconnect
await bot.disconnect()
```

## 🔧 Customization

### Modify Keywords
Edit the `KEYWORDS` list in `telegram_automation_example.py`:
```python
KEYWORDS = ['urgent', 'important', 'breaking', 'announcement']
```

### Change Message Template
```python
message_template = """
Hello {first_name},

This is your custom message here.
You can use {username} and other variables.

Best regards
"""
```

### Adjust Timing
```python
MESSAGE_DELAY = 15  # seconds between messages
MAX_USERS = 50      # maximum users to process
SEARCH_LIMIT = 200  # messages to search through
```

## 📈 Scaling Considerations

### For Large Operations

1. **Use Multiple Accounts**: Distribute load across accounts
2. **Database Storage**: Store data in SQLite or PostgreSQL
3. **Queue System**: Implement message queue for reliability
4. **Monitoring**: Add logging and error tracking
5. **Scheduling**: Use cron or schedule library for automation

### Performance Tips

- Process users in batches
- Implement exponential backoff for errors
- Cache channel/user entities
- Use async operations for parallelization
- Monitor memory usage for large datasets

## 🐛 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "Invalid API credentials" | Check API_ID and API_HASH in .env |
| "Phone number invalid" | Use international format: +1234567890 |
| "FloodWaitError" | Increase delays between messages |
| "Cannot get entity" | Ensure you're a member of the channel |
| "ChatAdminRequiredError" | Some operations need admin rights |

See `SETUP_INSTRUCTIONS.md` for detailed troubleshooting.

## 📦 Dependencies

- **telethon**: Main Telegram client library
- **python-dotenv**: Environment variable management
- **aiohttp**: Async HTTP requests
- **schedule**: Task scheduling (optional)

## 🔐 Security Checklist

- [ ] API credentials stored in .env (not in code)
- [ ] .env and *.session in .gitignore
- [ ] Session files kept secure
- [ ] Rate limiting implemented
- [ ] Error handling in place
- [ ] Dry-run mode tested
- [ ] Compliance with ToS verified

## 📖 Additional Resources

### Documentation
- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram API](https://core.telegram.org/api)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Getting API Credentials
- [My Telegram Apps](https://my.telegram.org/apps)

### Community
- [Telethon Chat](https://t.me/TelethonChat)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/telethon)

## 🎓 Learning Path

1. **Beginner**: Read SETUP_INSTRUCTIONS.md and run the example
2. **Intermediate**: Read TELEGRAM_AUTOMATION_GUIDE.md for theory
3. **Advanced**: Customize the code and add features
4. **Expert**: Integrate with databases, APIs, and other systems

## 📝 License & Disclaimer

This tool is provided for educational purposes. Users are solely responsible for:
- Compliance with all applicable laws
- Adherence to Telegram's Terms of Service
- Ethical use of the tool
- Obtaining necessary consents
- Protecting user privacy

The creators assume no liability for misuse.

---

## 🚀 Getting Started Now

1. **Read**: `SETUP_INSTRUCTIONS.md`
2. **Configure**: Set up your `.env` file
3. **Run**: `python telegram_automation_example.py`
4. **Customize**: Modify for your use case
5. **Test**: Always use dry_run=True first!

---

**Questions?** Check the comprehensive guide in `TELEGRAM_AUTOMATION_GUIDE.md`

**Need help?** Review the troubleshooting section in `SETUP_INSTRUCTIONS.md`

**Ready to code?** Study `telegram_automation_example.py` for working examples

---

*Built with ❤️ for automation enthusiasts*

*Remember: With great power comes great responsibility. Use ethically!* 🤝
