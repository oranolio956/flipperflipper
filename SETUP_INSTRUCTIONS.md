# Telegram Automation Setup Instructions

## Quick Start Guide

### Step 1: Install Python
Make sure you have Python 3.7 or higher installed:
```bash
python --version
```

### Step 2: Install Dependencies
```bash
pip install -r telegram_requirements.txt
```

### Step 3: Get Telegram API Credentials

1. **Visit Telegram's API Development Tools**
   - Go to: https://my.telegram.org/apps
   - Log in with your phone number
   - You'll receive a verification code via Telegram

2. **Create an Application**
   - Click on "API Development Tools"
   - Fill in the application details:
     - App title: (e.g., "My Automation Bot")
     - Short name: (e.g., "mybot")
     - Platform: Other
     - Description: (optional)
   - Click "Create application"

3. **Save Your Credentials**
   - You'll receive:
     - **api_id**: A number (e.g., 12345678)
     - **api_hash**: A string (e.g., "0123456789abcdef0123456789abcdef")
   - **IMPORTANT**: Keep these secret!

### Step 4: Configure Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your credentials:**
   ```
   TELEGRAM_API_ID=12345678
   TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef
   TELEGRAM_PHONE=+1234567890
   ```

3. **Set your target channel:**
   ```
   DEFAULT_CHANNEL=@channelname
   ```

### Step 5: Run the Example Script

```bash
python telegram_automation_example.py
```

