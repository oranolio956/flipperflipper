#!/usr/bin/env python3
"""
Authentication utilities for API keys and failed login alerts
"""
import os
import json
import hashlib
import secrets
import time
import smtplib
import requests
import logging
import html
import re
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request, jsonify, g, session
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config

logger = logging.getLogger(__name__)

# Failed login tracking
failed_login_attempts = {}
failed_login_lock = {}

class APIKeyManager:
    """Manage API keys for authentication"""
    
    def __init__(self):
        self.api_keys_file = Config.API_KEYS_FILE
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from file"""
        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load API keys: {e}")
        return {}
    
    def _save_api_keys(self):
        """Save API keys to file"""
        try:
            # Ensure directory exists
            self.api_keys_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.api_keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
            
            # Set restricted permissions
            try:
                os.chmod(self.api_keys_file, 0o600)
            except Exception:
                pass  # Windows doesn't support chmod
                
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")
    
    def generate_api_key(self, name, description=""):
        """Generate a new API key"""
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'usage_count': 0
        }
        
        self._save_api_keys()
        return api_key
    
    def validate_api_key(self, api_key):
        """Validate an API key"""
        if not api_key:
            return False
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            # Update usage statistics
            self.api_keys[key_hash]['last_used'] = datetime.now().isoformat()
            self.api_keys[key_hash]['usage_count'] += 1
            self._save_api_keys()
            return True
        
        return False
    
    def revoke_api_key(self, api_key):
        """Revoke an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            del self.api_keys[key_hash]
            self._save_api_keys()
            return True
        
        return False
    
    def list_api_keys(self):
        """List all API keys (without exposing actual keys)"""
        return [{
            'name': info['name'],
            'description': info['description'],
            'created_at': info['created_at'],
            'last_used': info['last_used'],
            'usage_count': info['usage_count']
        } for info in self.api_keys.values()]

# Global API key manager instance
api_key_manager = APIKeyManager()

def api_key_required(f):
    """Decorator for endpoints that require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.ENABLE_API_KEYS:
            # API keys not enabled, fall back to session auth
            if 'user' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        
        # Check for API key in header
        api_key = request.headers.get(Config.API_KEY_HEADER)
        
        if api_key and api_key_manager.validate_api_key(api_key):
            g.api_authenticated = True
            return f(*args, **kwargs)
        
        # Fall back to session authentication
        if 'user' in session:
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Invalid or missing API key'}), 401
    
    return decorated_function

def api_key_or_login_required(f):
    """Decorator that accepts either API key or session authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check API key first
        if Config.ENABLE_API_KEYS:
            api_key = request.headers.get(Config.API_KEY_HEADER)
            if api_key and api_key_manager.validate_api_key(api_key):
                g.api_authenticated = True
                return f(*args, **kwargs)
        
        # Check session authentication
        if 'user' in session:
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function

