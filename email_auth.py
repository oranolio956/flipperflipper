#!/usr/bin/env python3
"""
Email Authentication System
Ultra-secure passwordless authentication with Mailjet
"""

import sqlite3
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from email_manager_mailjet import email_manager

logger = logging.getLogger(__name__)

# Database path
DB_PATH = '/workspace/Application/stitch.db'

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def email_exists(email):
    """Check if email exists in users_email table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users_email WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
        
    except Exception as e:
        logger.error(f"Error checking email existence: {e}")
        return False

def create_email_user(email):
    """Create new email user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users_email (email, created_at, is_active)
            VALUES (?, ?, ?)
        ''', (email, datetime.now(), True))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Created new email user: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating email user: {e}")
        return False

def check_rate_limit(email, max_requests=3, window_hours=1):
    """
    Check rate limiting for email verification requests
    
    Args:
        email (str): Email address
        max_requests (int): Maximum requests per window
        window_hours (int): Time window in hours
    
    Returns:
        bool: True if within rate limit, False if exceeded
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clean up old rate limit records
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        cursor.execute('''
            DELETE FROM email_rate_limits 
            WHERE window_start < ? AND blocked_until IS NULL
        ''', (cutoff_time,))
        
        # Check current rate limit
        cursor.execute('''
            SELECT request_count, blocked_until 
            FROM email_rate_limits 
            WHERE email = ? AND window_start > ?
        ''', (email, cutoff_time))
        
        result = cursor.fetchone()
        
        if result:
            request_count, blocked_until = result
            
            # Check if blocked
            if blocked_until and datetime.fromisoformat(blocked_until) > datetime.now():
                conn.close()
                return False
            
            # Check if exceeded limit
            if request_count >= max_requests:
                # Block for 1 hour
                block_until = datetime.now() + timedelta(hours=1)
                cursor.execute('''
                    UPDATE email_rate_limits 
                    SET blocked_until = ? 
                    WHERE email = ?
                ''', (block_until, email))
                conn.commit()
                conn.close()
                return False
            
            # Increment counter
            cursor.execute('''
                UPDATE email_rate_limits 
                SET request_count = request_count + 1 
                WHERE email = ?
            ''', (email,))
        else:
            # Create new rate limit record
            cursor.execute('''
                INSERT INTO email_rate_limits (email, request_count, window_start)
                VALUES (?, 1, ?)
            ''', (email, datetime.now()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return False

def create_verification_code(email, ip_address=""):
    """
    Create and store verification code
    
    Args:
        email (str): Email address
        ip_address (str): IP address of request
    
    Returns:
        tuple: (code, expires_at) or (None, None) on error
    """
    try:
        # Generate 6-digit code
        code = email_manager.generate_code()
        code_hash = email_manager.hash_code(code)
        
        # Set expiration (10 minutes)
        expires_at = datetime.now() + timedelta(minutes=10)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clean up old codes for this email
        cursor.execute('''
            DELETE FROM email_verification_codes 
            WHERE email = ? AND (expires_at < ? OR is_used = 1)
        ''', (email, datetime.now()))
        
        # Store new code
        cursor.execute('''
            INSERT INTO email_verification_codes 
            (email, code_hash, ip_address, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (email, code_hash, ip_address, expires_at))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Created verification code for {email}")
        return code, expires_at
        
    except Exception as e:
        logger.error(f"Error creating verification code: {e}")
        return None, None

def verify_code(email, code):
    """
    Verify email verification code
    
    Args:
        email (str): Email address
        code (str): Verification code to check
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        code_hash = email_manager.hash_code(code)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find matching code
        cursor.execute('''
            SELECT id, expires_at, is_used, attempts 
            FROM email_verification_codes 
            WHERE email = ? AND code_hash = ?
        ''', (email, code_hash))
        
        result = cursor.fetchone()
        
        if not result:
            # Log failed attempt
            log_email_auth_event(email, 'code_verify_failed', '', success=False, details='Code not found')
            conn.close()
            return False
        
        code_id, expires_at_str, is_used, attempts = result
        expires_at = datetime.fromisoformat(expires_at_str)
        
        # Check if already used
        if is_used:
            log_email_auth_event(email, 'code_verify_failed', '', success=False, details='Code already used')
            conn.close()
            return False
        
        # Check if expired
        if datetime.now() > expires_at:
            log_email_auth_event(email, 'code_verify_failed', '', success=False, details='Code expired')
            conn.close()
            return False
        
        # Mark as used
        cursor.execute('''
            UPDATE email_verification_codes 
            SET is_used = 1, used_at = ? 
            WHERE id = ?
        ''', (datetime.now(), code_id))
        
        # Update user last login
        cursor.execute('''
            UPDATE users_email 
            SET last_login = ?, failed_attempts = 0 
            WHERE email = ?
        ''', (datetime.now(), email))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Code verified successfully for {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        return False

def record_failed_attempt(email, code):
    """Record failed verification attempt"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Increment failed attempts
        cursor.execute('''
            UPDATE users_email 
            SET failed_attempts = failed_attempts + 1 
            WHERE email = ?
        ''', (email,))
        
        # Check if should lock account (5 failed attempts)
        cursor.execute('''
            SELECT failed_attempts FROM users_email WHERE email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        if result and result[0] >= 5:
            # Lock for 15 minutes
            lock_until = datetime.now() + timedelta(minutes=15)
            cursor.execute('''
                UPDATE users_email 
                SET locked_until = ? 
                WHERE email = ?
            ''', (lock_until, email))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error recording failed attempt: {e}")

def log_email_auth_event(email, event_type, ip_address, success=True, details="", user_agent=""):
    """Log authentication event"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_auth_audit 
            (email, event_type, ip_address, user_agent, success, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email, event_type, ip_address, user_agent, success, details, datetime.now()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging auth event: {e}")

def cleanup_expired_codes():
    """Clean up expired verification codes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete expired codes
        cursor.execute('''
            DELETE FROM email_verification_codes 
            WHERE expires_at < ? OR is_used = 1
        ''', (datetime.now(),))
        
        deleted = cursor.rowcount
        
        # Clean up old audit logs (keep 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        cursor.execute('''
            DELETE FROM email_auth_audit 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        
        audit_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"🧹 Cleaned up {deleted} expired codes and {audit_deleted} old audit logs")
        
    except Exception as e:
        logger.error(f"Error cleaning up expired codes: {e}")

def get_user_stats(email):
    """Get user authentication statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # User info
        cursor.execute('''
            SELECT created_at, last_login, failed_attempts, locked_until 
            FROM users_email WHERE email = ?
        ''', (email,))
        
        user_info = cursor.fetchone()
        
        # Recent audit events
        cursor.execute('''
            SELECT event_type, success, timestamp 
            FROM email_auth_audit 
            WHERE email = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (email,))
        
        recent_events = cursor.fetchall()
        
        conn.close()
        
        return {
            'user_info': user_info,
            'recent_events': recent_events
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return None

# Utility function for web app
def get_remote_address():
    """Get remote IP address from Flask request"""
    try:
        from flask import request
        return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    except:
        return '127.0.0.1'