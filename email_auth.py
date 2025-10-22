#!/usr/bin/env python3
"""
Email Authentication Module
Database operations for email-based authentication
Elite passwordless authentication system
"""

import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from config import Config
from automated_email_service import automated_email_service

DB_PATH = Config.APPLICATION_DIR / 'stitch.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_verification_code(length=6):
    """
    Generate cryptographically secure numeric code
    
    Args:
        length (int): Length of code (default: 6)
    
    Returns:
        str: Random numeric code (e.g., "742891")
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

def hash_code(code):
    """
    Hash verification code for secure storage
    
    Args:
        code (str): Plaintext code
    
    Returns:
        str: SHA-256 hash of code
    """
    return hashlib.sha256(code.encode()).hexdigest()

def create_verification_code(email, ip_address=""):
    """
    Generate and store verification code for email
    
    Args:
        email (str): Email address
        ip_address (str): IP address of requester
    
    Returns:
        tuple: (code, expires_at) or (None, None) if failed
    """
    # Generate code
    code = generate_verification_code(6)
    code_hash = hash_code(code)
    
    # Set expiration (10 minutes)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO email_verification_codes 
            (email, code_hash, ip_address, expires_at)
            VALUES (?, ?, ?, ?)
        """, (email, code_hash, ip_address, expires_at))
        
        conn.commit()
        return code, expires_at
    
    except Exception as e:
        print(f"Error creating verification code: {e}")
        conn.rollback()
        return None, None
    
    finally:
        conn.close()

def verify_code(email, code):
    """
    Verify email verification code
    
    Args:
        email (str): Email address
        code (str): Code to verify
    
    Returns:
        bool: True if valid, False otherwise
    """
    code_hash = hash_code(code)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Find valid code
        cursor.execute("""
            SELECT id, expires_at, used, attempts 
            FROM email_verification_codes
            WHERE email = ? AND code_hash = ? AND used = 0
            ORDER BY created_at DESC
            LIMIT 1
        """, (email, code_hash))
        
        row = cursor.fetchone()
        
        if not row:
            return False
        
        # Check expiration
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            return False
        
        # Check attempts
        if row['attempts'] >= 5:
            return False
        
        # Mark as used
        cursor.execute("""
            UPDATE email_verification_codes 
            SET used = 1
            WHERE id = ?
        """, (row['id'],))
        
        # Update last login
        cursor.execute("""
            UPDATE users_email 
            SET last_login = CURRENT_TIMESTAMP,
                login_count = login_count + 1
            WHERE email = ?
        """, (email,))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error verifying code: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def record_failed_attempt(email, code):
    """Record failed verification attempt"""
    code_hash = hash_code(code)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE email_verification_codes
            SET attempts = attempts + 1
            WHERE email = ? AND code_hash = ?
        """, (email, code_hash))
        
        conn.commit()
    
    except Exception as e:
        print(f"Error recording failed attempt: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def log_email_auth_event(email, action, ip_address="", user_agent="", success=True, details=None):
    """Log email authentication event"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO email_auth_audit
            (email, action, ip_address, user_agent, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email, action, ip_address, user_agent, 1 if success else 0, 
              json.dumps(details) if details else None))
        
        conn.commit()
    
    except Exception as e:
        print(f"Error logging event: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def check_rate_limit(email, hours=1, max_codes=3):
    """
    Check if email has exceeded rate limit
    
    Args:
        email (str): Email address
        hours (int): Time window in hours
        max_codes (int): Max codes allowed in time window
    
    Returns:
        bool: True if within limit, False if exceeded
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM email_verification_codes
            WHERE email = ? AND created_at > ?
        """, (email, since))
        
        row = cursor.fetchone()
        count = row['count'] if row else 0
        
        return count < max_codes
    
    finally:
        conn.close()

def email_exists(email):
    """Check if email exists in database"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users_email WHERE email = ?", (email,))
        return cursor.fetchone() is not None
    
    finally:
        conn.close()

def create_email_user(email):
    """Create new email user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO users_email (email, is_verified, is_active)
            VALUES (?, 1, 1)
        """, (email,))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error creating email user: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def send_verification_email(email, ip_address=""):
    """
    Generate code and send verification email
    
    Args:
        email (str): Email address
        ip_address (str): IP address of requester
    
    Returns:
        tuple: (success: bool, code: str or None, expires_at: datetime or None)
    """
    # Check rate limit
    if not check_rate_limit(email):
        log_email_auth_event(email, 'rate_limited', ip_address, success=False)
        return False, None, None
    
    # Generate and store code
    code, expires_at = create_verification_code(email, ip_address)
    
    if not code:
        log_email_auth_event(email, 'code_generation_failed', ip_address, success=False)
        return False, None, None
    
    # Send email via automated methods
    success = automated_email_service.send_verification_email(email, code, ip_address)
    
    if success:
        log_email_auth_event(email, 'code_sent', ip_address, success=True)
        return True, code, expires_at
    else:
        log_email_auth_event(email, 'email_send_failed', ip_address, success=False)
        return False, None, None

def cleanup_expired_codes():
    """Clean up expired verification codes"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM email_verification_codes
            WHERE expires_at < CURRENT_TIMESTAMP
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} expired verification codes")
    
    except Exception as e:
        print(f"Error cleaning up expired codes: {e}")
        conn.rollback()
    
    finally:
        conn.close()

# Utility function for getting remote address
def get_remote_address():
    """Get remote IP address from Flask request"""
    try:
        from flask import request
        return request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    except:
        return 'unknown'