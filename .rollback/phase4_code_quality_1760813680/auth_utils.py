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