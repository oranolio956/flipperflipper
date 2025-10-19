#!/usr/bin/env python3
"""
Helper script to list all groups and their IDs
Run this to find the group ID for your config
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def main():
    """List all groups user is in"""
    
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone = os.getenv('PHONE_NUMBER')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Error: API_ID, API_HASH, and PHONE_NUMBER required in .env!")
        return
    
    client = TelegramClient('get_groups_session', int(api_id), api_hash)
    
    print("🔐 Connecting to Telegram...")
    await client.start(phone=phone)
    
    print("✅ Connected!\n")
    print("=" * 70)
    print("YOUR TELEGRAM GROUPS:")
    print("=" * 70)
    print()
    
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            chat = dialog.entity
            print(f"📁 Name: {dialog.name}")
            print(f"   ID: {chat.id}")
            if hasattr(chat, 'username') and chat.username:
                print(f"   Username: @{chat.username}")
            group_type = 'Channel' if dialog.is_channel else 'Group'
            print(f"   Type: {group_type}")
            print()
    
    print("=" * 70)
    print("\n💡 Copy the ID or username of your target group")
    print("   Then add it to config.json as 'target_group'")
    print()
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
