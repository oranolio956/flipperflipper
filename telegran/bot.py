"""
Telegran Bot - Auto Welcome & Help Support Bot
Main bot application
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)

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


class TelegranBot:
    """Main bot class for handling welcomes and help requests"""
    
    def __init__(self):
        """Initialize the bot with configuration"""
        self.config = self.load_config()
        self.welcomed_users: Set[int] = set()  # Track who we've welcomed
        self.help_cooldowns: Dict[int, datetime] = {}  # Track help message cooldowns
        self.bot_token = os.getenv('BOT_TOKEN')
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables!")
    
    def load_config(self) -> dict:
        """Load configuration from config.json or use defaults"""
        default_config = {
            "welcome_message": "👋 Welcome {username} to our community! We're glad to have you here!\n\n"
                             "Feel free to introduce yourself and don't hesitate to ask if you need help! 💬",
            "help_message": "👋 Hi {username}! I noticed you might need some help.\n\n"
                          "Here are some resources:\n"
                          "📚 Getting Started Guide: [Link]\n"
                          "💬 Ask in the group - our community is friendly!\n"
                          "🔧 For technical issues, tag an admin\n\n"
                          "What specifically do you need help with?",
            "welcome_delay": 30,  # seconds
            "cooldown_hours": 24,
            "help_keywords": [
                "help", "support", "how do i", "how to", "question",
                "need assistance", "can someone help", "issue", "problem"
            ],
            "enable_welcome_buttons": True,
            "admin_notify": True
        }
        
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **config}
        except Exception as e:
            logger.warning(f"Could not load config.json: {e}. Using defaults.")
        
        # Save default config
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 **Telegran Bot Active!**\n\n"
            "I'm monitoring this chat for:\n"
            "👋 New members to welcome\n"
            "💬 Users asking for help\n\n"
            "**Admin Commands:**\n"
            "/stats - View bot statistics\n"
            "/config - View current configuration\n"
            "/test_welcome - Test welcome message\n"
            "/test_help - Test help message",
            parse_mode='Markdown'
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display bot statistics"""
        stats_msg = (
            "📊 **Bot Statistics**\n\n"
            f"👥 Welcomed users: {len(self.welcomed_users)}\n"
            f"💬 Active cooldowns: {len(self.help_cooldowns)}\n"
            f"⏰ Uptime: {self.get_uptime()}\n"
            f"🤖 Status: Active ✅"
        )
        await update.message.reply_text(stats_msg, parse_mode='Markdown')
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display current configuration"""
        config_msg = (
            "⚙️ **Current Configuration**\n\n"
            f"⏱️ Welcome Delay: {self.config['welcome_delay']}s\n"
            f"❄️ Cooldown Period: {self.config['cooldown_hours']}h\n"
            f"🔘 Welcome Buttons: {'Enabled' if self.config['enable_welcome_buttons'] else 'Disabled'}\n"
            f"📢 Admin Notifications: {'Enabled' if self.config['admin_notify'] else 'Disabled'}\n\n"
            "Edit `config.json` to change settings."
        )
        await update.message.reply_text(config_msg, parse_mode='Markdown')
    
    async def test_welcome_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test welcome message"""
        username = update.effective_user.first_name
        message = self.config['welcome_message'].format(
            username=username,
            user_id=update.effective_user.id
        )
        
        if self.config['enable_welcome_buttons']:
            keyboard = [
                [InlineKeyboardButton("📚 Getting Started", url="https://t.me/cupidbotg")],
                [InlineKeyboardButton("💬 Need Help?", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message)
    
    async def test_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test help message"""
        username = update.effective_user.first_name
        message = self.config['help_message'].format(
            username=username,
            user_id=update.effective_user.id
        )
        await update.message.reply_text(message)
    
    async def handle_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new member joins"""
        try:
            # Check if this is a new member event
            if not update.message or not update.message.new_chat_members:
                return
            
            for new_member in update.message.new_chat_members:
                # Skip if it's a bot (unless you want to welcome bots too)
                if new_member.is_bot:
                    logger.info(f"Skipping bot: {new_member.username}")
                    continue
                
                user_id = new_member.id
                username = new_member.first_name or new_member.username or "there"
                
                # Check if we've already welcomed this user
                if user_id in self.welcomed_users:
                    logger.info(f"Already welcomed user {username} ({user_id})")
                    continue
                
                logger.info(f"New member detected: {username} ({user_id})")
                
                # Schedule welcome message with delay
                await asyncio.sleep(self.config['welcome_delay'])
                
                # Send welcome message
                await self.send_welcome(update, username, user_id)
                
                # Mark as welcomed
                self.welcomed_users.add(user_id)
                
        except Exception as e:
            logger.error(f"Error handling new member: {e}", exc_info=True)
    
    async def send_welcome(self, update: Update, username: str, user_id: int):
        """Send welcome message to new member"""
        try:
            message = self.config['welcome_message'].format(
                username=username,
                user_id=user_id
            )
            
            if self.config['enable_welcome_buttons']:
                keyboard = [
                    [InlineKeyboardButton("📚 Getting Started", url="https://t.me/cupidbotg")],
                    [InlineKeyboardButton("💬 Community Rules", url="https://t.me/cupidbotg")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message)
            
            logger.info(f"✅ Sent welcome message to {username}")
            
        except Exception as e:
            logger.error(f"Error sending welcome: {e}", exc_info=True)
    
    async def handle_help_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detect and respond to help requests"""
        try:
            if not update.message or not update.message.text:
                return
            
            message_text = update.message.text.lower()
            user_id = update.effective_user.id
            username = update.effective_user.first_name or update.effective_user.username or "there"
            
            # Check if message contains help keywords
            is_help_request = any(
                keyword in message_text 
                for keyword in self.config['help_keywords']
            )
            
            if not is_help_request:
                return
            
            # Check cooldown
            if user_id in self.help_cooldowns:
                last_help = self.help_cooldowns[user_id]
                cooldown_time = timedelta(hours=self.config['cooldown_hours'])
                if datetime.now() - last_help < cooldown_time:
                    logger.info(f"Cooldown active for {username}, skipping help message")
                    return
            
            logger.info(f"Help request detected from {username}: {message_text[:50]}...")
            
            # Send help message
            help_text = self.config['help_message'].format(
                username=username,
                user_id=user_id
            )
            
            await update.message.reply_text(help_text)
            
            # Update cooldown
            self.help_cooldowns[user_id] = datetime.now()
            
            logger.info(f"✅ Sent help message to {username}")
            
        except Exception as e:
            logger.error(f"Error handling help request: {e}", exc_info=True)
    
    def get_uptime(self) -> str:
        """Calculate bot uptime"""
        # This is a placeholder - you'd track actual start time
        return "Active"
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting Telegran Bot...")
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("config", self.config_command))
        application.add_handler(CommandHandler("test_welcome", self.test_welcome_command))
        application.add_handler(CommandHandler("test_help", self.test_help_command))
        
        # Handle new members
        application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self.handle_new_member
        ))
        
        # Handle help requests
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_help_request
        ))
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        logger.info("✅ Bot started successfully!")
        logger.info("📡 Listening for new members and help requests...")
        
        # Start polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    try:
        bot = TelegranBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
