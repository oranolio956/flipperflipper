#!/usr/bin/env python3
"""
Free Email Setup Script
Interactive setup for free email verification methods
"""

import os
import sys
from pathlib import Path

def print_banner():
    print("""
🚀 FREE EMAIL SETUP SCRIPT
==========================
This script will help you set up FREE email verification
without needing paid services like Mailjet.

Available methods:
1. Gmail SMTP (Recommended)
2. Outlook SMTP
3. Telegram Bot
4. Discord Webhook
5. Webhook.site (Testing)
""")

def create_env_file():
    """Create .env file with user's configuration"""
    print("\n📝 Setting up environment variables...")
    
    env_content = """# Free Email Configuration
USE_FREE_EMAIL=true
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Your App Name

# Choose ONE method below (uncomment the one you want to use):

# Gmail SMTP (Recommended)
# GMAIL_APP_PASSWORD=your-16-char-app-password

# Outlook SMTP
# OUTLOOK_PASSWORD=your-outlook-password

# Telegram Bot
# TELEGRAM_BOT_TOKEN=your-bot-token
# TELEGRAM_CHAT_ID=your-chat-id

# Discord Webhook
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Webhook.site (Testing)
# WEBHOOK_SITE_URL=https://webhook.site/your-unique-id
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env file with your email configuration")

def setup_gmail():
    """Guide user through Gmail setup"""
    print("""
📧 GMAIL SMTP SETUP
==================

1. Go to https://gmail.com and create an account (if needed)
2. Enable 2-Factor Authentication:
   - Google Account → Security → 2-Step Verification
3. Generate App Password:
   - Google Account → Security → App passwords
   - Select "Mail" and "Other"
   - Enter "Stitch RAT" as app name
   - Copy the 16-character password
4. Edit .env file:
   - Set FROM_EMAIL to your Gmail address
   - Set GMAIL_APP_PASSWORD to the 16-character password
   - Uncomment the Gmail lines
""")

def setup_outlook():
    """Guide user through Outlook setup"""
    print("""
📧 OUTLOOK SMTP SETUP
====================

1. Go to https://outlook.com and create an account (if needed)
2. Edit .env file:
   - Set FROM_EMAIL to your Outlook address
   - Set OUTLOOK_PASSWORD to your Outlook password
   - Uncomment the Outlook lines
""")

def setup_telegram():
    """Guide user through Telegram setup"""
    print("""
📱 TELEGRAM BOT SETUP
====================

1. Open Telegram and message @BotFather
2. Send /newbot and follow instructions
3. Copy the bot token you receive
4. Message your new bot to get chat ID
5. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
6. Find your chat ID in the response
7. Edit .env file:
   - Set TELEGRAM_BOT_TOKEN to your bot token
   - Set TELEGRAM_CHAT_ID to your chat ID
   - Uncomment the Telegram lines
""")

def setup_discord():
    """Guide user through Discord setup"""
    print("""
💬 DISCORD WEBHOOK SETUP
========================

1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Create New Webhook
4. Copy the webhook URL
5. Edit .env file:
   - Set DISCORD_WEBHOOK_URL to your webhook URL
   - Uncomment the Discord lines
""")

def setup_webhook_site():
    """Guide user through Webhook.site setup"""
    print("""
🌐 WEBHOOK.SITE SETUP
====================

1. Visit https://webhook.site
2. Copy your unique webhook URL
3. Edit .env file:
   - Set WEBHOOK_SITE_URL to your webhook URL
   - Uncomment the Webhook.site lines

Note: This is mainly for testing - codes will appear on the webhook.site page
""")

def test_setup():
    """Test the email setup"""
    print("\n🧪 Testing email setup...")
    
    try:
        from free_email_manager import free_email_manager
        
        # Test email
        test_email = input("Enter your email to test: ").strip()
        if not test_email:
            print("❌ No email provided")
            return False
        
        print("Sending test email...")
        success = free_email_manager.send_verification_email(test_email, "123456", "127.0.0.1")
        
        if success:
            print("✅ Test email sent successfully!")
            print("Check your chosen method for the verification code")
            return True
        else:
            print("❌ Failed to send test email")
            print("Please check your .env configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error testing setup: {e}")
        return False

def main():
    print_banner()
    
    # Create .env file
    create_env_file()
    
    # Show setup options
    while True:
        print("\n🔧 SETUP OPTIONS")
        print("1. Gmail SMTP (Recommended)")
        print("2. Outlook SMTP")
        print("3. Telegram Bot")
        print("4. Discord Webhook")
        print("5. Webhook.site (Testing)")
        print("6. Test current setup")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            setup_gmail()
        elif choice == "2":
            setup_outlook()
        elif choice == "3":
            setup_telegram()
        elif choice == "4":
            setup_discord()
        elif choice == "5":
            setup_webhook_site()
        elif choice == "6":
            test_setup()
        elif choice == "7":
            print("\n✅ Setup complete!")
            print("Next steps:")
            print("1. Edit .env file with your configuration")
            print("2. Run: python3 create_email_tables.py")
            print("3. Run: python3 create_mfa_tables.py")
            print("4. Run: python3 web_app_real.py")
            print("5. Visit: http://localhost:5000")
            break
        else:
            print("❌ Invalid option, please try again")

if __name__ == "__main__":
    main()