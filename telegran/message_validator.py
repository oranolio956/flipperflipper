"""
Message Validator - Sanitize and validate all messages
Handles encoding, length, special characters
"""

import unicodedata
import re
from typing import Tuple


class MessageValidator:
    """Validate and sanitize messages before sending"""
    
    # Telegram limits
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    MAX_USERNAME_LENGTH = 32
    
    def __init__(self):
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002500-\U00002BEF"  # chinese char
            "\U00002702-\U000027B0"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+",
            flags=re.UNICODE
        )
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode text to NFC form
        Handles combining characters, emoji, RTL text
        """
        if not text:
            return ""
        
        # Normalize to NFC (Canonical Composition)
        normalized = unicodedata.normalize('NFC', text)
        
        # Remove zero-width characters (can be used maliciously)
        zero_width_chars = [
            '\u200b',  # Zero-width space
            '\u200c',  # Zero-width non-joiner
            '\u200d',  # Zero-width joiner (keep for emoji)
            '\u200e',  # Left-to-right mark
            '\u200f',  # Right-to-left mark
            '\ufeff',  # Zero-width no-break space
        ]
        
        for char in zero_width_chars:
            if char != '\u200d':  # Keep ZWJ for emoji
                normalized = normalized.replace(char, '')
        
        return normalized
    
    def sanitize_username(self, username: str) -> str:
        """
        Sanitize username for safe display
        
        Args:
            username: Raw username from Telegram
            
        Returns:
            Safe username
        """
        if not username:
            return "there"
        
        # Normalize
        username = self.normalize_unicode(username)
        
        # Remove control characters
        username = ''.join(
            char for char in username
            if not unicodedata.category(char).startswith('C')
            or char in ['\n', '\t']
        )
        
        # Truncate if too long
        if len(username) > self.MAX_USERNAME_LENGTH:
            username = username[:self.MAX_USERNAME_LENGTH] + "..."
        
        # Remove leading/trailing whitespace
        username = username.strip()
        
        # Fallback if empty after sanitization
        if not username:
            return "there"
        
        return username
    
    def validate_message_length(self, message: str, max_length: int = None) -> Tuple[bool, str]:
        """
        Validate message length
        
        Args:
            message: Message text
            max_length: Maximum length (default: Telegram limit)
            
        Returns:
            (is_valid, error_message)
        """
        if max_length is None:
            max_length = self.MAX_MESSAGE_LENGTH
        
        if len(message) > max_length:
            return False, f"Message too long: {len(message)} > {max_length}"
        
        return True, ""
    
    def truncate_message(self, message: str, max_length: int = None) -> str:
        """
        Truncate message to safe length
        
        Args:
            message: Message text
            max_length: Maximum length
            
        Returns:
            Truncated message
        """
        if max_length is None:
            max_length = self.MAX_MESSAGE_LENGTH
        
        if len(message) <= max_length:
            return message
        
        # Leave room for ellipsis
        truncate_at = max_length - 3
        return message[:truncate_at] + "..."
    
    def remove_zalgo(self, text: str) -> str:
        """
        Remove Zalgo text (excessive combining diacritics)
        
        Example of Zalgo: H̷̡̪̯ͨ͊̽̅̾̎Ȩ̬̩̾͛ͪ̈́̀́͘
        """
        if not text:
            return ""
        
        # Remove excessive combining diacritics
        result = []
        combining_count = 0
        max_combining = 3  # Allow up to 3 combining chars
        
        for char in text:
            category = unicodedata.category(char)
            
            if category.startswith('M'):  # Mark category (combining)
                combining_count += 1
                if combining_count <= max_combining:
                    result.append(char)
            else:
                combining_count = 0
                result.append(char)
        
        return ''.join(result)
    
    def is_rtl_text(self, text: str) -> bool:
        """Check if text contains RTL (Right-to-Left) characters"""
        rtl_categories = {'AL', 'AN', 'RLI', 'RLE', 'RLO', 'RLM'}
        
        for char in text:
            if unicodedata.bidirectional(char) in rtl_categories:
                return True
        
        return False
    
    def count_emojis(self, text: str) -> int:
        """Count emojis in text"""
        return len(self.emoji_pattern.findall(text))
    
    def validate_and_sanitize(self, message: str, username: str = None) -> Tuple[str, str]:
        """
        Complete validation and sanitization
        
        Args:
            message: Message template
            username: Username to insert
            
        Returns:
            (sanitized_message, sanitized_username)
        """
        # Sanitize username
        if username:
            clean_username = self.sanitize_username(username)
            clean_username = self.remove_zalgo(clean_username)
        else:
            clean_username = "there"
        
        # Format message
        try:
            formatted_message = message.format(username=clean_username)
        except (KeyError, ValueError) as e:
            # Fallback if format fails
            formatted_message = message.replace('{username}', clean_username)
        
        # Normalize
        formatted_message = self.normalize_unicode(formatted_message)
        
        # Remove Zalgo
        formatted_message = self.remove_zalgo(formatted_message)
        
        # Truncate if needed
        formatted_message = self.truncate_message(formatted_message)
        
        return formatted_message, clean_username
    
    def validate_config_message(self, message: str) -> Tuple[bool, str]:
        """
        Validate a config message template
        
        Returns:
            (is_valid, error_message)
        """
        if not message:
            return False, "Message is empty"
        
        # Check for {username} placeholder
        if '{username}' not in message:
            return False, "Message must contain {username} placeholder"
        
        # Test with max length username
        test_username = "A" * self.MAX_USERNAME_LENGTH
        test_message = message.format(username=test_username)
        
        valid, error = self.validate_message_length(test_message)
        if not valid:
            return False, f"Message with max username is too long: {error}"
        
        return True, ""


# Global validator instance
validator = MessageValidator()


def safe_format_message(message: str, username: str) -> str:
    """
    Safely format a message with username
    
    Usage:
        safe_msg = safe_format_message("Hey {username}!", user.first_name)
    """
    clean_message, clean_username = validator.validate_and_sanitize(message, username)
    return clean_message
