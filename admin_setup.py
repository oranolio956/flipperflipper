#!/usr/bin/env python3
"""
One-Time Admin Setup System
Generates a unique token URL for initial admin account creation
"""

import os
import sys
import secrets
import sqlite3
import bcrypt
import re
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

class AdminSetupManager:
    """Manages one-time admin setup tokens"""
    
    def __init__(self, db_path='Application/admin_setup.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize admin setup database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS setup_tokens (
                token TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                used_at TEXT,
                ip_address TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                setup_token TEXT,
                last_login TEXT,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                FOREIGN KEY (setup_token) REFERENCES setup_tokens(token)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_setup_token(self, expires_hours=24):
        """Generate a one-time setup token"""
        # Generate cryptographically secure token
        token = secrets.token_urlsafe(32)
        
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=expires_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO setup_tokens (token, created_at, expires_at)
            VALUES (?, ?, ?)
        ''', (token, created_at.isoformat(), expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        return token
    
    def validate_token(self, token):
        """Validate setup token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT token, expires_at, used
            FROM setup_tokens
            WHERE token = ?
        ''', (token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "Invalid token"
        
        token_val, expires_at, used = result
        
        if used:
            return False, "Token already used"
        
        expires = datetime.fromisoformat(expires_at)
        if datetime.utcnow() > expires:
            return False, "Token expired"
        
        return True, "Token valid"
    
    def mark_token_used(self, token, ip_address=None):
        """Mark token as used"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE setup_tokens
            SET used = 1, used_at = ?, ip_address = ?
            WHERE token = ?
        ''', (datetime.utcnow().isoformat(), ip_address, token))
        
        conn.commit()
        conn.close()
    
    def create_admin_account(self, token, username, password):
        """Create admin account using setup token"""
        # Validate token first
        valid, message = self.validate_token(token)
        if not valid:
            return False, message
        
        # Validate username (alphanumeric + underscore only)
        if not re.match(r'^[a-zA-Z0-9_]{3,32}$', username):
            return False, "Username must be 3-32 alphanumeric characters"
        
        # Validate password strength
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special character"
        
        # Hash password with bcrypt (proper password hashing)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO admin_accounts (username, password_hash, created_at, setup_token)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, datetime.utcnow().isoformat(), token))
            
            conn.commit()
            return True, "Admin account created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        finally:
            conn.close()
    
    def admin_exists(self):
        """Check if any admin account exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM admin_accounts')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    
    def get_unused_tokens(self):
        """Get all unused, non-expired tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT token, created_at, expires_at
            FROM setup_tokens
            WHERE used = 0 AND datetime(expires_at) > datetime('now')
        ''')
        
        tokens = cursor.fetchall()
        conn.close()
        
        return tokens


def generate_setup_url(base_url='http://localhost:5000'):
    """Generate a one-time admin setup URL"""
    manager = AdminSetupManager()
    
    # Check if admin already exists
    if manager.admin_exists():
        print("❌ Admin account already exists!")
        print("   Delete Application/admin_setup.db to reset")
        return None
    
    # Generate token
    token = manager.generate_setup_token(expires_hours=24)
    
    # Create setup URL
    setup_url = f"{base_url}/admin/setup?token={token}"
    
    return setup_url, token


if __name__ == '__main__':
    print("=" * 70)
    print("🔐 ONE-TIME ADMIN SETUP TOKEN GENERATOR")
    print("=" * 70)
    print()
    
    manager = AdminSetupManager()
    
    # Check if admin exists
    if manager.admin_exists():
        print("❌ Admin account already exists!")
        print()
        print("To reset and generate a new token:")
        print("  rm Application/admin_setup.db")
        print("  python3 admin_setup.py")
        sys.exit(1)
    
    # Get base URL from environment or use default
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # Check if running in Gitpod
    if os.getenv('GITPOD_WORKSPACE_ID'):
        workspace_id = os.getenv('GITPOD_WORKSPACE_ID')
        cluster_host = os.getenv('GITPOD_WORKSPACE_CLUSTER_HOST', 'gitpod.io')
        base_url = f"https://5000-{workspace_id}.{cluster_host}"
    
    # Generate token
    token = manager.generate_setup_token(expires_hours=24)
    setup_url = f"{base_url}/admin/setup?token={token}"
    
    print("✅ One-time admin setup token generated!")
    print()
    print("📋 SETUP INFORMATION:")
    print("-" * 70)
    print(f"Token:      {token}")
    print(f"Expires:    24 hours from now")
    print()
    print("🔗 SETUP URL (use this once):")
    print("-" * 70)
    print(setup_url)
    print()
    print("⚠️  IMPORTANT:")
    print("  • This URL can only be used ONCE")
    print("  • It expires in 24 hours")
    print("  • Keep this URL secret and secure")
    print("  • After setup, you can manage users from the admin panel")
    print()
    print("=" * 70)
