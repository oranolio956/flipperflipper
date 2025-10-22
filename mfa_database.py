#!/usr/bin/env python3
"""
MFA Database Operations
Database layer for TOTP and backup codes management
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from mfa_manager import mfa_manager

logger = logging.getLogger(__name__)

# Database path
DB_PATH = '/workspace/Application/stitch.db'

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def get_user_mfa_status(email):
    """
    Get user MFA status and settings
    
    Args:
        email (str): User email
    
    Returns:
        dict: MFA status information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT mfa_secret, is_enabled, setup_completed_at, last_totp_used, recovery_codes_used
            FROM user_mfa 
            WHERE email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            mfa_secret, is_enabled, setup_completed_at, last_totp_used, recovery_codes_used = result
            return {
                'enabled': bool(is_enabled),
                'secret': mfa_secret,
                'setup_completed_at': setup_completed_at,
                'last_totp_used': last_totp_used,
                'recovery_codes_used': recovery_codes_used
            }
        else:
            return {
                'enabled': False,
                'secret': None,
                'setup_completed_at': None,
                'last_totp_used': 0,
                'recovery_codes_used': 0
            }
    
    except Exception as e:
        logger.error(f"Error getting MFA status: {e}")
        return {'enabled': False, 'secret': None}

def setup_user_mfa(email):
    """
    Initialize MFA setup for user
    
    Args:
        email (str): User email
    
    Returns:
        dict: Setup information (secret, qr_code)
    """
    try:
        # Generate new TOTP secret
        secret = mfa_manager.generate_totp_secret()
        encrypted_secret = mfa_manager.encrypt_secret(secret)
        
        if not encrypted_secret:
            return None
        
        # Generate QR code
        qr_code = mfa_manager.generate_qr_code(email, secret)
        
        if not qr_code:
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert or update MFA record
        cursor.execute('''
            INSERT OR REPLACE INTO user_mfa 
            (email, mfa_secret, is_enabled, created_at, updated_at)
            VALUES (?, ?, 0, ?, ?)
        ''', (email, encrypted_secret, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ MFA setup initialized for {email}")
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'encrypted_secret': encrypted_secret
        }
    
    except Exception as e:
        logger.error(f"Error setting up MFA: {e}")
        return None

def complete_mfa_setup(email, totp_token):
    """
    Complete MFA setup by verifying first TOTP token
    
    Args:
        email (str): User email
        totp_token (str): TOTP token to verify
    
    Returns:
        dict: Setup completion result with backup codes
    """
    try:
        # Get user's encrypted secret
        mfa_status = get_user_mfa_status(email)
        if not mfa_status['secret']:
            return {'success': False, 'error': 'MFA not initialized'}
        
        # Decrypt secret
        secret = mfa_manager.decrypt_secret(mfa_status['secret'])
        if not secret:
            return {'success': False, 'error': 'Failed to decrypt secret'}
        
        # Verify TOTP token
        if not mfa_manager.verify_totp(secret, totp_token):
            log_mfa_event(email, 'setup_verify_failed', '', success=False, 
                         failure_reason='Invalid TOTP token')
            return {'success': False, 'error': 'Invalid TOTP token'}
        
        # Generate backup codes
        backup_codes = mfa_manager.generate_backup_codes()
        
        # Store backup codes
        success = store_backup_codes(email, backup_codes)
        if not success:
            return {'success': False, 'error': 'Failed to store backup codes'}
        
        # Enable MFA
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_mfa 
            SET is_enabled = 1, setup_completed_at = ?, updated_at = ?
            WHERE email = ?
        ''', (datetime.now(), datetime.now(), email))
        
        conn.commit()
        conn.close()
        
        # Log success
        log_mfa_event(email, 'setup_completed', '', success=True)
        
        logger.info(f"✅ MFA setup completed for {email}")
        
        return {
            'success': True,
            'backup_codes': backup_codes
        }
    
    except Exception as e:
        logger.error(f"Error completing MFA setup: {e}")
        return {'success': False, 'error': 'Setup failed'}

def store_backup_codes(email, codes):
    """Store backup codes in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing backup codes
        cursor.execute('DELETE FROM mfa_backup_codes WHERE email = ?', (email,))
        
        # Store new codes
        for code in codes:
            code_hash = mfa_manager.hash_backup_code(code)
            cursor.execute('''
                INSERT INTO mfa_backup_codes (email, code_hash, created_at)
                VALUES (?, ?, ?)
            ''', (email, code_hash, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Error storing backup codes: {e}")
        return False

def verify_mfa_token(email, token, ip_address=""):
    """
    Verify MFA token (TOTP or backup code)
    
    Args:
        email (str): User email
        token (str): TOTP token or backup code
        ip_address (str): IP address
    
    Returns:
        dict: Verification result
    """
    try:
        # Get MFA status
        mfa_status = get_user_mfa_status(email)
        if not mfa_status['enabled']:
            return {'success': False, 'error': 'MFA not enabled'}
        
        # Try TOTP first
        secret = mfa_manager.decrypt_secret(mfa_status['secret'])
        if secret and mfa_manager.validate_totp_format(token):
            if mfa_manager.verify_totp(secret, token):
                # Update last TOTP used timestamp
                update_last_totp_used(email)
                log_mfa_event(email, 'totp_verified', ip_address, success=True)
                return {'success': True, 'method': 'totp'}
        
        # Try backup code
        if verify_backup_code_and_mark_used(email, token):
            log_mfa_event(email, 'backup_code_used', ip_address, success=True)
            return {'success': True, 'method': 'backup_code'}
        
        # Both failed
        log_mfa_event(email, 'mfa_verify_failed', ip_address, success=False,
                     failure_reason='Invalid token')
        return {'success': False, 'error': 'Invalid token'}
    
    except Exception as e:
        logger.error(f"Error verifying MFA token: {e}")
        return {'success': False, 'error': 'Verification failed'}

def verify_backup_code_and_mark_used(email, code):
    """Verify backup code and mark as used"""
    try:
        code_hash = mfa_manager.hash_backup_code(code)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find unused backup code
        cursor.execute('''
            SELECT id FROM mfa_backup_codes 
            WHERE email = ? AND code_hash = ? AND is_used = 0
        ''', (email, code_hash))
        
        result = cursor.fetchone()
        
        if result:
            code_id = result[0]
            
            # Mark as used
            cursor.execute('''
                UPDATE mfa_backup_codes 
                SET is_used = 1, used_at = ? 
                WHERE id = ?
            ''', (datetime.now(), code_id))
            
            # Update recovery codes used count
            cursor.execute('''
                UPDATE user_mfa 
                SET recovery_codes_used = recovery_codes_used + 1, updated_at = ?
                WHERE email = ?
            ''', (datetime.now(), email))
            
            conn.commit()
            conn.close()
            
            return True
        
        conn.close()
        return False
    
    except Exception as e:
        logger.error(f"Error verifying backup code: {e}")
        return False

def update_last_totp_used(email):
    """Update last TOTP used timestamp"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_mfa 
            SET last_totp_used = ?, updated_at = ?
            WHERE email = ?
        ''', (int(datetime.now().timestamp()), datetime.now(), email))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating last TOTP used: {e}")

