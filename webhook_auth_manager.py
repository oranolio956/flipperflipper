#!/usr/bin/env python3
"""
Webhook-Based Authentication Manager
Secure authentication system using webhook.site for code generation and verification
"""

import os
import json
import secrets
import hashlib
import requests
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
from config import Config

class WebhookAuthManager:
    """
    Manages webhook-based authentication with secure code generation
    """
    
    def __init__(self):
        """Initialize webhook authentication manager"""
        self.webhook_url = "https://webhook.site/b8f87549-03f0-4032-be49-859cc22f0e46"
        self.webhook_api_url = "https://webhook.site/token/b8f87549-03f0-4032-be49-859cc22f0e46/requests"
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # In-memory storage for active authentication sessions
        self.active_sessions = {}
        self.session_lock = threading.Lock()
        
        # Cleanup expired sessions every 5 minutes
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def _get_encryption_key(self):
        """Get or generate encryption key for secure data storage"""
        key_file = Config.APPLICATION_DIR / '.webhook_auth_key'
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                    Fernet(key)  # Verify it's valid
                    return key
            except Exception:
                pass
        
        # Generate new key
        key = Fernet.generate_key()
        try:
            Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
        except Exception as e:
            print(f"Warning: Could not save webhook auth key: {e}")
        
        return key
    
    def generate_auth_code(self, user_identifier: str, ip_address: str) -> Tuple[str, str]:
        """
        Generate a secure authentication code and send it to webhook
        
        Args:
            user_identifier: Email or username for authentication
            ip_address: Client IP address for security tracking
            
        Returns:
            Tuple of (session_id, display_code) - display_code is what user sees
        """
        # Generate secure session ID
        session_id = secrets.token_urlsafe(32)
        
        # Generate 6-digit display code (what user will see)
        display_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Generate internal verification code (more complex)
        verification_code = secrets.token_urlsafe(16)
        
        # Create session data
        session_data = {
            'user_identifier': user_identifier,
            'ip_address': ip_address,
            'display_code': display_code,
            'verification_code': verification_code,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat(),
            'attempts': 0,
            'max_attempts': 3,
            'verified': False
        }
        
        # Encrypt and store session
        encrypted_data = self.cipher.encrypt(json.dumps(session_data).encode())
        
        with self.session_lock:
            self.active_sessions[session_id] = encrypted_data
        
        # Send to webhook
        self._send_to_webhook(session_data, display_code)
        
        return session_id, display_code
    
    def _send_to_webhook(self, session_data: dict, display_code: str):
        """Send authentication data to webhook.site"""
        try:
            webhook_data = {
                'timestamp': datetime.now().isoformat(),
                'type': 'auth_code_generated',
                'user_identifier': session_data['user_identifier'],
                'ip_address': session_data['ip_address'],
                'display_code': display_code,
                'expires_in_minutes': 10,
                'security_level': 'high',
                'message': f"Authentication code for {session_data['user_identifier']}: {display_code}"
            }
            
            response = requests.post(
                self.webhook_url,
                json=webhook_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✅ Webhook notification sent for user: {session_data['user_identifier']}")
            else:
                print(f"⚠️ Webhook notification failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to send webhook notification: {e}")
    
    def verify_auth_code(self, session_id: str, entered_code: str, ip_address: str) -> Tuple[bool, str, dict]:
        """
        Verify the entered authentication code
        
        Args:
            session_id: Session ID from generate_auth_code
            entered_code: Code entered by user
            ip_address: Client IP for verification
            
        Returns:
            Tuple of (is_valid, message, session_data)
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False, "Invalid or expired session", {}
            
            try:
                # Decrypt session data
                encrypted_data = self.active_sessions[session_id]
                session_data = json.loads(self.cipher.decrypt(encrypted_data).decode())
                
                # Check if session is expired
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    del self.active_sessions[session_id]
                    return False, "Session expired", {}
                
                # Check IP address
                if session_data['ip_address'] != ip_address:
                    return False, "IP address mismatch", {}
                
                # Check attempts
                session_data['attempts'] += 1
                if session_data['attempts'] > session_data['max_attempts']:
                    del self.active_sessions[session_id]
                    return False, "Too many failed attempts", {}
                
                # Verify code
                if session_data['display_code'] == entered_code.strip():
                    session_data['verified'] = True
                    session_data['verified_at'] = datetime.now().isoformat()
                    
                    # Update stored session
                    encrypted_data = self.cipher.encrypt(json.dumps(session_data).encode())
                    self.active_sessions[session_id] = encrypted_data
                    
                    return True, "Authentication successful", session_data
                else:
                    # Update attempts
                    encrypted_data = self.cipher.encrypt(json.dumps(session_data).encode())
                    self.active_sessions[session_id] = encrypted_data
                    
                    remaining_attempts = session_data['max_attempts'] - session_data['attempts']
                    return False, f"Invalid code. {remaining_attempts} attempts remaining", session_data
                    
            except Exception as e:
                print(f"Error verifying auth code: {e}")
                return False, "Verification error", {}
    
    def get_session_status(self, session_id: str) -> Optional[dict]:
        """Get current session status"""
        with self.session_lock:
            if session_id not in self.active_sessions:
                return None
            
            try:
                encrypted_data = self.active_sessions[session_id]
                session_data = json.loads(self.cipher.decrypt(encrypted_data).decode())
                
                # Check if expired
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    del self.active_sessions[session_id]
                    return None
                
                return session_data
            except Exception:
                return None
    
    def cleanup_session(self, session_id: str):
        """Remove session from active sessions"""
        with self.session_lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    def _cleanup_expired_sessions(self):
        """Background thread to clean up expired sessions"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                with self.session_lock:
                    expired_sessions = []
                    current_time = datetime.now()
                    
                    for session_id, encrypted_data in self.active_sessions.items():
                        try:
                            session_data = json.loads(self.cipher.decrypt(encrypted_data).decode())
                            expires_at = datetime.fromisoformat(session_data['expires_at'])
                            
                            if current_time > expires_at:
                                expired_sessions.append(session_id)
                        except Exception:
                            # Invalid session data, mark for cleanup
                            expired_sessions.append(session_id)
                    
                    # Remove expired sessions
                    for session_id in expired_sessions:
                        del self.active_sessions[session_id]
                    
                    if expired_sessions:
                        print(f"🧹 Cleaned up {len(expired_sessions)} expired webhook sessions")
                        
            except Exception as e:
                print(f"Error in session cleanup: {e}")
    
    def get_webhook_requests(self) -> list:
        """Get recent webhook requests for monitoring"""
        try:
            response = requests.get(
                self.webhook_api_url,
                params={'query': 'uuid:bb08afb4-147e-4772-8547-5583eb152ea9'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch webhook requests: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching webhook requests: {e}")
            return []
    
    def send_verification_notification(self, user_identifier: str, success: bool, ip_address: str):
        """Send verification result to webhook"""
        try:
            webhook_data = {
                'timestamp': datetime.now().isoformat(),
                'type': 'auth_verification_result',
                'user_identifier': user_identifier,
                'ip_address': ip_address,
                'success': success,
                'message': f"Authentication {'succeeded' if success else 'failed'} for {user_identifier}"
            }
            
            response = requests.post(
                self.webhook_url,
                json=webhook_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✅ Verification notification sent for {user_identifier}")
                
        except Exception as e:
            print(f"❌ Failed to send verification notification: {e}")

# Global instance
webhook_auth_manager = WebhookAuthManager()