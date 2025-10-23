#!/usr/bin/env python3
"""
Switch to Free Email System
Automatically configures the system to use free email methods
"""

import os
import sys
from pathlib import Path

def switch_to_free_email():
    """Switch the system to use free email manager"""
    
    print("🔄 Switching to Free Email System...")
    
    # Read the current email_auth.py
    try:
        with open('email_auth.py', 'r') as f:
            content = f.read()
        
        # Check if already using free email
        if 'from free_email_manager import free_email_manager' in content:
            print("✅ System already using free email manager")
            return True
        
        # Replace the automated_email_service import
        old_import = 'from automated_email_service import automated_email_service'
        new_import = 'from free_email_manager import free_email_manager'
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            print("✅ Updated import statement")
        
        # Replace the send_verification_email call
        old_call = 'success = automated_email_service.send_verification_email(email, code, ip_address)'
        new_call = 'success = free_email_manager.send_verification_email(email, code, ip_address)'
        
        if old_call in content:
            content = content.replace(old_call, new_call)
            print("✅ Updated email sending call")
        
        # Write the updated content
        with open('email_auth.py', 'w') as f:
            f.write(content)
        
        print("✅ Successfully switched to free email system!")
        print("\nNext steps:")
        print("1. Run: python3 simple_email_setup.py")
        print("2. Choose your preferred email method")
        print("3. Test the setup")
        print("4. Start the system: python3 web_app_real.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error switching to free email: {e}")
        return False

def main():
    print("""
🔐 FREE EMAIL SYSTEM SWITCHER
=============================
This will switch your system from paid email services
to free anonymous email methods.

Perfect for 10 emails/month with no signup required!
""")
    
    confirm = input("\nSwitch to free email system? (y/n): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        if switch_to_free_email():
            print("\n🎉 System successfully configured for free email!")
        else:
            print("\n❌ Failed to switch to free email system")
    else:
        print("\n❌ Operation cancelled")

if __name__ == "__main__":
    main()