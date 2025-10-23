#!/usr/bin/env python3
"""
Multi-Factor Authentication Manager
Handles TOTP setup, verification, and backup codes
Elite passwordless authentication system
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
from config import Config

class MFAManager:
    """
    Main class for handling all MFA operations
    """
    
    def __init__(self):
        """Initialize MFA manager with encryption"""
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.issuer_name = Config.APP_NAME  # "Oranolio RAT"
    
    def _get_encryption_key(self):
        """
        Get or generate encryption key for TOTP secrets
        
        The TOTP secret is sensitive and must be encrypted before storing.
        This function ensures we have a persistent encryption key.
        
        Returns:
            bytes: Fernet encryption key
        """
        key_file = Config.APPLICATION_DIR / '.mfa_encryption_key'
        
        # Check if key already exists
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                    # Verify it's a valid Fernet key
                    Fernet(key)  # Will raise exception if invalid
                    return key
            except Exception as e:
                print(f"⚠️  Existing MFA key invalid: {e}")
                print("   Generating new key (existing MFA setups will be invalidated)")
        
        # Generate new encryption key
        key = Fernet.generate_key()
        
        try:
            # Ensure directory exists
            Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save key to file
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions (Unix/Linux only)
            try:
                os.chmod(key_file, 0o600)  # Owner read/write only
                print(f"✅ MFA encryption key generated: {key_file}")
            except Exception:
                print(f"✅ MFA encryption key generated: {key_file}")
                print("   (Could not set file permissions on Windows)")
        
        except Exception as e:
            print(f"❌ ERROR: Could not save MFA encryption key: {e}")
            print("   MFA will not work correctly!")
            raise
        
        return key
    
    def generate_secret(self):
        """
        Generate a new TOTP secret
        
        This is a random base32-encoded string that will be shared between
        the server and the user's authenticator app.
        
        Returns:
            str: Base32-encoded secret (e.g., "JBSWY3DPEHPK3PXP")
        """
        return pyotp.random_base32()
    
    def encrypt_secret(self, secret):
        """
        Encrypt TOTP secret for storage in database
        
        Args:
            secret (str): Plain TOTP secret
        
        Returns:
            str: Encrypted secret (safe to store)
        """
        encrypted_bytes = self.cipher.encrypt(secret.encode())
        return encrypted_bytes.decode('utf-8')
    
    def decrypt_secret(self, encrypted_secret):
        """
        Decrypt TOTP secret from database
        
        Args:
            encrypted_secret (str): Encrypted secret from database
        
        Returns:
            str: Plain TOTP secret
        """
        decrypted_bytes = self.cipher.decrypt(encrypted_secret.encode())
        return decrypted_bytes.decode('utf-8')
    
    def get_provisioning_uri(self, username, secret):
        """
        Generate provisioning URI for QR code
        
        This URI encodes all information needed by the authenticator app:
        - The secret
        - The account name (username)
        - The issuer (app name)
        
        Format: otpauth://totp/Issuer:username?secret=SECRET&issuer=Issuer
        
        Args:
            username (str): User's username/email
            secret (str): TOTP secret
        
        Returns:
            str: Provisioning URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )
    
    def generate_qr_code(self, provisioning_uri):
        """
        Generate QR code image from provisioning URI
        
        Creates a PNG image of the QR code and converts it to base64
        for easy embedding in HTML.
        
        Args:
            provisioning_uri (str): The provisioning URI
        
        Returns:
            str: Data URI for <img> tag (data:image/png;base64,...)
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=1,  # Size (1 = 21x21 modules)
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,  # Pixels per module
            border=4,     # Modules on border
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def verify_token(self, secret, token):
        """
        Verify a TOTP token
        
        Checks if the provided 6-digit token is valid for the secret.
        Allows 1 time step (30 seconds) before/after current time to
        account for clock drift.
        
        Args:
            secret (str): TOTP secret
            token (str): 6-digit code from user
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not token or not secret:
            return False
        
        # Remove spaces and ensure it's 6 digits
        token = token.replace(' ', '').strip()
        
        if len(token) != 6 or not token.isdigit():
            return False
        
        totp = pyotp.TOTP(secret)
        
        # Verify with 1 window = ±30 seconds tolerance
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count=10):
        """
        Generate backup recovery codes
        
        Creates random 8-character codes for account recovery.
        Uses characters safe for typing: uppercase letters and numbers,
        excluding easily confused characters (0, O, 1, I, L).
        
        Args:
            count (int): Number of codes to generate (default: 10)
        
        Returns:
            list: List of backup codes (e.g., ["ABCD1234", "EFGH5678", ...])
        """
        # Character set: no easily confused characters
        charset = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(charset) for _ in range(8))
            codes.append(code)
        
        return codes
    
    def hash_backup_code(self, code):
        """
        Hash a backup code for secure storage
        
        Backup codes are hashed like passwords - we never store them plain.
        
        Args:
            code (str): Backup code to hash
        
        Returns:
            str: SHA-256 hash of the code
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    def verify_backup_code(self, code, hashed_codes_json):
        """
        Verify a backup code and remove it from the list
        
        Backup codes are one-time use. After verification, the code
        is removed from the database.
        
        Args:
            code (str): Code entered by user
            hashed_codes_json (str): JSON array of hashed codes from database
        
        Returns:
            tuple: (is_valid: bool, remaining_codes_json: str)
        """
        # Parse hashed codes from JSON
        try:
            hashed_codes = json.loads(hashed_codes_json)
        except:
            return False, hashed_codes_json
        
        # Hash the provided code
        code_hash = self.hash_backup_code(code.strip().upper())
        
        # Check if it matches any stored hash
        if code_hash in hashed_codes:
            # Remove the used code
            hashed_codes.remove(code_hash)
            return True, json.dumps(hashed_codes)
        
        return False, hashed_codes_json
    
    def get_remaining_backup_codes_count(self, hashed_codes_json):
        """
        Get count of remaining backup codes
        
        Args:
            hashed_codes_json (str): JSON array of hashed codes
        
        Returns:
            int: Number of remaining backup codes
        """
        try:
            hashed_codes = json.loads(hashed_codes_json)
            return len(hashed_codes)
        except:
            return 0

# Create global instance
mfa_manager = MFAManager()