#!/usr/bin/env python3
"""
Test Free Email System
Quick test to verify email verification works
"""

import os
import sys
from pathlib import Path

def test_free_email():
    """Test the free email system"""
    print("🧪 Testing Free Email System...")
    
    try:
        # Import the free email manager
        from free_email_manager import free_email_manager
        
        # Test email
        test_email = "test@example.com"
        test_code = "123456"
        test_ip = "127.0.0.1"
        
        print(f"📧 Sending test email to: {test_email}")
        print(f"🔢 Test code: {test_code}")
        
        # Send test email
        success = free_email_manager.send_verification_email(test_email, test_code, test_ip)
        
        if success:
            print("✅ Free email system is working!")
            print("\n📋 Available methods:")
            print("1. Gmail SMTP - sends to your Gmail inbox")
            print("2. Telegram Bot - sends to your Telegram chat")
            print("3. Discord Webhook - sends to your Discord channel")
            print("4. Webhook.site - sends to webhook page (testing)")
            
            print("\n🚀 Next steps:")
            print("1. Run: python3 simple_email_setup.py")
            print("2. Choose your preferred method")
            print("3. Configure your .env file")
            print("4. Test with your real email")
            print("5. Start the system: python3 web_app_real.py")
            
            return True
        else:
            print("❌ Free email system test failed")
            print("This is normal - you need to configure your .env file first")
            print("Run: python3 simple_email_setup.py")
            return False
            
    except Exception as e:
        print(f"❌ Error testing free email: {e}")
        return False

def main():
    print("""
🔐 FREE EMAIL SYSTEM TEST
=========================
Testing your anonymous email verification system...
""")
    
    test_free_email()

if __name__ == "__main__":
    main()