def get_remaining_backup_codes_count(email):
    """Get count of remaining unused backup codes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM mfa_backup_codes 
            WHERE email = ? AND is_used = 0
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    except Exception as e:
        logger.error(f"Error getting backup codes count: {e}")
        return 0

def regenerate_backup_codes(email):
    """Regenerate backup codes for user"""
    try:
        # Generate new codes
        backup_codes = mfa_manager.generate_backup_codes()
        
        # Store new codes (this clears old ones)
        success = store_backup_codes(email, backup_codes)
        
        if success:
            # Reset recovery codes used count
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_mfa 
                SET recovery_codes_used = 0, updated_at = ?
                WHERE email = ?
            ''', (datetime.now(), email))
            
            conn.commit()
            conn.close()
            
            log_mfa_event(email, 'backup_codes_regenerated', '', success=True)
            
            return backup_codes
        
        return None
    
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {e}")
        return None

def disable_user_mfa(email):
    """Disable MFA for user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Disable MFA
        cursor.execute('''
            UPDATE user_mfa 
            SET is_enabled = 0, updated_at = ?
            WHERE email = ?
        ''', (datetime.now(), email))
        
        # Clear backup codes
        cursor.execute('DELETE FROM mfa_backup_codes WHERE email = ?', (email,))
        
        conn.commit()
        conn.close()
        
        log_mfa_event(email, 'mfa_disabled', '', success=True)
        
        return True
    
    except Exception as e:
        logger.error(f"Error disabling MFA: {e}")
        return False

def log_mfa_event(email, event_type, ip_address, success=True, totp_code=None, failure_reason=None, user_agent=""):
    """Log MFA event to audit log"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO mfa_audit_log 
            (email, event_type, ip_address, user_agent, totp_code, success, failure_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, event_type, ip_address, user_agent, totp_code, success, failure_reason, datetime.now()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging MFA event: {e}")

def cleanup_mfa_sessions():
    """Clean up expired MFA sessions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mark expired sessions as inactive
        cursor.execute('''
            UPDATE mfa_sessions 
            SET is_active = 0 
            WHERE expires_at < ? AND is_active = 1
        ''', (datetime.now(),))
        
        expired_count = cursor.rowcount
        
        # Clean up old audit logs (keep 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        cursor.execute('''
            DELETE FROM mfa_audit_log 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        
        audit_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"🧹 Cleaned up {expired_count} expired MFA sessions and {audit_deleted} old audit logs")
        
    except Exception as e:
        logger.error(f"Error cleaning up MFA sessions: {e}")

def get_mfa_stats(email):
    """Get MFA statistics for user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # MFA info
        mfa_status = get_user_mfa_status(email)
        
        # Backup codes count
        remaining_codes = get_remaining_backup_codes_count(email)
        
        # Recent events
        cursor.execute('''
            SELECT event_type, success, timestamp 
            FROM mfa_audit_log 
            WHERE email = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (email,))
        
        recent_events = cursor.fetchall()
        
        conn.close()
        
        return {
            'mfa_status': mfa_status,
            'remaining_backup_codes': remaining_codes,
            'recent_events': recent_events
        }
    
    except Exception as e:
        logger.error(f"Error getting MFA stats: {e}")
        return None