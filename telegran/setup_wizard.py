#!/usr/bin/env python3
"""
Interactive Setup Wizard for Telegran Userbot
Makes setup super easy!
"""

import os
import json
import sys

def print_header():
    """Print welcome header"""
    print("\n" + "="*60)
    print("🕵️  TELEGRAN USERBOT - SETUP WIZARD")
    print("="*60)
    print()

def print_step(num, title):
    """Print step header"""
    print(f"\n{'='*60}")
    print(f"STEP {num}: {title}")
    print(f"{'='*60}\n")

def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def yes_no(prompt):
    """Get yes/no input"""
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")

def main():
    """Run interactive setup"""
    
    print_header()
    
    print("This wizard will help you set up your Telegran userbot.")
    print("It's quick and easy - just answer a few questions!")
    print()
    
    if not yes_no("Ready to begin?"):
        print("\nSetup cancelled. Run this again when ready!")
        return
    
    # Check if already configured
    if os.path.exists('.env') and os.path.exists('config.json'):
        print("\n⚠️  Found existing configuration!")
        if not yes_no("Do you want to reconfigure?"):
            print("\nKeeping existing configuration. Setup complete!")
            return
    
    # Step 1: API Credentials
    print_step(1, "Telegram API Credentials")
    print("You need API credentials from Telegram.")
    print("📝 Get them here: https://my.telegram.org/apps")
    print()
    
    if yes_no("Have you created an app and got your credentials?"):
        api_id = get_input("Enter your API_ID (numbers only)")
        api_hash = get_input("Enter your API_HASH")
        phone = get_input("Enter your phone number (with country code, e.g., +1234567890)")
        
        # Save to .env
        with open('.env', 'w') as f:
            f.write(f"# Telegran Userbot Configuration\n")
            f.write(f"API_ID={api_id}\n")
            f.write(f"API_HASH={api_hash}\n")
            f.write(f"PHONE_NUMBER={phone}\n")
            f.write(f"ENVIRONMENT=production\n")
            f.write(f"LOG_LEVEL=INFO\n")
        
        print("\n✅ Credentials saved to .env")
    else:
        print("\n⚠️  Please:")
        print("   1. Go to https://my.telegram.org/apps")
        print("   2. Create an application")
        print("   3. Run this wizard again")
        return
    
    # Step 2: Find Target Group
    print_step(2, "Target Group")
    print("Which Telegram group do you want to monitor?")
    print()
    print("💡 Tip: You can run 'python3 get_group_id.py' to see all your groups")
    print()
    
    group_choice = get_input("Enter group username (e.g., cupidbotg) or ID")
    
    # Step 3: Message Configuration
    print_step(3, "Welcome Message Setup")
    print("How do you want to welcome new members?")
    print()
    print("Option 1: SIMPLE MODE (Recommended for beginners)")
    print("   - Same message for everyone")
    print("   - Consistent branding")
    print("   - Perfect for 'copy/paste all day'")
    print()
    print("Option 2: STEALTH MODE (Advanced)")
    print("   - Multiple message variations")
    print("   - Looks more human")
    print("   - Better anti-detection")
    print()
    
    simple_mode = yes_no("Use SIMPLE MODE?")
    
    if simple_mode:
        print("\nEnter your welcome message:")
        print("💡 Use {username} where you want the person's name")
        print("Example: Hey {username}! Welcome to our community! 👋")
        print()
        welcome_msg = get_input("Your message")
        
        print("\nEnter your help response message:")
        print("Example: Hi {username}! What do you need help with?")
        print()
        help_msg = get_input("Your message")
    else:
        print("\n✅ Using stealth mode with multiple variations")
        print("   You can edit these later in config.json")
        welcome_msg = None
        help_msg = None
    
    # Step 4: Rate Limits
    print_step(4, "Rate Limits (Safety)")
    print("How many messages per hour should the bot send?")
    print()
    print("Recommended:")
    print("  - Conservative: 3-5 messages/hour")
    print("  - Moderate: 5-8 messages/hour")
    print("  - Aggressive: 8-12 messages/hour (riskier)")
    print()
    
    rate_limit = get_input("Messages per hour", "8")
    try:
        rate_limit = int(rate_limit)
        if rate_limit > 30:
            print("\n⚠️  Warning: That's very high! Telegram limit is ~30/minute")
            if not yes_no("Continue anyway?"):
                rate_limit = 8
    except:
        rate_limit = 8
    
    # Step 5: Enable Features
    print_step(5, "Features to Enable")
    
    enable_welcome = yes_no("Enable auto-welcome for new members?")
    enable_help = yes_no("Enable auto-response to help requests?")
    
    # Step 6: Create Config
    print_step(6, "Creating Configuration")
    
    config = {
        "simple_mode": simple_mode,
        "target_group": group_choice,
        "enable_welcome": enable_welcome,
        "enable_help": enable_help,
        "stealth_mode": True
    }
    
    if simple_mode and welcome_msg:
        config["simple_welcome_message"] = welcome_msg
        config["simple_help_message"] = help_msg
    else:
        config["welcome_messages"] = [
            f"Hey {{username}}! Welcome to the group! 👋 Glad you're here!",
            f"Hi {{username}}! Great to have you join us! Feel free to ask if you need anything 😊",
            f"Welcome {{username}}! 🎉 Hope you enjoy the community!",
            f"Hey there {{username}}! Welcome aboard! Don't hesitate to reach out if you have questions 💬",
            f"Hi {{username}}! Nice to see you here! Welcome to the group! 😊"
        ]
        config["help_messages"] = [
            f"Hey {{username}}! I saw your message - what do you need help with?",
            f"Hi {{username}}! I can help with that. What specifically are you looking for?",
            f"Hey {{username}}! I'm around if you need assistance. What's up?",
            f"Hi {{username}}! Let me know how I can help you out 😊",
            f"Hey {{username}}! What can I help you with?"
        ]
    
    config["help_keywords"] = [
        "help", "support", "how do i", "how to", "question",
        "need assistance", "can someone help", "anyone help",
        "issue", "problem", "stuck", "confused",
        "don't understand", "not working", "need help"
    ]
    
    config["stealth"] = {
        "welcome_delay_min": 45,
        "welcome_delay_max": 180,
        "help_delay_min": 10,
        "help_delay_max": 60,
        "typing_time_min": 0 if simple_mode else 2,  # Disable typing in simple mode
        "typing_time_max": 0 if simple_mode else 5,
        "cooldown_hours": 24,
        "max_messages_per_hour": rate_limit,
        "max_messages_per_day": rate_limit * 6,  # 6 hours worth
        "response_probability": 1.0 if simple_mode else 0.85,  # Always respond in simple mode
        "active_hours_start": 8,
        "active_hours_end": 23,
        "night_response_probability": 0.3 if not simple_mode else 1.0
    }
    
    # Save config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Configuration saved!")
    
    # Step 7: Summary
    print_step(7, "Setup Complete!")
    print("✅ API credentials configured")
    print(f"✅ Target group: {group_choice}")
    print(f"✅ Mode: {'SIMPLE' if simple_mode else 'STEALTH'}")
    print(f"✅ Rate limit: {rate_limit} messages/hour")
    print(f"✅ Auto-welcome: {'ON' if enable_welcome else 'OFF'}")
    print(f"✅ Auto-help: {'ON' if enable_help else 'OFF'}")
    print()
    print("="*60)
    print("NEXT STEPS:")
    print("="*60)
    print()
    print("1. Join your target group if you haven't already")
    print()
    print("2. Test your setup:")
    print("   python3 test_bot.py")
    print()
    print("3. Start the bot:")
    print("   python3 userbot.py")
    print()
    print("4. Watch the logs:")
    print("   tail -f telegran.log")
    print()
    print("💡 Pro tip: Start with low rate limits and increase gradually!")
    print()
    print("📚 Read USERBOT_SETUP.md for more details")
    print()
    print("🎉 You're ready to go!")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
