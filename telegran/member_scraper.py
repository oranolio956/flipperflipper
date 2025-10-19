"""
Member Scraper & Outreach Tool
⚠️ EXTREME RISK - USE AT YOUR OWN RISK ⚠️

Scrapes members from a channel and allows outreach.
"""

import os
import json
import logging
import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set
from dotenv import load_dotenv

from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, User
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, ChatWriteForbiddenError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('member_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MemberScraper:
    """Scrape members from channels and perform outreach"""
    
    def __init__(self):
        """Initialize scraper"""
        # Telegram credentials
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone = os.getenv('PHONE_NUMBER')
        
        if not all([self.api_id, self.api_hash, self.phone]):
            raise ValueError("Missing API_ID, API_HASH, or PHONE_NUMBER in .env")
        
        # Initialize client
        self.client = TelegramClient('scraper_session', self.api_id, self.api_hash)
        
        # Load config
        self.config = self.load_config()
        
        # State
        self.scraped_members: List[Dict] = []
        self.contacted_users: Set[int] = set()
        self.failed_users: Set[int] = set()
        
        # Rate limiting (VERY CONSERVATIVE)
        self.messages_sent_today = 0
        self.max_messages_per_day = self.config.get('max_messages_per_day', 20)
        self.max_messages_per_hour = self.config.get('max_messages_per_hour', 3)
        self.messages_this_hour = 0
        self.last_message_time = None
        
        # Load state
        self.load_state()
    
    def load_config(self) -> dict:
        """Load configuration"""
        default_config = {
            'source_channels': [],  # Channels to scrape from
            'target_channel': None,  # Channel to invite to (optional)
            'outreach_message': 'Hey {username}! I found your profile interesting. Would you like to check out {channel}?',
            'delay_between_messages_min': 300,  # 5 minutes
            'delay_between_messages_max': 900,  # 15 minutes
            'max_messages_per_day': 20,  # VERY low
            'max_messages_per_hour': 3,  # VERY low
            'scrape_limit': 1000,  # Max members to scrape
            'enable_typing': False,  # Typing = more obvious
            'enable_read_receipt': False,  # Don't mark as read
            'filter_bots': True,  # Skip bots
            'filter_deleted': True,  # Skip deleted accounts
            'min_account_age_days': 7,  # Only message accounts older than 7 days
        }
        
        if os.path.exists('scraper_config.json'):
            try:
                with open('scraper_config.json', 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration"""
        try:
            with open('scraper_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def load_state(self):
        """Load state from file"""
        if os.path.exists('scraper_state.json'):
            try:
                with open('scraper_state.json', 'r') as f:
                    state = json.load(f)
                    self.scraped_members = state.get('scraped_members', [])
                    self.contacted_users = set(state.get('contacted_users', []))
                    self.failed_users = set(state.get('failed_users', []))
                    logger.info(f"📥 Loaded state: {len(self.scraped_members)} scraped, {len(self.contacted_users)} contacted")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save state to file"""
        try:
            state = {
                'scraped_members': self.scraped_members,
                'contacted_users': list(self.contacted_users),
                'failed_users': list(self.failed_users),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            with open('scraper_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    async def scrape_channel(self, channel_username: str) -> List[Dict]:
        """
        Scrape members from a channel
        
        Args:
            channel_username: Channel username (e.g., 'aquisitionpublic')
            
        Returns:
            List of member dictionaries
        """
        logger.info(f"🔍 Scraping channel: {channel_username}")
        
        try:
            # Get channel entity
            channel = await self.client.get_entity(channel_username)
            
            # Check if we can access participants
            logger.info(f"📊 Channel: {channel.title}")
            
            members = []
            offset = 0
            limit = 100  # Fetch 100 at a time
            scrape_limit = self.config['scrape_limit']
            
            while len(members) < scrape_limit:
                try:
                    # Get participants
                    participants = await self.client(GetParticipantsRequest(
                        channel=channel,
                        filter=ChannelParticipantsSearch(''),
                        offset=offset,
                        limit=limit,
                        hash=0
                    ))
                    
                    if not participants.users:
                        logger.info("✅ Reached end of members list")
                        break
                    
                    # Process users
                    for user in participants.users:
                        if not isinstance(user, User):
                            continue
                        
                        # Apply filters
                        if self.config['filter_bots'] and user.bot:
                            continue
                        
                        if self.config['filter_deleted'] and user.deleted:
                            continue
                        
                        # Extract user info
                        member_info = {
                            'id': user.id,
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone': user.phone,
                            'is_bot': user.bot,
                            'is_verified': user.verified,
                            'is_premium': user.premium,
                            'scraped_at': datetime.now(timezone.utc).isoformat(),
                            'source_channel': channel_username
                        }
                        
                        members.append(member_info)
                    
                    offset += len(participants.users)
                    logger.info(f"📊 Scraped {len(members)} members so far...")
                    
                    # Rate limit: Wait between requests
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except FloodWaitError as e:
                    logger.warning(f"⏰ FloodWait: {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                    continue
                
                except Exception as e:
                    logger.error(f"❌ Error fetching participants: {e}")
                    break
            
            logger.info(f"✅ Scraped {len(members)} members from {channel_username}")
            return members
            
        except Exception as e:
            logger.error(f"❌ Error scraping channel: {e}")
            return []
    
    async def can_message_user(self, user_id: int) -> bool:
        """Check if we can message a user"""
        # Already contacted?
        if user_id in self.contacted_users:
            return False
        
        # Already failed?
        if user_id in self.failed_users:
            return False
        
        # Rate limits
        if self.messages_sent_today >= self.max_messages_per_day:
            logger.warning(f"⚠️ Daily limit reached ({self.max_messages_per_day})")
            return False
        
        if self.messages_this_hour >= self.max_messages_per_hour:
            logger.warning(f"⚠️ Hourly limit reached ({self.max_messages_per_hour})")
            return False
        
        return True
    
    async def send_outreach_message(self, member: Dict) -> bool:
        """
        Send outreach message to a member
        
        Args:
            member: Member dictionary from scraping
            
        Returns:
            True if sent successfully
        """
        user_id = member['id']
        username = member.get('username') or member.get('first_name') or 'there'
        
        # Check if we can message
        if not await self.can_message_user(user_id):
            return False
        
        try:
            # Format message
            message = self.config['outreach_message'].format(
                username=username,
                channel=self.config.get('target_channel', 'our community')
            )
            
            # Simulate human delay
            delay = random.uniform(
                self.config['delay_between_messages_min'],
                self.config['delay_between_messages_max']
            )
            logger.info(f"⏰ Waiting {delay:.1f}s before messaging {username}...")
            await asyncio.sleep(delay)
            
            # Optional: Show typing
            if self.config['enable_typing']:
                async with self.client.action(user_id, 'typing'):
                    await asyncio.sleep(random.uniform(2, 5))
            
            # Send message
            await self.client.send_message(user_id, message)
            
            # Track success
            self.contacted_users.add(user_id)
            self.messages_sent_today += 1
            self.messages_this_hour += 1
            self.last_message_time = datetime.now(timezone.utc)
            
            logger.info(f"✅ Messaged {username} (Today: {self.messages_sent_today}/{self.max_messages_per_day})")
            
            # Save state
            self.save_state()
            
            return True
            
        except UserPrivacyRestrictedError:
            logger.warning(f"⚠️ {username} has privacy settings enabled")
            self.failed_users.add(user_id)
            self.save_state()
            return False
            
        except FloodWaitError as e:
            logger.error(f"🚨 FLOOD WAIT: {e.seconds} seconds!")
            await asyncio.sleep(e.seconds)
            return False
            
        except ChatWriteForbiddenError:
            logger.warning(f"⚠️ Can't message {username} (forbidden)")
            self.failed_users.add(user_id)
            self.save_state()
            return False
            
        except Exception as e:
            logger.error(f"❌ Error messaging {username}: {e}")
            self.failed_users.add(user_id)
            self.save_state()
            return False
    
    async def invite_to_channel(self, member: Dict, target_channel: str) -> bool:
        """
        Invite member to a channel
        
        Args:
            member: Member dictionary
            target_channel: Target channel username
            
        Returns:
            True if invited successfully
        """
        user_id = member['id']
        username = member.get('username') or member.get('first_name') or 'there'
        
        try:
            # Get channel
            channel = await self.client.get_entity(target_channel)
            
            # Invite user
            await self.client.invite_to_channel(channel, [user_id])
            
            logger.info(f"✅ Invited {username} to {target_channel}")
            self.contacted_users.add(user_id)
            self.save_state()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inviting {username}: {e}")
            self.failed_users.add(user_id)
            self.save_state()
            return False
    
    async def run_scraper(self):
        """Scrape all configured channels"""
        logger.info("🚀 Starting member scraper...")
        
        source_channels = self.config.get('source_channels', [])
        
        if not source_channels:
            logger.error("❌ No source channels configured!")
            logger.info("Edit scraper_config.json and add channels to scrape")
            return
        
        for channel in source_channels:
            logger.info(f"📡 Scraping {channel}...")
            members = await self.scrape_channel(channel)
            
            # Add to scraped members
            self.scraped_members.extend(members)
            
            # Save state
            self.save_state()
            
            logger.info(f"✅ Total scraped: {len(self.scraped_members)} members")
            
            # Wait between channels
            await asyncio.sleep(random.uniform(30, 60))
    
    async def run_outreach(self):
        """Send outreach messages to scraped members"""
        logger.info("📨 Starting outreach campaign...")
        
        if not self.scraped_members:
            logger.error("❌ No scraped members! Run scraper first.")
            return
        
        # Filter uncontacted members
        uncontacted = [
            m for m in self.scraped_members
            if m['id'] not in self.contacted_users and m['id'] not in self.failed_users
        ]
        
        logger.info(f"📊 {len(uncontacted)} members to contact")
        
        # Shuffle to avoid patterns
        random.shuffle(uncontacted)
        
        for member in uncontacted:
            # Check daily limit
            if self.messages_sent_today >= self.max_messages_per_day:
                logger.warning(f"🛑 Daily limit reached. Stopping for today.")
                break
            
            # Send message
            await self.send_outreach_message(member)
        
        logger.info("✅ Outreach campaign complete!")
        logger.info(f"📊 Contacted: {len(self.contacted_users)}, Failed: {len(self.failed_users)}")
    
    async def reset_hourly_counter(self):
        """Reset hourly message counter"""
        while True:
            await asyncio.sleep(3600)  # 1 hour
            self.messages_this_hour = 0
            logger.info("🔄 Hourly counter reset")
    
    async def reset_daily_counter(self):
        """Reset daily message counter"""
        while True:
            await asyncio.sleep(86400)  # 24 hours
            self.messages_sent_today = 0
            logger.info("🔄 Daily counter reset")
    
    async def start(self):
        """Start the scraper"""
        await self.client.start(phone=self.phone)
        logger.info("✅ Connected to Telegram")
        
        # Start background tasks
        asyncio.create_task(self.reset_hourly_counter())
        asyncio.create_task(self.reset_daily_counter())
        
        # Main menu
        while True:
            print("\n" + "="*60)
            print("🔍 MEMBER SCRAPER & OUTREACH TOOL")
            print("="*60)
            print("1. Scrape members from channels")
            print("2. Send outreach messages")
            print("3. View statistics")
            print("4. Configure settings")
            print("5. Export scraped members")
            print("6. Exit")
            print("="*60)
            
            choice = input("Choose option: ").strip()
            
            if choice == '1':
                await self.run_scraper()
            elif choice == '2':
                await self.run_outreach()
            elif choice == '3':
                self.show_statistics()
            elif choice == '4':
                await self.configure()
            elif choice == '5':
                self.export_members()
            elif choice == '6':
                logger.info("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
    
    def show_statistics(self):
        """Show statistics"""
        print("\n📊 STATISTICS")
        print("="*60)
        print(f"Total scraped: {len(self.scraped_members)}")
        print(f"Successfully contacted: {len(self.contacted_users)}")
        print(f"Failed contacts: {len(self.failed_users)}")
        print(f"Pending: {len(self.scraped_members) - len(self.contacted_users) - len(self.failed_users)}")
        print(f"Messages today: {self.messages_sent_today}/{self.max_messages_per_day}")
        print(f"Messages this hour: {self.messages_this_hour}/{self.max_messages_per_hour}")
        print("="*60)
    
    async def configure(self):
        """Interactive configuration"""
        print("\n⚙️ CONFIGURATION")
        print("="*60)
        
        # Source channels
        channels = input(f"Source channels (comma-separated) [{','.join(self.config.get('source_channels', []))}]: ").strip()
        if channels:
            self.config['source_channels'] = [c.strip() for c in channels.split(',')]
        
        # Target channel
        target = input(f"Target channel (optional) [{self.config.get('target_channel', '')}]: ").strip()
        if target:
            self.config['target_channel'] = target
        
        # Outreach message
        print(f"\nCurrent message:\n{self.config['outreach_message']}")
        new_message = input("New outreach message (or press Enter to keep): ").strip()
        if new_message:
            self.config['outreach_message'] = new_message
        
        # Rate limits
        daily = input(f"Max messages per day [{self.config['max_messages_per_day']}]: ").strip()
        if daily and daily.isdigit():
            self.config['max_messages_per_day'] = int(daily)
        
        hourly = input(f"Max messages per hour [{self.config['max_messages_per_hour']}]: ").strip()
        if hourly and hourly.isdigit():
            self.config['max_messages_per_hour'] = int(hourly)
        
        # Save
        self.save_config()
        print("✅ Configuration saved!")
    
    def export_members(self):
        """Export scraped members to CSV"""
        try:
            import csv
            
            filename = f"scraped_members_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if not self.scraped_members:
                    print("❌ No members to export")
                    return
                
                writer = csv.DictWriter(f, fieldnames=self.scraped_members[0].keys())
                writer.writeheader()
                writer.writerows(self.scraped_members)
            
            print(f"✅ Exported to {filename}")
            
        except Exception as e:
            print(f"❌ Error exporting: {e}")


async def main():
    """Main function"""
    print("\n" + "="*60)
    print("⚠️  EXTREME WARNING ⚠️")
    print("="*60)
    print("This tool:")
    print("- Scrapes channel members")
    print("- Sends unsolicited messages")
    print("- VIOLATES Telegram ToS")
    print("- HIGH RISK of account ban")
    print("- Could be considered spam/harassment")
    print("="*60)
    print("\nUse at your own risk!")
    confirm = input("Type 'I UNDERSTAND THE RISKS' to continue: ").strip()
    
    if confirm != "I UNDERSTAND THE RISKS":
        print("❌ Aborted")
        return
    
    try:
        scraper = MemberScraper()
        await scraper.start()
    except KeyboardInterrupt:
        logger.info("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
