#!/usr/bin/env python3
"""
Simple Email Setup for Anonymous Verification
Perfect for 10 emails/month - no signup required!
"""

import os
import sys
from pathlib import Path

def print_banner():
    print("""
🔐 ANONYMOUS EMAIL VERIFICATION SETUP
=====================================
Perfect for 10 emails/month - NO SIGNUP REQUIRED!

Choose your preferred method:
""")

def create_simple_env():
    """Create a simple .env file"""
    env_content = """# Simple Email Configuration - Choose ONE method below
USE_FREE_EMAIL=true
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Security System

# METHOD 1: Gmail SMTP (Easiest - just need Gmail account)
# Uncomment these lines and add your Gmail details:
# GMAIL_APP_PASSWORD=your-16-char-app-password

# METHOD 2: Telegram Bot (Instant - no email needed)
# Uncomment these lines and add your bot details:
# TELEGRAM_BOT_TOKEN=your-bot-token
# TELEGRAM_CHAT_ID=your-chat-id

# METHOD 3: Discord Webhook (Instant - no email needed)
# Uncomment this line and add your webhook:
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# METHOD 4: Webhook.site (Testing - instant, no setup)
# Uncomment this line and add your webhook:
# WEBHOOK_SITE_URL=https://webhook.site/your-unique-id
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")

def setup_gmail_simple():
    """Super simple Gmail setup"""
    print("""
📧 GMAIL SETUP (2 minutes)
=========================

1. Go to https://gmail.com (create account if needed)
2. Go to Google Account → Security → 2-Step Verification → Turn ON
3. Go to Google Account → Security → App passwords
4. Select "Mail" → "Other" → Enter "Security" → Copy the 16-character password
5. Edit .env file:
   - Change FROM_EMAIL to your Gmail address
   - Uncomment GMAIL_APP_PASSWORD line
   - Paste the 16-character password

That's it! Your verification codes will be sent to your Gmail inbox.
""")

def setup_telegram_simple():
    """Super simple Telegram setup"""
    print("""
📱 TELEGRAM SETUP (1 minute)
============================

1. Open Telegram app
2. Message @BotFather
3. Send: /newbot
4. Follow instructions to create bot
5. Copy the bot token
6. Message your new bot (to get chat ID)
7. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
8. Find your chat ID in the response
9. Edit .env file:
   - Uncomment TELEGRAM_BOT_TOKEN and add your token
   - Uncomment TELEGRAM_CHAT_ID and add your chat ID

That's it! Verification codes will appear in your Telegram chat instantly.
""")

def setup_discord_simple():
    """Super simple Discord setup"""
    print("""
💬 DISCORD SETUP (30 seconds)
============================

1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Create New Webhook → Copy URL
4. Edit .env file:
   - Uncomment DISCORD_WEBHOOK_URL
   - Paste your webhook URL

That's it! Verification codes will appear in your Discord channel instantly.
""")

def setup_webhook_simple():
    """Super simple Webhook setup"""
    print("""
🌐 WEBHOOK.SITE SETUP (10 seconds)
==================================

1. Visit https://webhook.site
2. Copy your unique URL
3. Edit .env file:
   - Uncomment WEBHOOK_SITE_URL
   - Paste your webhook URL

That's it! Verification codes will appear on the webhook.site page instantly.
Perfect for testing!
""")

def test_email():
    """Test the email setup"""
    print("\n🧪 Testing your setup...")
    
    try:
        from free_email_manager import free_email_manager
        
        test_email = input("Enter your email to test: ").strip()
        if not test_email:
            print("❌ No email provided")
            return False
        
        print("Sending test verification code...")
        success = free_email_manager.send_verification_email(test_email, "123456", "127.0.0.1")
        
        if success:
            print("✅ Test successful!")
            print("Check your chosen method for the verification code")
            return True
        else:
            print("❌ Test failed - check your .env configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print_banner()
    
    # Create .env file
    create_simple_env()
    
    while True:
        print("\n🚀 QUICK SETUP OPTIONS")
        print("1. Gmail SMTP (Email to your inbox)")
        print("2. Telegram Bot (Instant messages)")
        print("3. Discord Webhook (Instant messages)")
        print("4. Webhook.site (Testing only)")
        print("5. Test current setup")
        print("6. Start the system")
        print("7. Exit")
        
        choice = input("\nChoose (1-7): ").strip()
        
        if choice == "1":
            setup_gmail_simple()
        elif choice == "2":
            setup_telegram_simple()
        elif choice == "3":
            setup_discord_simple()
        elif choice == "4":
            setup_webhook_simple()
        elif choice == "5":
            test_email()
        elif choice == "6":
            print("\n🚀 Starting the system...")
            print("Run these commands:")
            print("1. python3 create_email_tables.py")
            print("2. python3 web_app_real.py")
            print("3. Visit: http://localhost:5000")
            break
        elif choice == "7":
            print("\n✅ Setup complete!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()