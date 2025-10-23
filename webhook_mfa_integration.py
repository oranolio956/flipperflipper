#!/usr/bin/env python3
"""
Webhook MFA Integration
Integrates MFA setup and verification with webhook authentication
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from mfa_manager import mfa_manager
from config import Config

class WebhookMFAIntegration:
    """
    Handles MFA setup and verification for webhook-authenticated users
    """
    
    def __init__(self):
        """Initialize MFA integration"""
        self.db_path = Config.APPLICATION_DIR / 'webhook_mfa.db'
        self._init_database()
    
    def _init_database(self):
        """Initialize MFA database"""
        try:
            Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_mfa (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_identifier TEXT UNIQUE NOT NULL,
                        totp_secret_encrypted TEXT,
                        backup_codes_encrypted TEXT,
                        mfa_enabled BOOLEAN DEFAULT FALSE,
                        setup_completed_at TEXT,
                        last_used_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS mfa_verification_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_identifier TEXT NOT NULL,
                        verification_type TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Error initializing MFA database: {e}")
    
    def is_mfa_required(self, user_identifier: str) -> bool:
        """Check if MFA setup is required for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT mfa_enabled FROM user_mfa WHERE user_identifier = ?',
                    (user_identifier,)
                )
                result = cursor.fetchone()
                
                if result is None:
                    # User not in database, MFA required
                    return True
                
                return not result[0]  # MFA required if not enabled
                
        except Exception as e:
            print(f"Error checking MFA requirement: {e}")
            return True  # Default to requiring MFA on error
    
    def setup_mfa(self, user_identifier: str) -> dict:
        """Set up MFA for user"""
        try:
            # Generate TOTP secret
            secret = mfa_manager.generate_secret()
            encrypted_secret = mfa_manager.encrypt_secret(secret)
            
            # Generate backup codes
            backup_codes = mfa_manager.generate_backup_codes()
            hashed_backup_codes = [mfa_manager.hash_backup_code(code) for code in backup_codes]
            encrypted_backup_codes = mfa_manager.encrypt_secret(json.dumps(hashed_backup_codes))
            
            # Generate QR code
            provisioning_uri = mfa_manager.get_provisioning_uri(user_identifier, secret)
            qr_code_data = mfa_manager.generate_qr_code(provisioning_uri)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_mfa 
                    (user_identifier, totp_secret_encrypted, backup_codes_encrypted, 
                     mfa_enabled, setup_completed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_identifier,
                    encrypted_secret,
                    encrypted_backup_codes,
                    False,  # Not enabled until verified
                    None
                ))
                conn.commit()
            
            return {
                'success': True,
                'secret': secret,
                'provisioning_uri': provisioning_uri,
                'qr_code': qr_code_data,
                'backup_codes': backup_codes,
                'message': 'MFA setup initiated. Scan QR code with your authenticator app.'
            }
            
        except Exception as e:
            print(f"Error setting up MFA: {e}")
            return {
                'success': False,
                'message': 'Failed to set up MFA. Please try again.'
            }
    
    def verify_mfa_setup(self, user_identifier: str, token: str) -> dict:
        """Verify MFA setup with initial token"""
        try:
            # Get user's encrypted secret
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT totp_secret_encrypted FROM user_mfa WHERE user_identifier = ?',
                    (user_identifier,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'message': 'MFA setup not found. Please start over.'
                    }
                
                encrypted_secret = result[0]
                secret = mfa_manager.decrypt_secret(encrypted_secret)
                
                # Verify token
                if mfa_manager.verify_token(secret, token):
                    # Enable MFA
                    conn.execute('''
                        UPDATE user_mfa 
                        SET mfa_enabled = TRUE, setup_completed_at = ?
                        WHERE user_identifier = ?
                    ''', (datetime.now().isoformat(), user_identifier))
                    conn.commit()
                    
                    return {
                        'success': True,
                        'message': 'MFA setup completed successfully!'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Invalid verification code. Please try again.'
                    }
                    
        except Exception as e:
            print(f"Error verifying MFA setup: {e}")
            return {
                'success': False,
                'message': 'Failed to verify MFA setup. Please try again.'
            }
    
    def verify_mfa_login(self, user_identifier: str, token: str, ip_address: str = None, user_agent: str = None) -> dict:
        """Verify MFA token for login"""
        try:
            # Get user's encrypted secret
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT totp_secret_encrypted, mfa_enabled FROM user_mfa WHERE user_identifier = ?',
                    (user_identifier,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'message': 'MFA not configured for this user.'
                    }
                
                encrypted_secret, mfa_enabled = result
                
                if not mfa_enabled:
                    return {
                        'success': False,
                        'message': 'MFA not enabled for this user.'
                    }
                
                secret = mfa_manager.decrypt_secret(encrypted_secret)
                
                # Verify token
                if mfa_manager.verify_token(secret, token):
                    # Log successful verification
                    conn.execute('''
                        INSERT INTO mfa_verification_logs 
                        (user_identifier, verification_type, success, ip_address, user_agent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_identifier, 'totp', True, ip_address, user_agent))
                    
                    # Update last used
                    conn.execute('''
                        UPDATE user_mfa SET last_used_at = ? WHERE user_identifier = ?
                    ''', (datetime.now().isoformat(), user_identifier))
                    
                    conn.commit()
                    
                    return {
                        'success': True,
                        'message': 'MFA verification successful!'
                    }
                else:
                    # Log failed verification
                    conn.execute('''
                        INSERT INTO mfa_verification_logs 
                        (user_identifier, verification_type, success, ip_address, user_agent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_identifier, 'totp', False, ip_address, user_agent))
                    conn.commit()
                    
                    return {
                        'success': False,
                        'message': 'Invalid verification code. Please try again.'
                    }
                    
        except Exception as e:
            print(f"Error verifying MFA login: {e}")
            return {
                'success': False,
                'message': 'Failed to verify MFA. Please try again.'
            }
    
    def verify_backup_code(self, user_identifier: str, code: str, ip_address: str = None, user_agent: str = None) -> dict:
        """Verify backup code for login"""
        try:
            # Get user's encrypted backup codes
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT backup_codes_encrypted, mfa_enabled FROM user_mfa WHERE user_identifier = ?',
                    (user_identifier,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'message': 'MFA not configured for this user.'
                    }
                
                encrypted_backup_codes, mfa_enabled = result
                
                if not mfa_enabled:
                    return {
                        'success': False,
                        'message': 'MFA not enabled for this user.'
                    }
                
                hashed_codes_json = mfa_manager.decrypt_secret(encrypted_backup_codes)
                
                # Verify backup code
                is_valid, remaining_codes_json = mfa_manager.verify_backup_code(code, hashed_codes_json)
                
                if is_valid:
                    # Update backup codes
                    encrypted_remaining = mfa_manager.encrypt_secret(remaining_codes_json)
                    conn.execute('''
                        UPDATE user_mfa SET backup_codes_encrypted = ?, last_used_at = ?
                        WHERE user_identifier = ?
                    ''', (encrypted_remaining, datetime.now().isoformat(), user_identifier))
                    
                    # Log successful verification
                    conn.execute('''
                        INSERT INTO mfa_verification_logs 
                        (user_identifier, verification_type, success, ip_address, user_agent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_identifier, 'backup_code', True, ip_address, user_agent))
                    
                    conn.commit()
                    
                    remaining_count = mfa_manager.get_remaining_backup_codes_count(remaining_codes_json)
                    
                    return {
                        'success': True,
                        'message': f'Backup code verified successfully! {remaining_count} codes remaining.',
                        'remaining_codes': remaining_count
                    }
                else:
                    # Log failed verification
                    conn.execute('''
                        INSERT INTO mfa_verification_logs 
                        (user_identifier, verification_type, success, ip_address, user_agent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_identifier, 'backup_code', False, ip_address, user_agent))
                    conn.commit()
                    
                    return {
                        'success': False,
                        'message': 'Invalid backup code. Please try again.'
                    }
                    
        except Exception as e:
            print(f"Error verifying backup code: {e}")
            return {
                'success': False,
                'message': 'Failed to verify backup code. Please try again.'
            }
    
    def get_mfa_status(self, user_identifier: str) -> dict:
        """Get MFA status for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT mfa_enabled, setup_completed_at, last_used_at
                    FROM user_mfa WHERE user_identifier = ?
                ''', (user_identifier,))
                result = cursor.fetchone()
                
                if not result:
                    return {
                        'mfa_enabled': False,
                        'setup_required': True,
                        'setup_completed_at': None,
                        'last_used_at': None
                    }
                
                mfa_enabled, setup_completed_at, last_used_at = result
                
                return {
                    'mfa_enabled': bool(mfa_enabled),
                    'setup_required': not bool(mfa_enabled),
                    'setup_completed_at': setup_completed_at,
                    'last_used_at': last_used_at
                }
                
        except Exception as e:
            print(f"Error getting MFA status: {e}")
            return {
                'mfa_enabled': False,
                'setup_required': True,
                'setup_completed_at': None,
                'last_used_at': None
            }
    
    def get_verification_logs(self, user_identifier: str, limit: int = 10) -> list:
        """Get verification logs for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT verification_type, success, ip_address, created_at
                    FROM mfa_verification_logs 
                    WHERE user_identifier = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_identifier, limit))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        'verification_type': row[0],
                        'success': bool(row[1]),
                        'ip_address': row[2],
                        'created_at': row[3]
                    })
                
                return logs
                
        except Exception as e:
            print(f"Error getting verification logs: {e}")
            return []

# Global instance
webhook_mfa = WebhookMFAIntegration()