**First time running:**
- You'll be asked to enter the verification code sent to your Telegram
- If you have 2FA enabled, you'll need to enter your password
- A session file will be created (don't share this file!)

### Step 6: Customize for Your Needs

Edit the `telegram_automation_example.py` file:
- Change `CHANNEL_USERNAME` to your target channel
- Modify `KEYWORDS` to search for specific terms
- Adjust message templates
- Enable/disable different examples

---

## Security Best Practices

### 1. Protect Your Credentials
```bash
# Never commit these files:
echo ".env" >> .gitignore
echo "*.session" >> .gitignore
echo "*.session-journal" >> .gitignore
```

### 2. Session Files
- Session files contain authentication tokens
- Treat them like passwords
- Don't share or upload them
- Store them securely

### 3. Rate Limiting
- Always include delays between messages (minimum 5-10 seconds)
- Respect Telegram's rate limits
- Handle `FloodWaitError` properly

### 4. Legal Compliance
- Only message people who've consented
- Respect privacy laws (GDPR, etc.)
- Follow Telegram's Terms of Service
- Don't spam or send unsolicited messages

---

## Common Issues and Solutions

### Issue 1: "API ID or Hash is invalid"
**Solution:**
- Double-check your API ID and Hash
- Make sure there are no extra spaces
- Verify you're using the correct credentials from my.telegram.org

### Issue 2: "Phone number is invalid"
**Solution:**
- Include country code (e.g., +1234567890)
- No spaces or special characters except +
- Use international format

### Issue 3: "Cannot get entity"
**Solution:**
- Make sure you're a member of the channel
- For private channels, you need an invitation
- Check if the channel username is correct (include @)

### Issue 4: "FloodWaitError"
**Solution:**
- You're sending too many requests
- Increase delays between messages
- Wait for the specified time in the error
- Use the error handling in the example script

### Issue 5: "ChatAdminRequiredError"
**Solution:**
- Some operations require admin rights
- Request admin access from channel owner
- Or use alternative methods that don't require admin rights

### Issue 6: "Session file not found"
**Solution:**
- This is normal on first run
- The script will create a session file after authentication
- Don't delete session files unnecessarily

---

## Usage Examples

### Example 1: Search for Resources
```python
resources = await bot.search_messages(
    channel, 
    keywords=['job', 'hiring', 'available'],
    limit=100
)
bot.save_to_json(resources, 'jobs.json')
```

### Example 2: Find Active Users
```python
active_users = await bot.find_active_users(
    channel, 
    days=7,  # Last 7 days
    limit=500
)
```

### Example 3: Send Personalized Messages
```python
message = """
Hi {first_name},

I noticed you're active in our channel.
[Your message here]

Best regards
"""

await bot.send_bulk_messages(
    users,
    message,
    delay=15,  # 15 seconds between messages
    dry_run=False  # Set to False to actually send
)
```

### Example 4: Real-time Monitoring
```python
await bot.monitor_channel(
    '@mychannel',
    keywords=['urgent', 'important', 'breaking'],
    duration=3600  # Monitor for 1 hour
)
```

---

## Advanced Configuration

### Using Multiple Accounts
```python
# Account 1
bot1 = TelegramChannelBot(API_ID_1, API_HASH_1, PHONE_1, 'session1')

# Account 2
bot2 = TelegramChannelBot(API_ID_2, API_HASH_2, PHONE_2, 'session2')

# Distribute work between accounts
await bot1.send_bulk_messages(users[:50], message)
await bot2.send_bulk_messages(users[50:], message)
```

### Database Integration
```python
import sqlite3

conn = sqlite3.connect('telegram_data.db')
cursor = conn.cursor()

# Store users
cursor.execute('''
    INSERT INTO users (id, username, first_name)
    VALUES (?, ?, ?)
''', (user['id'], user['username'], user['first_name']))

conn.commit()
```

### Scheduled Automation
```python
import schedule

def scan_resources():
    asyncio.run(bot.search_messages(channel, keywords))

# Run every hour
schedule.every().hour.do(scan_resources)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Project Structure

```
telegram-automation/
├── telegram_automation_example.py  # Main script
├── telegram_requirements.txt       # Dependencies
├── .env                           # Your credentials (DO NOT COMMIT)
├── .env.example                   # Template for .env
├── TELEGRAM_AUTOMATION_GUIDE.md   # Comprehensive guide
├── SETUP_INSTRUCTIONS.md          # This file
├── telegram_session.session       # Session file (auto-created)
├── found_resources.json          # Search results (auto-created)
├── active_users.json             # Active users data (auto-created)
└── monitored_resources.txt       # Monitoring logs (auto-created)
```

---

## Testing Checklist

Before running in production:

- [ ] Test with a small number of users (5-10)
- [ ] Verify message content is correct
- [ ] Check rate limiting is working
- [ ] Ensure error handling is functional
- [ ] Test in dry-run mode first
- [ ] Verify you have necessary permissions
- [ ] Check that session is persisting correctly
- [ ] Test recovery from FloodWaitError
- [ ] Confirm data is being saved correctly
- [ ] Review and comply with ToS

---

## Getting Help

### Resources
- **Telethon Docs**: https://docs.telethon.dev/
- **Telegram API**: https://core.telegram.org/api
- **Stack Overflow**: Search for "telethon" tag

### Common Commands

```bash
# Install dependencies
pip install -r telegram_requirements.txt

# Run the script
python telegram_automation_example.py

# Check session status
ls -la *.session

# View logs (if you add logging)
tail -f automation.log

# Clean session (to re-authenticate)
rm *.session*
```

---

## Next Steps

1. ✅ Complete setup and test basic functionality
2. ✅ Customize the script for your specific use case
3. ✅ Test thoroughly with dry_run=True
4. ✅ Implement additional features as needed
5. ✅ Set up monitoring and logging
6. ✅ Consider database integration for larger datasets
7. ✅ Implement scheduled automation if needed
8. ✅ Review and follow best practices

---

## Disclaimer

This tool is for educational and legitimate automation purposes only. Users are responsible for:
- Complying with Telegram's Terms of Service
- Respecting user privacy and data protection laws
- Obtaining consent before sending messages
- Not engaging in spam or harassment
- Using the tool ethically and responsibly

The creators are not responsible for misuse of this tool.

---

## Support

For issues or questions:
1. Check the TELEGRAM_AUTOMATION_GUIDE.md for detailed information
2. Review this setup guide
3. Search for similar issues online
4. Check Telethon documentation

Happy automating! 🚀