class FailedLoginAlerter:
    """Handle failed login alerts via email or webhook"""
    
    @staticmethod
    def send_email_alert(ip_address, username, attempt_count):
        """Send email alert for failed login attempts"""
        if not Config.ALERT_EMAIL or not Config.SMTP_HOST:
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[SECURITY] Failed Login Alert - {Config.APP_NAME}"
            msg['From'] = Config.SMTP_USER or 'noreply@localhost'
            msg['To'] = Config.ALERT_EMAIL
            
            text = f"""
            SECURITY ALERT: Multiple Failed Login Attempts
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            IP Address: {ip_address}
            Username Attempted: {username}
            Failed Attempts: {attempt_count}
            
            Action Taken: Account temporarily locked for {Config.LOGIN_LOCKOUT_MINUTES} minutes
            
            If this was not you, please review your security settings immediately.
            """
            
            html = f"""
            <html>
              <body>
                <h2 style="color: #dc2626;">SECURITY ALERT: Multiple Failed Login Attempts</h2>
                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                  <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Time:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>IP Address:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{ip_address}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Username:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{username}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Failed Attempts:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{attempt_count}</td>
                  </tr>
                </table>
                <p><strong>Action Taken:</strong> Account temporarily locked for {Config.LOGIN_LOCKOUT_MINUTES} minutes</p>
                <p style="color: #666;">If this was not you, please review your security settings immediately.</p>
              </body>
            </html>
            """
            
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                if Config.SMTP_USE_TLS:
                    server.starttls()
                if Config.SMTP_USER and Config.SMTP_PASSWORD:
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(msg)
                
            logger.info(f"Failed login alert email sent to {Config.ALERT_EMAIL}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    @staticmethod
    def send_webhook_alert(ip_address, username, attempt_count):
        """Send webhook alert for failed login attempts"""
        if not Config.ALERT_WEBHOOK_URL:
            return
        
        try:
            payload = {
                'event': 'failed_login_alert',
                'timestamp': datetime.now().isoformat(),
                'app': Config.APP_NAME,
                'details': {
                    'ip_address': ip_address,
                    'username': username,
                    'failed_attempts': attempt_count,
                    'lockout_minutes': Config.LOGIN_LOCKOUT_MINUTES
                }
            }
            
            response = requests.post(
                Config.ALERT_WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Failed login webhook alert sent successfully")
            else:
                logger.error(f"Webhook alert failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

def track_failed_login(ip_address, username):
    """Track failed login attempts and trigger alerts if needed"""
    global failed_login_attempts
    
    # Initialize tracking for this IP
    if ip_address not in failed_login_attempts:
        failed_login_attempts[ip_address] = []
    
    # Add this attempt
    failed_login_attempts[ip_address].append({
        'username': username,
        'timestamp': datetime.now()
    })
    
    # Clean old attempts (outside the lockout window)
    cutoff_time = datetime.now() - timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
    failed_login_attempts[ip_address] = [
        attempt for attempt in failed_login_attempts[ip_address]
        if attempt['timestamp'] > cutoff_time
    ]
    
    # Check if we've exceeded the threshold
    attempt_count = len(failed_login_attempts[ip_address])
    
    if attempt_count >= Config.FAILED_LOGIN_THRESHOLD and Config.ENABLE_FAILED_LOGIN_ALERTS:
        # Send alerts
        FailedLoginAlerter.send_email_alert(ip_address, username, attempt_count)
        FailedLoginAlerter.send_webhook_alert(ip_address, username, attempt_count)
    
    return attempt_count

def track_failed_email_login(email, ip_address):
    """Track failed email login attempts and lock email if needed"""
    # This would integrate with the email_auth module
    # For now, we'll use the existing IP-based tracking
    return track_failed_login(ip_address, email)

def is_login_locked(ip_address):
    """Check if an IP address is locked due to too many failed attempts"""
    global failed_login_lock
    
    if ip_address in failed_login_lock:
        lock_time = failed_login_lock[ip_address]
        if datetime.now() < lock_time:
            return True
        else:
            # Lock expired
            del failed_login_lock[ip_address]
    
    if ip_address in failed_login_attempts:
        attempt_count = len(failed_login_attempts.get(ip_address, []))
        if attempt_count >= Config.MAX_LOGIN_ATTEMPTS:
            # Lock the IP
            failed_login_lock[ip_address] = datetime.now() + timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
            return True
    
    return False

def get_lockout_time_remaining(ip_address):
    """Get remaining lockout time in seconds"""
    if ip_address in failed_login_lock:
        remaining = (failed_login_lock[ip_address] - datetime.now()).total_seconds()
        if remaining > 0:
            return int(remaining)
    return 0

def clear_failed_login_attempts(ip_address):
    """Clear failed login attempts for an IP after successful login"""
    global failed_login_attempts, failed_login_lock
    
    if ip_address in failed_login_attempts:
        del failed_login_attempts[ip_address]
    
    if ip_address in failed_login_lock:
        del failed_login_lock[ip_address]

# ============================================================================
# Security Validation Functions
# ============================================================================

import re
import html
from urllib.parse import quote, unquote

def validate_input(input_data: str, input_type: str = "general") -> bool:
    """
    Validate input data based on type
    
    Args:
        input_data: The input string to validate
        input_type: Type of input (email, command, filename, etc.)
    
    Returns:
        bool: True if valid, False if invalid
    """
    if not isinstance(input_data, str):
        return False
    
    # Length limits
    if len(input_data) > 1000:
        return False
    
    # Type-specific validation
    if input_type == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, input_data))
    
    elif input_type == "command":
        # Allow alphanumeric, spaces, and common command characters
        command_pattern = r'^[a-zA-Z0-9\s\-_./\\:;=+*?()[\]{}|&<>!@#$%^~`"\']*$'
        return bool(re.match(command_pattern, input_data))
    
    elif input_type == "filename":
        # Prevent path traversal and dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in input_data for char in dangerous_chars):
            return False
        return len(input_data) <= 255
    
    elif input_type == "url":
        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(url_pattern, input_data))
    
    else:  # general
        # Basic validation - no null bytes, control characters, etc.
        if '\x00' in input_data or any(ord(c) < 32 and c not in '\t\n\r' for c in input_data):
            return False
        return True

