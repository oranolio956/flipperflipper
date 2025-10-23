#!/usr/bin/env python3
"""
MFA Database Operations
Helper functions for storing and retrieving MFA data
Elite passwordless authentication system
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import Config

DB_PATH = Config.APPLICATION_DIR / 'stitch.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def get_user_mfa_status(email):
    """
    Check if user has MFA enabled
    
    Args:
        email (str): Email address to check
    
    Returns:
        dict: {
            'exists': bool,
            'enabled': bool,
            'secret': str or None
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT mfa_enabled, mfa_secret FROM user_mfa WHERE email = ?",
        (email,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return {'exists': False, 'enabled': False, 'secret': None}
    
    return {
        'exists': True,
        'enabled': bool(row['mfa_enabled']),
        'secret': row['mfa_secret']
    }

def save_user_mfa(email, encrypted_secret, hashed_backup_codes_json):
    """
    Save MFA configuration for user
    
    Args:
        email (str): Email address
        encrypted_secret (str): Encrypted TOTP secret
        hashed_backup_codes_json (str): JSON array of hashed backup codes
    
    Returns:
        bool: Success
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO user_mfa 
            (email, mfa_secret, mfa_enabled, backup_codes, updated_at)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
        """, (email, encrypted_secret, hashed_backup_codes_json))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Error saving MFA: {e}")
        conn.rollback()
        conn.close()
        return False

def get_user_mfa_config(email):
    """
    Get full MFA configuration for user
    
    Args:
        email (str): Email address
    
    Returns:
        dict or None: MFA configuration
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM user_mfa WHERE email = ?",
        (email,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return dict(row)

def update_user_backup_codes(email, new_backup_codes_json):
    """
    Update backup codes for user (after one is used)
    
    Args:
        email (str): Email address
        new_backup_codes_json (str): JSON array of remaining hashed codes
    
    Returns:
        bool: Success
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE user_mfa 
            SET backup_codes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (new_backup_codes_json, email))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Error updating backup codes: {e}")
        conn.rollback()
        conn.close()
        return False

def log_mfa_event(email, action, ip_address, user_agent="", success=True, details=None):
    """
    Log MFA event to audit log
    
    Args:
        email (str): Email address
        action (str): Action type ('setup', 'verify_success', 'verify_fail', etc.)
        ip_address (str): IP address
        user_agent (str): User agent string
        success (bool): Whether action succeeded
        details (dict): Additional details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO mfa_audit_log 
            (email, action, ip_address, user_agent, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            email,
            action,
            ip_address,
            user_agent,
            1 if success else 0,
            json.dumps(details) if details else None
        ))
        
        conn.commit()
    
    except Exception as e:
        print(f"⚠️  Error logging MFA event: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def disable_user_mfa(email):
    """
    Disable MFA for user (admin function)
    
    Args:
        email (str): Email address
    
    Returns:
        bool: Success
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE user_mfa 
            SET mfa_enabled = 0
            WHERE email = ?
        """, (email,))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Error disabling MFA: {e}")
        conn.rollback()
        conn.close()
        return False

def delete_user_mfa(email):
    """
    Completely remove MFA configuration for user
    
    Args:
        email (str): Email address
    
    Returns:
        bool: Success
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM user_mfa WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Error deleting MFA: {e}")
        conn.rollback()
        conn.close()
        return False

def get_mfa_audit_logs(email=None, limit=100):
    """
    Get MFA audit logs
    
    Args:
        email (str, optional): Filter by email address
        limit (int): Maximum number of records to return
    
    Returns:
        list: List of audit log entries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if email:
            cursor.execute("""
                SELECT * FROM mfa_audit_log 
                WHERE email = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (email, limit))
        else:
            cursor.execute("""
                SELECT * FROM mfa_audit_log 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    finally:
        conn.close()

def update_mfa_last_used(email):
    """
    Update last used timestamp for MFA
    
    Args:
        email (str): Email address
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE user_mfa 
            SET last_used = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (email,))
        
        conn.commit()
    
    except Exception as e:
        print(f"⚠️  Error updating MFA last used: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def get_mfa_statistics():
    """
    Get MFA usage statistics
    
    Returns:
        dict: Statistics about MFA usage
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Count total users with MFA enabled
        cursor.execute("SELECT COUNT(*) as count FROM user_mfa WHERE mfa_enabled = 1")
        enabled_count = cursor.fetchone()['count']
        
        # Count total MFA events today
        cursor.execute("""
            SELECT COUNT(*) as count FROM mfa_audit_log 
            WHERE DATE(timestamp) = DATE('now')
        """)
        events_today = cursor.fetchone()['count']
        
        # Count successful verifications today
        cursor.execute("""
            SELECT COUNT(*) as count FROM mfa_audit_log 
            WHERE DATE(timestamp) = DATE('now') 
            AND action LIKE '%verify%' 
            AND success = 1
        """)
        successful_today = cursor.fetchone()['count']
        
        return {
            'enabled_users': enabled_count,
            'events_today': events_today,
            'successful_verifications_today': successful_today
        }
    
    finally:
        conn.close()