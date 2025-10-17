#!/usr/bin/env python3
"""
Telegram Channel Automation Example
====================================

This script demonstrates how to:
1. Connect to a Telegram channel
2. Retrieve channel members
3. Send messages to users
4. Search for resources in channel history

Requirements:
    pip install telethon python-dotenv

Usage:
    1. Create a .env file with your credentials
    2. Run: python telegram_automation_example.py
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from telethon import TelegramClient, events
    from telethon.tl.functions.channels import GetParticipantsRequest
    from telethon.tl.types import ChannelParticipantsSearch
    from telethon.errors import FloodWaitError, SessionPasswordNeededError
except ImportError:
    print("Error: telethon not installed. Run: pip install telethon")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables directly.")


class TelegramChannelBot:
    """
    A bot for automating Telegram channel operations
    """
    
    def __init__(self, api_id: str, api_hash: str, phone: str, session_name: str = 'telegram_session'):
        """
        Initialize the Telegram bot
        
        Args:
            api_id: Your Telegram API ID
            api_hash: Your Telegram API Hash
            phone: Your phone number (with country code)
            session_name: Name for the session file
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.is_connected = False
    
    async def connect(self):
        """Connect to Telegram"""
        try:
            await self.client.start(phone=self.phone)
            self.is_connected = True
            print("✅ Successfully connected to Telegram")
            
            # Get and display current user info
            me = await self.client.get_me()
            print(f"📱 Logged in as: {me.first_name} (@{me.username})")
            
        except SessionPasswordNeededError:
            print("❌ Two-factor authentication enabled. Please enter your password.")
            password = input("Password: ")
            await self.client.start(phone=self.phone, password=password)
            self.is_connected = True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        await self.client.disconnect()
        self.is_connected = False
        print("👋 Disconnected from Telegram")
    
    async def get_channel(self, channel_identifier: str):
        """
        Get channel entity
        
        Args:
            channel_identifier: Channel username (e.g., '@channelname') or ID
            
        Returns:
            Channel entity
        """
        try:
            channel = await self.client.get_entity(channel_identifier)
            print(f"📺 Channel: {channel.title}")
            print(f"   ID: {channel.id}")
            print(f"   Username: @{channel.username if channel.username else 'N/A'}")
            print(f"   Participants: {channel.participants_count if hasattr(channel, 'participants_count') else 'Unknown'}")
            return channel
        except Exception as e:
            print(f"❌ Error getting channel: {e}")
            return None
    
    async def get_channel_members(self, channel, max_members: int = 100) -> List[Dict]:
        """
        Retrieve members from a channel
        
        Args:
            channel: Channel entity
            max_members: Maximum number of members to retrieve
            
        Returns:
            List of user dictionaries
        """
        print(f"\n🔍 Retrieving up to {max_members} channel members...")
        
        all_participants = []
        offset = 0
        limit = 100
        
        try:
            while len(all_participants) < max_members:
                participants = await self.client(GetParticipantsRequest(
                    channel=channel,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=min(limit, max_members - len(all_participants)),
                    hash=0
                ))
                
                if not participants.users:
                    break
                
                # Convert users to dictionaries
                for user in participants.users:
                    if not user.bot:  # Skip bots
                        all_participants.append({
                            'id': user.id,
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone': user.phone if hasattr(user, 'phone') else None,
                            'is_bot': user.bot
                        })
                
                offset += len(participants.users)
                print(f"   Retrieved {len(all_participants)} members so far...")
                
                # Rate limiting
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"⚠️ Error retrieving members: {e}")
            print(f"   Retrieved {len(all_participants)} members before error")
        
        print(f"✅ Total members retrieved: {len(all_participants)}")
        return all_participants
    
    async def send_message_to_user(self, user_id: int, message: str, delay: int = 5) -> bool:
        """
        Send a message to a single user
        
        Args:
            user_id: User's Telegram ID
            message: Message text
            delay: Delay after sending (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.client.send_message(user_id, message)
            await asyncio.sleep(delay)
            return True
        except FloodWaitError as e:
            print(f"⚠️ Rate limit hit. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    async def send_bulk_messages(self, users: List[Dict], message_template: str, delay: int = 10, dry_run: bool = True):
        """
        Send messages to multiple users
        
        Args:
            users: List of user dictionaries
            message_template: Message template (use {first_name}, {username})
            delay: Delay between messages (seconds)
            dry_run: If True, only simulate sending
        """
        print(f"\n{'📝 DRY RUN' if dry_run else '📤 SENDING'} - Bulk message to {len(users)} users")
        print(f"   Delay between messages: {delay}s")
        print(f"   Estimated time: {len(users) * delay / 60:.1f} minutes")
        
        if dry_run:
            print("\n⚠️ DRY RUN MODE - No messages will be sent")
            print("   Set dry_run=False to actually send messages")
        
        successful = 0
        failed = 0
        
        for i, user in enumerate(users, 1):
            try:
                # Personalize message
                message = message_template.format(
                    first_name=user.get('first_name', 'there'),
                    last_name=user.get('last_name', ''),
                    username=user.get('username', 'User')
                )
                
                if dry_run:
                    print(f"   [{i}/{len(users)}] Would send to: {user.get('first_name', 'Unknown')}")
                else:
                    success = await self.send_message_to_user(user['id'], message, delay)
                    if success:
                        successful += 1
                        print(f"   ✅ [{i}/{len(users)}] Sent to: {user.get('first_name', 'Unknown')}")
                    else:
                        failed += 1
                        print(f"   ❌ [{i}/{len(users)}] Failed: {user.get('first_name', 'Unknown')}")
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Error for user {i}: {e}")
        
        print(f"\n📊 Results: {successful} successful, {failed} failed")
    
    async def search_messages(self, channel, keywords: List[str], limit: int = 100) -> List[Dict]:
        """
        Search for messages containing specific keywords
        
        Args:
            channel: Channel entity
            keywords: List of keywords to search for
            limit: Maximum number of messages to check
            
        Returns:
            List of matching messages
        """
        print(f"\n🔍 Searching for keywords: {', '.join(keywords)}")
        print(f"   Checking last {limit} messages...")
        
        found_messages = []
        
        try:
            async for message in self.client.iter_messages(channel, limit=limit):
                if message.text:
                    message_lower = message.text.lower()
                    
                    # Check if any keyword is in the message
                    matching_keywords = [kw for kw in keywords if kw.lower() in message_lower]
                    
                    if matching_keywords:
                        found_messages.append({
                            'id': message.id,
                            'date': str(message.date),
                            'text': message.text,
                            'sender_id': message.sender_id,
                            'matching_keywords': matching_keywords,
                            'link': f"https://t.me/c/{channel.id}/{message.id}"
                        })
        
        except Exception as e:
            print(f"❌ Error searching messages: {e}")
        
        print(f"✅ Found {len(found_messages)} messages with keywords")
        return found_messages
    
    async def find_active_users(self, channel, days: int = 30, limit: int = 500) -> List[Dict]:
        """
        Find users who have been active in the channel recently
        
        Args:
            channel: Channel entity
            days: Number of days to look back
            limit: Number of messages to check
            
        Returns:
            List of active user dictionaries
        """
        print(f"\n🔍 Finding active users (last {days} days)...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        active_user_ids = set()
        
        try:
            async for message in self.client.iter_messages(channel, limit=limit):
                if message.date > cutoff_date and message.sender_id:
                    active_user_ids.add(message.sender_id)
        
        except Exception as e:
            print(f"❌ Error finding active users: {e}")
            return []
        
        print(f"   Found {len(active_user_ids)} unique active users")
        
        # Get user details
        active_users = []
        for user_id in active_user_ids:
            try:
                user = await self.client.get_entity(user_id)
                if not user.bot:
                    active_users.append({
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    })
            except:
                continue
        
        print(f"✅ Retrieved details for {len(active_users)} active users")
        return active_users
    
    async def monitor_channel(self, channel_identifier: str, keywords: List[str], duration: int = 60):
        """
        Monitor channel for new messages with keywords in real-time
        
        Args:
            channel_identifier: Channel username or ID
            keywords: Keywords to monitor
            duration: How long to monitor (seconds)
        """
        print(f"\n👀 Monitoring channel for {duration} seconds...")
        print(f"   Keywords: {', '.join(keywords)}")
        
        found_count = 0
        
        @self.client.on(events.NewMessage(chats=channel_identifier))
        async def handler(event):
            nonlocal found_count
            if event.message.text:
                message_lower = event.message.text.lower()
                if any(kw.lower() in message_lower for kw in keywords):
                    found_count += 1
                    print(f"\n🎯 Found message #{found_count}:")
                    print(f"   Date: {event.message.date}")
                    print(f"   Text: {event.message.text[:100]}...")
                    
                    # Save to file
                    with open('monitored_resources.txt', 'a', encoding='utf-8') as f:
                        f.write(f"\n{'='*50}\n")
                        f.write(f"Date: {event.message.date}\n")
                        f.write(f"Message: {event.message.text}\n")
        
        # Run for specified duration
        await asyncio.sleep(duration)
        print(f"\n✅ Monitoring complete. Found {found_count} matching messages")
    
    def save_to_json(self, data: any, filename: str):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved data to {filename}")
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")


async def main():
    """Main execution function"""
    
    print("=" * 60)
    print("  Telegram Channel Automation Tool")
    print("=" * 60)
    
    # Load credentials from environment variables
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    PHONE = os.getenv('TELEGRAM_PHONE')
    
    # Check if credentials are set
    if not all([API_ID, API_HASH, PHONE]):
        print("\n❌ Error: Missing credentials!")
        print("\nPlease set the following environment variables:")
        print("  - TELEGRAM_API_ID")
        print("  - TELEGRAM_API_HASH")
        print("  - TELEGRAM_PHONE")
        print("\nOr create a .env file with these values.")
        print("\nGet your API credentials from: https://my.telegram.org/apps")
        return
    
    # Configuration
    CHANNEL_USERNAME = '@your_channel_username'  # Change this
    KEYWORDS = ['available', 'free', 'open', 'resource', 'vacancy']
    
    # Initialize bot
    bot = TelegramChannelBot(API_ID, API_HASH, PHONE)
    
    try:
        # Connect
        await bot.connect()
        
        # Get channel
        print("\n" + "="*60)
        channel = await bot.get_channel(CHANNEL_USERNAME)
        
        if not channel:
            print("❌ Could not access channel. Please check the username.")
            return
        
        # Example 1: Search for resources in channel history
        print("\n" + "="*60)
        print("EXAMPLE 1: Searching for Resources")
        print("="*60)
        resources = await bot.search_messages(channel, KEYWORDS, limit=50)
        
        if resources:
            bot.save_to_json(resources, 'found_resources.json')
            print("\nSample results:")
            for resource in resources[:3]:
                print(f"\n  📋 {resource['date']}")
                print(f"     {resource['text'][:100]}...")
        
        # Example 2: Find active users
        print("\n" + "="*60)
        print("EXAMPLE 2: Finding Active Users")
        print("="*60)
        active_users = await bot.find_active_users(channel, days=7, limit=100)
        
        if active_users:
            bot.save_to_json(active_users, 'active_users.json')
            print(f"\nSample active users:")
            for user in active_users[:5]:
                print(f"  👤 {user['first_name']} (@{user.get('username', 'N/A')})")
        
        # Example 3: Get channel members (requires permissions)
        print("\n" + "="*60)
        print("EXAMPLE 3: Getting Channel Members")
        print("="*60)
        print("⚠️ Note: This requires admin permissions in most channels")
        
        # Uncomment to try getting members:
        # members = await bot.get_channel_members(channel, max_members=50)
        # bot.save_to_json(members, 'channel_members.json')
        
        # Example 4: Send bulk messages (DRY RUN)
        print("\n" + "="*60)
        print("EXAMPLE 4: Bulk Messaging (DRY RUN)")
        print("="*60)
        
        if active_users:
            message_template = """
Hello {first_name}!

This is an automated message example.
This is a DRY RUN - no actual message is being sent.

Best regards
            """.strip()
            
            # DRY RUN - won't actually send messages
            await bot.send_bulk_messages(
                active_users[:5],  # Only first 5 users
                message_template,
                delay=10,
                dry_run=True  # Set to False to actually send
            )
        
        # Example 5: Real-time monitoring (optional)
        # Uncomment to enable:
        # print("\n" + "="*60)
        # print("EXAMPLE 5: Real-time Monitoring")
        # print("="*60)
        # await bot.monitor_channel(CHANNEL_USERNAME, KEYWORDS, duration=60)
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        await bot.disconnect()
        print("\n👋 Script finished!")


if __name__ == '__main__':
    # Run the main function
    asyncio.run(main())
