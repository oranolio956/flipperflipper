"""
Security Manager - Encrypt session files and secure sensitive data
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend


class SecurityManager:
    """Manages encryption of sensitive data"""
    
    def __init__(self, password: str = None):
        """
        Initialize security manager
        
        Args:
            password: Master password for encryption
                     If None, will prompt user or generate
        """
        self.password = password or self._get_or_create_password()
        self.key = self._derive_key(self.password)
        self.cipher = Fernet(self.key)
    
    def _get_or_create_password(self) -> str:
        """Get password from environment or create new one"""
        # Try environment variable first
        password = os.getenv('TELEGRAN_MASTER_PASSWORD')
        
        if password:
            return password
        
        # Check if password file exists
        password_file = Path('.telegran_key')
        if password_file.exists():
            with open(password_file, 'r') as f:
                return f.read().strip()
        
        # Generate new password
        import secrets
        password = secrets.token_urlsafe(32)
        
        # Save it
        with open(password_file, 'w') as f:
            f.write(password)
        
        # Set restrictive permissions
        os.chmod(password_file, 0o600)
        
        print(f"🔐 Generated master password and saved to {password_file}")
        print(f"⚠️  Keep this file safe! Without it, you can't decrypt your data.")
        
        return password
    
    def _derive_key(self, password: str, salt: bytes = None) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            # Use consistent salt (in production, store this securely)
            salt = b'telegran_salt_v1'  # Should be random and stored
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_file(self, file_path: str) -> str:
        """
        Encrypt a file
        
        Args:
            file_path: Path to file to encrypt
            
        Returns:
            Path to encrypted file
        """
        # Read file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Encrypt
        encrypted = self.cipher.encrypt(data)
        
        # Write encrypted file
        encrypted_path = f"{file_path}.encrypted"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted)
        
        # Set restrictive permissions
        os.chmod(encrypted_path, 0o600)
        
        return encrypted_path
    
    def decrypt_file(self, encrypted_path: str) -> bytes:
        """
        Decrypt a file
        
        Args:
            encrypted_path: Path to encrypted file
            
        Returns:
            Decrypted data
        """
        with open(encrypted_path, 'rb') as f:
            encrypted = f.read()
        
        return self.cipher.decrypt(encrypted)
    
    def encrypt_data(self, data: dict) -> str:
        """
        Encrypt dictionary data
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        json_data = json.dumps(data).encode()
        encrypted = self.cipher.encrypt(json_data)
        return base64.b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_str: str) -> dict:
        """
        Decrypt dictionary data
        
        Args:
            encrypted_str: Base64-encoded encrypted data
            
        Returns:
            Decrypted dictionary
        """
        encrypted = base64.b64decode(encrypted_str.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
    
    def secure_session_file(self, session_file: str):
        """
        Encrypt Telegram session file
        
        Args:
            session_file: Path to session file
        """
        if not os.path.exists(session_file):
            print(f"⚠️  Session file {session_file} doesn't exist yet")
            return
        
        # Backup original
        backup_path = f"{session_file}.backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(session_file, backup_path)
            print(f"💾 Backed up session to {backup_path}")
        
        # Encrypt
        encrypted_path = self.encrypt_file(session_file)
        print(f"🔒 Encrypted session file: {encrypted_path}")
        
        # Remove original (optional)
        print(f"⚠️  Original session file still exists: {session_file}")
        print(f"   Consider deleting it after verifying encrypted version works")
    
    def hash_data(self, data: str) -> str:
        """Create SHA-256 hash of data"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """Verify data matches hash"""
        return self.hash_data(data) == hash_value


def secure_config_example():
    """Example of how to use security manager"""
    
    # Initialize
    security = SecurityManager()
    
    # Encrypt sensitive config
    config = {
        'api_id': '12345678',
        'api_hash': 'abcdef123456',
        'phone': '+1234567890'
    }
    
    encrypted = security.encrypt_data(config)
    print(f"Encrypted config: {encrypted[:50]}...")
    
    # Decrypt
    decrypted = security.decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")
    
    # Encrypt session file
    security.secure_session_file('userbot_session.session')


if __name__ == '__main__':
    secure_config_example()
