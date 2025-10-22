#!/usr/bin/env python3
"""
MFA Manager - TOTP and Backup Codes
Ultra-secure multi-factor authentication with encryption
"""

import pyotp
import qrcode
import secrets
import string
import hashlib
import logging
import os
from io import BytesIO
from cryptography.fernet import Fernet
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class MFAManager:
    """Manage TOTP and backup codes with encryption"""
    
    def __init__(self):
        self.encryption_key_path = '/workspace/Application/.mfa_encryption_key'
        self.fernet = self._get_or_create_encryption_key()
    
    def _get_or_create_encryption_key(self):
        """Get or create Fernet encryption key"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.encryption_key_path), exist_ok=True)
            
            if os.path.exists(self.encryption_key_path):
                # Load existing key
                with open(self.encryption_key_path, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.encryption_key_path, 'wb') as f:
                    f.write(key)
                # Set secure permissions (owner only)
                os.chmod(self.encryption_key_path, 0o600)
                logger.info("🔑 Created new MFA encryption key")
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error with encryption key: {e}")
            # Fallback - generate temporary key (not persistent)
            return Fernet(Fernet.generate_key())
    
    def generate_totp_secret(self):
        """Generate new TOTP secret"""
        return pyotp.random_base32()
    
    def encrypt_secret(self, secret):
        """Encrypt TOTP secret for storage"""
        try:
            encrypted = self.fernet.encrypt(secret.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting secret: {e}")
            return None
    
    def decrypt_secret(self, encrypted_secret):
        """Decrypt TOTP secret from storage"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_secret.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting secret: {e}")
            return None
    
    def generate_qr_code(self, email, secret, issuer="Oranolio Security"):
        """
        Generate QR code for TOTP setup
        
        Args:
            email (str): User email
            secret (str): TOTP secret
            issuer (str): Service name
        
        Returns:
            str: Base64 encoded QR code image
        """
        try:
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=email,
                issuer_name=issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def verify_totp(self, secret, token, window=1):
        """
        Verify TOTP token
        
        Args:
            secret (str): TOTP secret
            token (str): 6-digit TOTP token
            window (int): Time window tolerance
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False
    
    def generate_backup_codes(self, count=10):
        """
        Generate backup recovery codes
        
        Args:
            count (int): Number of codes to generate
        
        Returns:
            list: List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) 
                          for _ in range(8))
            codes.append(code)
        
        return codes
    
    def hash_backup_code(self, code):
        """Hash backup code for storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def verify_backup_code(self, code, code_hash):
        """Verify backup code against hash"""
        return hashlib.sha256(code.encode()).hexdigest() == code_hash
    
    def get_current_totp(self, secret):
        """Get current TOTP code (for testing)"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.now()
        except Exception as e:
            logger.error(f"Error getting current TOTP: {e}")
            return None
    
    def get_totp_remaining_time(self, secret):
        """Get seconds remaining for current TOTP"""
        try:
            totp = pyotp.TOTP(secret)
            return 30 - (int(datetime.now().timestamp()) % 30)
        except Exception as e:
            logger.error(f"Error getting TOTP remaining time: {e}")
            return 0
    
    def validate_totp_format(self, token):
        """Validate TOTP token format"""
        if not token:
            return False
        
        # Remove spaces and convert to string
        token = str(token).replace(' ', '')
        
        # Must be 6 digits
        if len(token) != 6:
            return False
        
        # Must be numeric
        if not token.isdigit():
            return False
        
        return True
    
    def format_backup_codes_for_display(self, codes):
        """Format backup codes for user display"""
        formatted = []
        for i, code in enumerate(codes, 1):
            # Insert dash in middle for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            formatted.append(f"{i:2d}. {formatted_code}")
        
        return formatted
    
    def create_backup_codes_text(self, codes):
        """Create downloadable text file content for backup codes"""
        content = """ORANOLIO SECURITY - BACKUP CODES
═══════════════════════════════════════

⚠️  IMPORTANT: Save these codes securely!

These backup codes can be used to access your account if you lose
your authenticator device. Each code can only be used once.

BACKUP CODES:
"""
        
        for i, code in enumerate(codes, 1):
            formatted_code = f"{code[:4]}-{code[4:]}"
            content += f"{i:2d}. {formatted_code}\n"
        
        content += f"""
SECURITY NOTES:
• Each code can only be used once
• Store these codes in a secure location
• Do not share these codes with anyone
• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

If you suspect these codes have been compromised, 
regenerate them immediately in your account settings.

--
Oranolio Security Team
"""
        
        return content

# Global instance
mfa_manager = MFAManager()