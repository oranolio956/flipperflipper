#!/usr/bin/env python3
"""
Test Mailjet Email System
"""

import os
from email_manager_mailjet import email_manager

def test_mailjet():
    print("🧪 Testing Mailjet Email System")
    print("=" * 50)
    
    # Check if API secret is set
    if not email_manager.api_secret:
        print("❌ MAILJET_API_SECRET not set!")
        print("Please set the environment variable:")
        print("export MAILJET_API_SECRET='your-secret-key-here'")
        print("\nGet your secret key from: https://app.mailjet.com/account/apikeys")
        return False
    
    print(f"✅ API Key: {email_manager.api_key}")
    print(f"✅ API Secret: {'*' * len(email_manager.api_secret)}")
    print(f"✅ From Email: {email_manager.from_email}")
    
    # Test connection
    print("\n🔗 Testing Mailjet connection...")
    if email_manager.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return False
    
    # Generate test code
    print("\n🔢 Generating verification code...")
    code = email_manager.generate_code()
    print(f"✅ Generated code: {code}")
    
    # Test email sending
    print(f"\n📧 Sending test email to brooketogo98@gmail.com...")
    success = email_manager.send_verification_email(
        to_email='brooketogo98@gmail.com',
        code=code,
        ip_address='127.0.0.1'
    )
    
    if success:
        print("✅ Test email sent successfully!")
        print(f"📬 Check brooketogo98@gmail.com for code: {code}")
        return True
    else:
        print("❌ Failed to send test email!")
        return False

if __name__ == "__main__":
    success = test_mailjet()
    if success:
        print("\n🏆 Mailjet test completed successfully!")
    else:
        print("\n💥 Mailjet test failed!")
        exit(1)