"""
Telegran Userbot - Stealth Auto-Welcome & Help System
Uses YOUR personal Telegram account to send messages
"""

import os
import json
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple
from dotenv import load_dotenv

from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat

from database import Database
from flood_wait_handler import FloodWaitHandler, RetryQueue
from message_validator import safe_format_message, validator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('telegran.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StealthUserbot:
    """Userbot with advanced anti-detection features"""
    
    def __init__(self):
        """Initialize the userbot with stealth configuration"""
        self.config = self.load_config()
        
        # Initialize database for persistence
        self.db = Database()
        
        # Initialize flood wait handler
        self.flood_handler = FloodWaitHandler()
        self.retry_queue = RetryQueue(self.flood_handler)
        
        # Load welcomed users from database
        self.welcomed_users: Set[int] = self.db.get_welcomed_users()
        
        # Counters
        self.message_count = 0  # Hourly counter (resets every hour)
        self.daily_message_count = self.db.get_daily_count()  # From database
        self.session_start = datetime.now()
        self.last_reset_date = datetime.now().date()
        
        logger.info(f"📊 Loaded from database: {len(self.welcomed_users)} welcomed users, {self.daily_message_count} messages today")
        
        # Get credentials
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone = os.getenv('PHONE_NUMBER')
        
        if not all([self.api_id, self.api_hash, self.phone]):
            raise ValueError("API_ID, API_HASH, and PHONE_NUMBER required in .env!")
        
        # Initialize Telegram client
        self.client = TelegramClient('userbot_session', int(self.api_id), self.api_hash)
    
    def validate_config(self, config: dict) -> tuple[bool, str]:
        """Validate configuration values"""
        # Check welcome messages
        if not config.get('welcome_messages') or len(config['welcome_messages']) == 0:
            return False, "welcome_messages cannot be empty"
        
        # Check help messages
        if not config.get('help_messages') or len(config['help_messages']) == 0:
            return False, "help_messages cannot be empty"
        
        # Check stealth settings
        stealth = config.get('stealth', {})
        
        if stealth.get('max_messages_per_hour', 0) <= 0:
            return False, "max_messages_per_hour must be positive"
        
        if stealth.get('max_messages_per_hour', 0) > 30:
            return False, "max_messages_per_hour too high (Telegram limit ~30/min)"
        
        if stealth.get('response_probability', 0) <= 0 or stealth.get('response_probability', 0) > 1:
            return False, "response_probability must be between 0 and 1"
        
        if stealth.get('welcome_delay_min', 0) > stealth.get('welcome_delay_max', 0):
            return False, "welcome_delay_min cannot be greater than welcome_delay_max"
        
        # Check target group
        if not config.get('target_group'):
            return False, "target_group must be set"
        
        return True, "OK"
    
    def load_config(self) -> dict:
        """Load stealth configuration"""
        default_config = {
            "welcome_messages": [
                "Hey {username}! Welcome to the group! 👋 Glad you're here!",
                "Hi {username}! Great to have you join us! Feel free to ask if you need anything 😊",
                "Welcome {username}! 🎉 Hope you enjoy the community!",
                "Hey there {username}! Welcome! Don't hesitate to reach out if you have questions 💬"
            ],
            "help_messages": [
                "Hey {username}! I saw your message - what do you need help with?",
                "Hi {username}! I can help with that. What specifically are you looking for?",
                "Hey {username}! I'm around if you need assistance. What's up?",
                "Hi {username}! Let me know how I can help you out 😊"
            ],
            "help_keywords": [
                "help", "support", "how do i", "how to", "question",
                "need assistance", "can someone help", "anyone help",
                "issue", "problem", "stuck", "confused"
            ],
            
            # STEALTH SETTINGS - Anti-Detection
            "stealth": {
                "welcome_delay_min": 45,      # Minimum seconds before welcome
                "welcome_delay_max": 180,     # Maximum seconds before welcome
                "help_delay_min": 10,         # Minimum seconds before help response
                "help_delay_max": 60,         # Maximum seconds before help response
                "typing_time_min": 2,         # Minimum typing indicator time
                "typing_time_max": 5,         # Maximum typing indicator time
                "cooldown_hours": 24,         # Don't message same user for 24h
                "max_messages_per_hour": 8,   # Limit messages per hour
                "max_messages_per_day": 50,   # Daily limit
                "response_probability": 0.85, # Respond to 85% of triggers (not 100%)
                "active_hours_start": 8,      # Be more active after 8 AM
                "active_hours_end": 23,       # Be less active after 11 PM
                "night_response_probability": 0.3  # Lower response rate at night
            },
            
            "target_group": "cupidbotg",      # Group username or ID
            "enable_welcome": True,
            "enable_help": True,
            "stealth_mode": True
        }
        
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    merged = {**default_config, **config}
                    
                    # Validate merged config
                    valid, error = self.validate_config(merged)
                    if not valid:
                        logger.error(f"❌ Invalid config.json: {error}")
                        logger.error("   Using default config instead")
                        return default_config
                    
                    return merged
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in config.json: {e}")
            logger.error("   Using default config instead")
        except Exception as e:
            logger.warning(f"Could not load config.json: {e}. Using defaults.")
        
        # Save default config
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def should_respond_now(self, is_welcome: bool = True) -> Tuple[bool, str]:
        """Determine if bot should respond based on stealth settings"""
        stealth = self.config['stealth']
        
        # Check hourly rate limit
        if self.message_count >= stealth['max_messages_per_hour']:
            logger.info("⏸️  Hourly rate limit reached, skipping response")
            return False, "hourly_limit"
        
        # Check daily rate limit
        if self.daily_message_count >= stealth['max_messages_per_day']:
            logger.info("⏸️  Daily rate limit reached, skipping response")
            return False, "daily_limit"
        
        # Check time of day
        current_hour = datetime.now().hour
        is_active_hours = stealth['active_hours_start'] <= current_hour <= stealth['active_hours_end']
        
        # Adjust probability based on time
        if is_active_hours:
            probability = stealth['response_probability']
        else:
            probability = stealth['night_response_probability']
            logger.info(f"🌙 Night time - reduced response probability: {probability}")
        
        # Random chance to skip (make it look human)
        # BUT: For welcomes, we ALWAYS welcome (just delay randomly)
        # Only use probability for help messages
        if not is_welcome:
            if random.random() > probability:
                logger.info(f"🎲 Randomly skipping help response (stealth mode)")
                return False, "probability"
        
        return True, "ok"
    
    async def simulate_human_delay(self, min_delay: int, max_delay: int):
        """Simulate human-like random delay"""
        delay = random.uniform(min_delay, max_delay)
        logger.info(f"⏰ Waiting {delay:.1f}s (human-like delay)")
        await asyncio.sleep(delay)
    
    async def simulate_typing(self, chat):
        """Show typing indicator like a human"""
        stealth = self.config['stealth']
        
        # Skip typing if disabled
        if stealth['typing_time_min'] == 0 and stealth['typing_time_max'] == 0:
            return
        
        typing_time = random.uniform(
            stealth['typing_time_min'],
            stealth['typing_time_max']
        )
        
        logger.info(f"⌨️  Showing typing for {typing_time:.1f}s...")
        async with self.client.action(chat, 'typing'):
            await asyncio.sleep(typing_time)
    
    def get_random_message(self, message_list: list, username: str, is_welcome: bool = True) -> str:
        """Get message - either simple mode (same every time) or random variation"""
        
        # Check if simple mode is enabled (one copy/paste message)
        if self.config.get('simple_mode', False):
            if is_welcome:
                message = self.config.get('simple_welcome_message', message_list[0])
            else:
                message = self.config.get('simple_help_message', message_list[0])
        else:
            # Random variation mode
            message = random.choice(message_list)
        
        return message.format(username=username)
    
    async def handle_new_member(self, event):
        """Handle new member joins with stealth"""
        try:
            if not self.config['enable_welcome']:
                return
            
            # Check if this is the target group
            chat = await event.get_chat()
            if not self.is_target_group(chat):
                return
            
            # Get new member info
            user = await event.get_user()
            
            if not isinstance(user, User) or user.bot:
                return
            
            user_id = user.id
            
            # Don't welcome myself!
            if user_id == self.my_id:
                logger.info("Skipping self-join event")
                return
            
            username = user.first_name or "there"
            
            # Check if already welcomed
            if user_id in self.welcomed_users:
                logger.info(f"Already welcomed {username}")
                return
            
            # Check if should respond (stealth mode)
            can_respond, reason = self.should_respond_now(is_welcome=True)
            if not can_respond:
                logger.warning(f"⚠️  Cannot welcome {username} due to {reason} - adding to pending queue")
                self.db.add_pending_welcome(user_id, username, reason)
                return
            
            logger.info(f"👤 New member: {username} ({user_id})")
            
            # Human-like delay before welcoming
            await self.simulate_human_delay(
                self.config['stealth']['welcome_delay_min'],
                self.config['stealth']['welcome_delay_max']
            )
            
            # Show typing indicator
            await self.simulate_typing(event.chat_id)
            
            # Get and validate welcome message
            template = self.get_random_message(
                self.config['welcome_messages'],
                username,
                is_welcome=True
            )
            
            # Sanitize and validate
            message = safe_format_message(template, username)
            
            # Send with flood wait protection
            result = await self.flood_handler.execute_with_flood_protection(
                self.client.send_message,
                event.chat_id,
                message
            )
            
            if result is None:
                # Failed even after retries - add to queue
                logger.warning(f"⚠️  Failed to send welcome, adding to retry queue")
                self.retry_queue.add(
                    self.client.send_message,
                    (event.chat_id, message),
                    {},
                    priority=1
                )
                return
            
            # Mark as welcomed in memory AND database
            self.welcomed_users.add(user_id)
            self.db.add_welcomed(user_id)
            
            # Update counters
            self.message_count += 1
            self.daily_message_count += 1
            self.db.increment_daily_count()
            
            # Remove from pending if they were there
            self.db.remove_pending_welcome(user_id)
            
            logger.info(f"✅ Welcomed {username} (Total: {len(self.welcomed_users)}, Today: {self.daily_message_count})")
            
        except Exception as e:
            logger.error(f"Error handling new member: {e}", exc_info=True)
    
    async def handle_message(self, event):
        """Handle messages and detect help requests"""
        try:
            if not self.config['enable_help']:
                return
            
            # Check if message has text
            if not event.message or not event.message.text:
                return
            
            # Check if this is the target group
            chat = await event.get_chat()
            if not self.is_target_group(chat):
                return
            
            # Don't respond to own messages
            if event.sender_id == (await self.client.get_me()).id:
                return
            
            message_text = event.message.text.lower()
            sender = await event.get_sender()
            
            if not isinstance(sender, User):
                return
            
            user_id = sender.id
            username = sender.first_name or "there"
            
            # Check for help keywords
            is_help_request = any(
                keyword in message_text 
                for keyword in self.config['help_keywords']
            )
            
            if not is_help_request:
                return
            
            # Check cooldown (from database)
            if self.db.is_on_cooldown(user_id, self.config['stealth']['cooldown_hours']):
                logger.info(f"Cooldown active for {username}")
                return
            
            # Check if should respond (stealth mode) - help can be skipped randomly
            can_respond, reason = self.should_respond_now(is_welcome=False)
            if not can_respond:
                logger.info(f"Stealth mode: Skipping help response for {username} ({reason})")
                return
            
            logger.info(f"💬 Help request from {username}: {message_text[:50]}...")
            
            # Human-like delay before responding
            await self.simulate_human_delay(
                self.config['stealth']['help_delay_min'],
                self.config['stealth']['help_delay_max']
            )
            
            # Show typing indicator
            await self.simulate_typing(event.chat_id)
            
            # Get and validate help message
            template = self.get_random_message(
                self.config['help_messages'],
                username,
                is_welcome=False
            )
            
            # Sanitize and validate
            help_text = safe_format_message(template, username)
            
            # Send with flood wait protection
            result = await self.flood_handler.execute_with_flood_protection(
                event.reply,
                help_text
            )
            
            if result is None:
                # Failed - add to queue
                logger.warning(f"⚠️  Failed to send help response, adding to retry queue")
                self.retry_queue.add(
                    event.reply,
                    (help_text,),
                    {},
                    priority=0
                )
                return
            
            # Save cooldown to database
            self.db.add_help_cooldown(user_id)
            
            # Update counters
            self.message_count += 1
            self.daily_message_count += 1
            self.db.increment_daily_count()
            
            logger.info(f"✅ Responded to {username} (Today: {self.daily_message_count})")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    async def reset_hourly_counter(self):
        """Reset message counter every hour"""
        while True:
            await asyncio.sleep(3600)  # 1 hour
            old_count = self.message_count
            self.message_count = 0
            
            # Check if we need to reset daily counter
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                logger.info(f"🔄 Daily reset - Sent {self.daily_message_count} messages yesterday")
                self.daily_message_count = 0
                self.last_reset_date = current_date
            
            logger.info(f"🔄 Hourly reset - Sent {old_count} messages last hour | Daily total: {self.daily_message_count}")
    
    def is_target_group(self, chat) -> bool:
        """Check if the chat is the target group"""
        target = self.config['target_group']
        
        # Check by username
        if hasattr(chat, 'username') and chat.username:
            if chat.username.lower() == target.lower():
                return True
        
        # Check by title (partial match)
        if hasattr(chat, 'title') and chat.title:
            if target.lower() in chat.title.lower():
                return True
        
        # Check by ID (if target is a number)
        try:
            target_id = int(target)
            if chat.id == target_id:
                return True
        except ValueError:
            pass
        
        return False
    
    async def process_pending_welcomes(self):
        """Process pending welcomes queue - try to welcome people we missed"""
        while True:
            await asyncio.sleep(600)  # Check every 10 minutes
            
            pending = self.db.get_pending_welcomes()
            if not pending:
                continue
            
            logger.info(f"🗓️  Processing {len(pending)} pending welcomes...")
            
            for user_data in pending[:3]:  # Try max 3 at a time
                user_id = user_data['user_id']
                username = user_data['username']
                
                # Skip if already welcomed
                if user_id in self.welcomed_users:
                    self.db.remove_pending_welcome(user_id)
                    continue
                
                # Check if we can send now
                can_respond, reason = self.should_respond_now(is_welcome=True)
                if not can_respond:
                    logger.info(f"⏸️  Still can't welcome {username} ({reason})")
                    continue
                
                try:
                    # Try to get the chat and send welcome
                    target_group = self.config['target_group']
                    
                    # Get message
                    message = self.get_random_message(
                        self.config['welcome_messages'],
                        username,
                        is_welcome=True
                    )
                    
                    # Send to group by username/id
                    await self.client.send_message(target_group, message)
                    
                    # Mark as welcomed
                    self.welcomed_users.add(user_id)
                    self.db.add_welcomed(user_id)
                    self.db.remove_pending_welcome(user_id)
                    
                    # Update counters
                    self.message_count += 1
                    self.daily_message_count += 1
                    self.db.increment_daily_count()
                    
                    logger.info(f"✅ Processed pending welcome for {username}")
                    
                    # Small delay between pending messages
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error processing pending welcome for {username}: {e}")
    
    async def cleanup_database(self):
        """Periodic database cleanup"""
        while True:
            await asyncio.sleep(3600)  # Every hour
            
            # Clean old cooldowns
            self.db.clean_old_cooldowns(hours=48)
            
            logger.info("🧹 Database cleanup completed")
    
    async def print_stats(self):
        """Print statistics every 30 minutes"""
        while True:
            await asyncio.sleep(1800)  # 30 minutes
            uptime = datetime.now() - self.session_start
            db_stats = self.db.get_stats()
            
            logger.info(
                f"📊 Stats - Welcomed: {db_stats['total_welcomed']} | "
                f"Cooldowns: {db_stats['active_cooldowns']} | "
                f"Messages/hr: {self.message_count}/{self.config['stealth']['max_messages_per_hour']} | "
                f"Today: {db_stats['messages_today']}/{self.config['stealth']['max_messages_per_day']} | "
                f"Pending: {db_stats['pending_welcomes']} | "
                f"Uptime: {uptime}"
            )
    
    async def start(self):
        """Start the userbot"""
        logger.info("🚀 Starting Telegran Userbot (STEALTH MODE)...")
        
        # Connect and authenticate
        await self.client.start(phone=self.phone)
        
        me = await self.client.get_me()
        self.my_id = me.id  # Store for later checks
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        logger.info(f"🎯 Monitoring group: {self.config['target_group']}")
        
        # Verify user is in target group
        await self.verify_target_group()
        
        # Register event handlers - ONLY for target group!
        target_chat_id = self.target_group_id if hasattr(self, 'target_group_id') else None
        
        @self.client.on(events.ChatAction(chats=[target_chat_id] if target_chat_id else None))
        async def chat_action_handler(event):
            # Handle group migration (group -> supergroup)
            if event.migrated_to:
                old_id = event.chat_id
                new_id = event.migrated_to.id
                logger.warning(f"🔄 Group migrated! Old ID: {old_id}, New ID: {new_id}")
                logger.warning(f"⚠️  Update config.json with new target_group: {new_id}")
                # Update our cached ID
                self.target_group_id = new_id
                return
            
            if event.user_joined or event.user_added:
                await self.handle_new_member(event)
        
        @self.client.on(events.NewMessage(chats=[target_chat_id] if target_chat_id else None))
        async def message_handler(event):
            await self.handle_message(event)
        
        # Start background tasks
        asyncio.create_task(self.reset_hourly_counter())
        asyncio.create_task(self.print_stats())
        asyncio.create_task(self.process_pending_welcomes())
        asyncio.create_task(self.cleanup_database())
        asyncio.create_task(self.retry_queue.process_queue())
        
        logger.info("✅ Userbot active! Monitoring for new members and help requests...")
        logger.info("🕵️  STEALTH MODE: Random delays, human patterns, rate limiting active")
        
        # Keep running
        await self.client.run_until_disconnected()


async def main():
    """Main entry point"""
    try:
        userbot = StealthUserbot()
        await userbot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Userbot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())