def sanitize_input(input_data: str, input_type: str = "general") -> str:
    """
    Sanitize input data to prevent XSS and injection attacks
    
    Args:
        input_data: The input string to sanitize
        input_type: Type of input (html, sql, command, etc.)
    
    Returns:
        str: Sanitized input
    """
    if not isinstance(input_data, str):
        return ""
    
    # HTML sanitization
    if input_type == "html":
        # Escape HTML entities
        sanitized = html.escape(input_data, quote=True)
        return sanitized
    
    # SQL sanitization (basic)
    elif input_type == "sql":
        # Remove or escape dangerous SQL characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = input_data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized
    
    # Command sanitization
    elif input_type == "command":
        # Remove shell metacharacters
        dangerous_chars = ['&', '|', ';', '`', '$', '(', ')', '<', '>', '\n', '\r']
        sanitized = input_data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized
    
    # General sanitization
    else:
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in input_data if ord(char) >= 32 or char in '\t\n\r')
        
        # Remove script tags and dangerous HTML
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized

def validate_email(email: str) -> bool:
    """Validate email address format"""
    return validate_input(email, "email")

def sanitize_html(html_content: str) -> str:
    """Sanitize HTML content to prevent XSS"""
    return sanitize_input(html_content, "html")

def sanitize_sql(sql_content: str) -> str:
    """Sanitize SQL content to prevent injection"""
    return sanitize_input(sql_content, "sql")

def sanitize_command(command: str) -> str:
    """Sanitize command to prevent shell injection"""
    return sanitize_input(command, "command")

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no path traversal)"""
    return validate_input(filename, "filename")

def validate_password_strength(password):
    """
    Validate password meets complexity requirements
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []
    
    if not password:
        return False, ["Password is required"]
    
    # Length check
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters long")
    
    # Uppercase check
    if Config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Lowercase check
    if Config.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Numbers check
    if Config.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    # Symbols check
    if Config.PASSWORD_REQUIRE_SYMBOLS:
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in symbols for c in password):
            errors.append("Password must contain at least one special character")
    
    # Common password check
    common_passwords = [
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "1234567890", "abc123"
    ]
    if password.lower() in common_passwords:
        errors.append("Password is too common, please choose a stronger password")
    
    return len(errors) == 0, errors

def test_security_validation():
    """Test security validation functions"""
    print("Testing security validation functions...")
    
    # Test email validation
    test_emails = [
        "test@example.com",
        "invalid-email",
        "test@domain.co.uk",
        "user+tag@example.org"
    ]
    
    print("\n1. Email validation:")
    for email in test_emails:
        result = validate_email(email)
        print(f"   {email}: {'✅' if result else '❌'}")
    
    # Test password validation
    test_passwords = [
        "StrongPass123!",
        "weak",
        "password123",
        "NoNumbers!",
        "nouppercase123!",
        "NOLOWERCASE123!"
    ]
    
    print("\n2. Password validation:")
    for password in test_passwords:
        is_valid, errors = validate_password_strength(password)
        print(f"   {password}: {'✅' if is_valid else '❌'}")
        if errors:
            for error in errors:
                print(f"      - {error}")
    
    # Test HTML sanitization
    test_html = [
        "Normal text",
        "<script>alert('xss')</script>",
        "Hello <b>world</b>",
        "<img src=x onerror=alert(1)>"
    ]
    
    print("\n3. HTML sanitization:")
    for html_content in test_html:
        sanitized = sanitize_html(html_content)
        print(f"   {html_content[:30]}... -> {sanitized[:30]}...")
    
    # Test command sanitization
    test_commands = [
        "ls -la",
        "rm -rf /; echo hacked",
        "cat file.txt",
        "command & echo hacked"
    ]
    
    print("\n4. Command sanitization:")
    for command in test_commands:
        sanitized = sanitize_command(command)
        print(f"   {command} -> {sanitized}")
    
    # Test filename validation
    test_filenames = [
        "document.pdf",
        "../../../etc/passwd",
        "file.txt",
        "file/with/path.txt"
    ]
    
    print("\n5. Filename validation:")
    for filename in test_filenames:
        result = is_safe_filename(filename)
        print(f"   {filename}: {'✅' if result else '❌'}")
    
    print("\n✅ Security validation test complete")

if __name__ == "__main__":
    test_security_validation()