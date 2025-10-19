"""
Database persistence for userbot state
Ensures we remember who we've messaged even after restarts
"""

import json
import os
from datetime import datetime, timezone
from typing import Set, Dict
from file_lock import DatabaseLock


class Database:
    """Simple JSON-based database for persistence"""
    
    def __init__(self, db_file='userbot_data.json'):
        self.db_file = db_file
        self.lock = DatabaseLock(db_file)
        self.data = self.load()
        # Create file immediately if it doesn't exist
        if not os.path.exists(self.db_file):
            self.save()
    
    def load(self) -> dict:
        """Load database from file with locking"""
        if os.path.exists(self.db_file):
            try:
                with self.lock.transaction():
                    with open(self.db_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error loading database: {e}")
                return self._default_data()
        return self._default_data()
    
    def _default_data(self) -> dict:
        """Default database structure"""
        return {
            'welcomed_users': [],
            'help_cooldowns': {},
            'message_count_today': 0,
            'last_reset_date': str(datetime.now().date()),
            'pending_welcomes': []  # Users we tried but couldn't message
        }
    
    def save(self):
        """Save database to file with locking"""
        try:
            with self.lock.transaction():
                # Write to temp file first
                temp_file = f"{self.db_file}.tmp"
                with open(temp_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                
                # Atomic rename
                os.replace(temp_file, self.db_file)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def has_welcomed(self, user_id: int) -> bool:
        """Check if user has been welcomed"""
        return user_id in self.data['welcomed_users']
    
    def add_welcomed(self, user_id: int):
        """Mark user as welcomed"""
        if user_id not in self.data['welcomed_users']:
            self.data['welcomed_users'].append(user_id)
            self.save()
    
    def get_welcomed_users(self) -> Set[int]:
        """Get set of welcomed user IDs"""
        return set(self.data['welcomed_users'])
    
    def is_on_cooldown(self, user_id: int, hours: int = 24) -> bool:
        """Check if user is on help cooldown"""
        str_id = str(user_id)
        if str_id not in self.data['help_cooldowns']:
            return False
        
        last_help = datetime.fromisoformat(self.data['help_cooldowns'][str_id])
        hours_passed = (datetime.now() - last_help).total_seconds() / 3600
        return hours_passed < hours
    
    def add_help_cooldown(self, user_id: int):
        """Add user to help cooldown"""
        self.data['help_cooldowns'][str(user_id)] = datetime.now(timezone.utc).isoformat()
        self.save()
    
    def get_daily_count(self) -> int:
        """Get today's message count"""
        today = str(datetime.now(timezone.utc).date())
        
        # Reset if new day
        if self.data['last_reset_date'] != today:
            self.data['message_count_today'] = 0
            self.data['last_reset_date'] = today
            self.save()
        
        return self.data['message_count_today']
    
    def increment_daily_count(self):
        """Increment today's message count"""
        self.data['message_count_today'] += 1
        self.save()
    
    def add_pending_welcome(self, user_id: int, username: str, reason: str):
        """Add user to pending welcomes (couldn't message due to limits)"""
        pending = {
            'user_id': user_id,
            'username': username,
            'reason': reason,
            'added': datetime.now(timezone.utc).isoformat()
        }
        
        # Don't add duplicates
        if not any(p['user_id'] == user_id for p in self.data['pending_welcomes']):
            self.data['pending_welcomes'].append(pending)
            self.save()
    
    def get_pending_welcomes(self) -> list:
        """Get list of pending welcomes"""
        return self.data['pending_welcomes']
    
    def remove_pending_welcome(self, user_id: int):
        """Remove user from pending welcomes"""
        self.data['pending_welcomes'] = [
            p for p in self.data['pending_welcomes'] 
            if p['user_id'] != user_id
        ]
        self.save()
    
    def clean_old_cooldowns(self, hours: int = 48):
        """Remove cooldowns older than specified hours"""
        now = datetime.now()
        cleaned = {}
        
        for user_id, timestamp in self.data['help_cooldowns'].items():
            last_help = datetime.fromisoformat(timestamp)
            hours_passed = (now - last_help).total_seconds() / 3600
            
            if hours_passed < hours:
                cleaned[user_id] = timestamp
        
        if len(cleaned) != len(self.data['help_cooldowns']):
            self.data['help_cooldowns'] = cleaned
            self.save()
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        return {
            'total_welcomed': len(self.data['welcomed_users']),
            'active_cooldowns': len(self.data['help_cooldowns']),
            'messages_today': self.data['message_count_today'],
            'pending_welcomes': len(self.data['pending_welcomes'])
        }
