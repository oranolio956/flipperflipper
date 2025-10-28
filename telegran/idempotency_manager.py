"""
Idempotency Manager - Prevent duplicate messages
Ensures messages are sent exactly once, even with network failures
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class IdempotencyManager:
    """Track message sends to prevent duplicates"""
    
    def __init__(self, ttl_hours: int = 48):
        """
        Initialize idempotency manager
        
        Args:
            ttl_hours: How long to remember message IDs (hours)
        """
        self.sent_messages = {}  # message_id -> timestamp
        self.ttl = timedelta(hours=ttl_hours)
        self.state_file = 'idempotency_state.json'
        self.load_state()
    
    def generate_message_id(self, user_id: int, message_type: str, content: str = "") -> str:
        """
        Generate unique message ID
        
        Args:
            user_id: Telegram user ID
            message_type: 'welcome' or 'help'
            content: Optional message content for additional uniqueness
            
        Returns:
            Unique message ID
        """
        # Create unique key from user_id + type + optional content
        key = f"{user_id}:{message_type}:{content}"
        
        # Hash it
        message_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        
        return message_id
    
    def has_been_sent(self, message_id: str) -> bool:
        """Check if message with this ID has been sent"""
        if message_id not in self.sent_messages:
            return False
        
        # Check if expired
        sent_at = datetime.fromisoformat(self.sent_messages[message_id])
        age = datetime.now(timezone.utc) - sent_at
        
        if age > self.ttl:
            # Expired, remove it
            del self.sent_messages[message_id]
            return False
        
        return True
    
    def mark_as_sent(self, message_id: str):
        """Mark message as sent"""
        self.sent_messages[message_id] = datetime.now(timezone.utc).isoformat()
        self.save_state()
    
    def cleanup_expired(self):
        """Remove expired message IDs"""
        now = datetime.now(timezone.utc)
        expired = []
        
        for message_id, timestamp in self.sent_messages.items():
            sent_at = datetime.fromisoformat(timestamp)
            age = now - sent_at
            
            if age > self.ttl:
                expired.append(message_id)
        
        for message_id in expired:
            del self.sent_messages[message_id]
        
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired message IDs")
            self.save_state()
    
    def load_state(self):
        """Load state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    self.sent_messages = json.load(f)
                logger.info(f"📥 Loaded {len(self.sent_messages)} message IDs from state")
        except Exception as e:
            logger.error(f"Error loading idempotency state: {e}")
            self.sent_messages = {}
    
    def save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.sent_messages, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving idempotency state: {e}")
    
    def get_stats(self) -> dict:
        """Get statistics"""
        return {
            'tracked_messages': len(self.sent_messages),
            'oldest_age_hours': self._get_oldest_age() / 3600 if self.sent_messages else 0
        }
    
    def _get_oldest_age(self) -> float:
        """Get age of oldest tracked message in seconds"""
        if not self.sent_messages:
            return 0
        
        oldest = min(
            datetime.fromisoformat(ts)
            for ts in self.sent_messages.values()
        )
        
        return (datetime.now(timezone.utc) - oldest).total_seconds()


# Add missing import
import os
