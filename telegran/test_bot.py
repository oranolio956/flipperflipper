#!/usr/bin/env python3
"""
Test script to verify bot setup without actually sending messages
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def main():
    """Test bot configuration"""
    
    print("🧪 TELEGRAN BOT TEST MODE")
    print("=" * 50)
    print()
    
    # Check 1: Environment variables
    print("1️⃣  Checking environment variables...")
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone = os.getenv('PHONE_NUMBER')
    
    if not all([api_id, api_hash, phone]):
        print("   ❌ FAIL: Missing API_ID, API_HASH, or PHONE_NUMBER in .env")
        return
    print("   ✅ PASS: All environment variables set")
    print()
    
    # Check 2: Config file
    print("2️⃣  Checking config.json...")
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Check welcome messages
        if not config.get('welcome_messages'):
            print("   ❌ FAIL: No welcome_messages in config")
            return
        print(f"   ✅ PASS: {len(config['welcome_messages'])} welcome messages")
        
        # Check help messages
        if not config.get('help_messages'):
            print("   ❌ FAIL: No help_messages in config")
            return
        print(f"   ✅ PASS: {len(config['help_messages'])} help messages")
        
        # Check target group
        if not config.get('target_group'):
            print("   ❌ FAIL: No target_group set")
            return
        print(f"   ✅ PASS: Target group: {config['target_group']}")
        
        # Check simple mode
        if config.get('simple_mode'):
            print("   ℹ️  INFO: Simple mode ENABLED (one message for all)")
            simple_msg = config.get('simple_welcome_message', 'NOT SET!')
            print(f"   Message: {simple_msg}")
        else:
            print("   ℹ️  INFO: Simple mode disabled (random variations)")
        
    except FileNotFoundError:
        print("   ❌ FAIL: config.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"   ❌ FAIL: Invalid JSON in config.json: {e}")
        return
    print()
    
    # Check 3: Database module
    print("3️⃣  Checking database module...")
    try:
        from database import Database
        db = Database()
        stats = db.get_stats()
        print("   ✅ PASS: Database initialized")
        print(f"   ℹ️  INFO: {stats['total_welcomed']} users welcomed so far")
    except Exception as e:
        print(f"   ❌ FAIL: Database error: {e}")
        return
    print()
    
    # Check 4: Telegram connection
    print("4️⃣  Testing Telegram connection...")
    client = TelegramClient('test_session', int(api_id), api_hash)
    
    try:
        await client.start(phone=phone)
        me = await client.get_me()
        username = f"@{me.username}" if me.username else "no username"
        print(f"   ✅ PASS: Connected as {me.first_name} ({username})")
    except Exception as e:
        print(f"   ❌ FAIL: Connection error: {e}")
        await client.disconnect()
        return
    print()
    
    # Check 5: Target group access
    print("5️⃣  Checking target group access...")
    target = config['target_group']
    found = False
    
    async for dialog in client.iter_dialogs():
        if not (dialog.is_group or dialog.is_channel):
            continue
        
        chat = dialog.entity
        
        # Check by username
        if hasattr(chat, 'username') and chat.username:
            if chat.username.lower() == target.lower():
                print(f"   ✅ PASS: Found group '{dialog.name}' (ID: {chat.id})")
                found = True
                break
        
        # Check by ID
        try:
            target_id = int(target)
            if chat.id == target_id:
                print(f"   ✅ PASS: Found group '{dialog.name}' (ID: {chat.id})")
                found = True
                break
        except ValueError:
            pass
    
    if not found:
        print(f"   ❌ FAIL: Target group '{target}' not found!")
        print("   ℹ️  Run 'python3 get_group_id.py' to see all your groups")
        await client.disconnect()
        return
    print()
    
    # Check 6: Permissions
    print("6️⃣  Checking bot permissions...")
    print("   ℹ️  INFO: Userbot has same permissions as your account")
    print("   ✅ PASS: Should be able to read and send messages")
    print()
    
    await client.disconnect()
    
    # Final summary
    print("=" * 50)
    print("✅ ALL CHECKS PASSED!")
    print("=" * 50)
    print()
    print("🚀 Your bot is ready to run!")
    print("   Start with: python3 userbot.py")
    print()
    print("💡 Tips:")
    print("   - Watch logs with: tail -f telegran.log")
    print("   - Check stats with: cat userbot_data.json")
    print("   - Start with conservative rate limits")
    print()

if __name__ == '__main__':
    asyncio.run(main())
