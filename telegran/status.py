#!/usr/bin/env python3
"""
Status and control script for Telegran userbot
Shows current status, stats, and allows manual control
"""

import os
import json
from datetime import datetime
from database import Database

def print_header(title):
    """Print section header"""
    print("\n" + "="*60)
    print(title)
    print("="*60)

def main():
    """Show status"""
    
    print("\n🤖 TELEGRAN USERBOT - STATUS")
    print("="*60)
    
    # Check if configured
    if not os.path.exists('.env'):
        print("\n❌ Bot not configured!")
        print("   Run: python3 setup_wizard.py")
        return
    
    if not os.path.exists('config.json'):
        print("\n❌ Config file missing!")
        print("   Run: python3 setup_wizard.py")
        return
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except:
        print("\n❌ Error reading config.json")
        return
    
    # Check database
    if not os.path.exists('userbot_data.json'):
        print("\n⚠️  Database not yet created")
        print("   Bot hasn't run yet or no one welcomed")
        db_stats = {
            'total_welcomed': 0,
            'active_cooldowns': 0,
            'messages_today': 0,
            'pending_welcomes': 0
        }
    else:
        db = Database()
        db_stats = db.get_stats()
    
    # Configuration Status
    print_header("CONFIGURATION")
    print(f"Target Group: {config.get('target_group', 'NOT SET')}")
    print(f"Mode: {'SIMPLE' if config.get('simple_mode') else 'STEALTH'}")
    print(f"Auto-Welcome: {'✅ ON' if config.get('enable_welcome') else '❌ OFF'}")
    print(f"Auto-Help: {'✅ ON' if config.get('enable_help') else '❌ OFF'}")
    
    # Rate Limits
    print_header("RATE LIMITS")
    stealth = config.get('stealth', {})
    print(f"Max/Hour: {stealth.get('max_messages_per_hour', 'NOT SET')}")
    print(f"Max/Day: {stealth.get('max_messages_per_day', 'NOT SET')}")
    print(f"Response Rate: {int(stealth.get('response_probability', 0) * 100)}%")
    
    # Statistics
    print_header("STATISTICS")
    print(f"Total Welcomed: {db_stats['total_welcomed']}")
    print(f"Messages Today: {db_stats['messages_today']}")
    print(f"Active Cooldowns: {db_stats['active_cooldowns']}")
    print(f"Pending Welcomes: {db_stats['pending_welcomes']}")
    
    if db_stats['pending_welcomes'] > 0:
        print("\n⚠️  Warning: People are waiting to be welcomed!")
        print(f"   {db_stats['pending_welcomes']} user(s) in pending queue")
        print("   They'll be welcomed when rate limits allow")
    
    # Messages
    print_header("MESSAGES")
    if config.get('simple_mode'):
        print("Simple Mode - Same message for everyone:")
        print(f"  Welcome: {config.get('simple_welcome_message', 'NOT SET')}")
        print(f"  Help: {config.get('simple_help_message', 'NOT SET')}")
    else:
        print(f"Stealth Mode - {len(config.get('welcome_messages', []))} variations")
    
    # Process Check
    print_header("PROCESS STATUS")
    # Try to detect if bot is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'userbot.py'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("✅ Bot is RUNNING")
            print(f"   PID: {result.stdout.strip()}")
        else:
            print("❌ Bot is NOT running")
            print("   Start with: python3 userbot.py")
    except:
        print("❓ Cannot detect process status")
    
    # Quick Actions
    print_header("QUICK ACTIONS")
    print("Test setup:     python3 test_bot.py")
    print("Find group ID:  python3 get_group_id.py")
    print("View logs:      tail -f telegran.log")
    print("Edit config:    nano config.json")
    print("Reconfigure:    python3 setup_wizard.py")
    print()
    
    # Database details
    if db_stats['total_welcomed'] > 0 and os.path.exists('userbot_data.json'):
        print_header("DATABASE DETAILS")
        db = Database()
        
        # Show last reset date
        with open('userbot_data.json', 'r') as f:
            data = json.load(f)
            last_reset = data.get('last_reset_date', 'Unknown')
            print(f"Last Daily Reset: {last_reset}")
        
        # Show pending if any
        pending = db.get_pending_welcomes()
        if pending:
            print(f"\nPending Welcomes ({len(pending)}):")
            for p in pending[:5]:  # Show first 5
                username = p.get('username', 'Unknown')
                reason = p.get('reason', 'unknown')
                added = p.get('added', 'unknown')
                print(f"  - {username} (reason: {reason}, added: {added})")
            if len(pending) > 5:
                print(f"  ... and {len(pending) - 5} more")
    
    print()

if __name__ == '__main__':
    main()
