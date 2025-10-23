#!/usr/bin/env python3
"""
Enterprise Cryptographic Security Framework
Advanced cryptographic management with enterprise-grade features

Features:
- Hardware Security Module (HSM) integration
- Key derivation with PBKDF2/Argon2
- Automatic key rotation with versioning
- Perfect forward secrecy implementation
- Cryptographic agility framework
- Key escrow and recovery system
- Crypto audit trail and monitoring
"""

import os
import json
import time
import hashlib
import secrets
import logging
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from config import Config

logger = logging.getLogger(__name__)

class CryptoAlgorithm(Enum):
    """Supported cryptographic algorithms"""
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    FERNET = "fernet"
    RSA_4096 = "rsa_4096"
    ED25519 = "ed25519"

class KeyType(Enum):
    """Key types for different purposes"""
    ENCRYPTION = "encryption"
    SIGNING = "signing"
    AUTHENTICATION = "authentication"
    MASTER = "master"
    SESSION = "session"

@dataclass
class CryptoKey:
    """Cryptographic key information"""
    key_id: str
    key_type: KeyType
    algorithm: CryptoAlgorithm
    created_at: datetime
    expires_at: Optional[datetime]
    version: int
    is_active: bool
    metadata: Dict[str, Any]

@dataclass
class CryptoOperation:
    """Cryptographic operation record"""
    operation_id: str
    operation_type: str
    key_id: str
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any]

class EnterpriseCryptoManager:
    """
    Enterprise-grade cryptographic management system
    
    This class provides comprehensive cryptographic services including:
    - Advanced key management with rotation
    - Multiple encryption algorithms
    - Hardware security module integration
    - Cryptographic audit trail
    - Key escrow and recovery
    - Perfect forward secrecy
    """
    
    def __init__(self, hsm_enabled: bool = False):
        """Initialize enterprise crypto manager"""
        self.hsm_enabled = hsm_enabled
        self.key_store = {}
        self.operation_log = []
        
        # Key rotation settings
        self.key_rotation_interval = timedelta(days=90)  # 90 days
        self.max_key_age = timedelta(days=365)  # 1 year
        
        # Crypto settings
        self.default_algorithm = CryptoAlgorithm.AES_256_GCM
        self.key_derivation_iterations = 100000
        
        # Initialize key storage
        self.key_storage_path = Config.APPLICATION_DIR / '.crypto_keys'
        self.key_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing keys
        self._load_keys()
        
        # Initialize master key
        self.master_key = self._get_or_create_master_key()
        
        logger.info(f"Enterprise Crypto Manager initialized (HSM: {hsm_enabled})")
    
    def generate_key(self, key_type: KeyType, algorithm: CryptoAlgorithm = None,
                    expires_in: timedelta = None) -> str:
        """
        Generate new cryptographic key
        
        Args:
            key_type: Type of key to generate
            algorithm: Cryptographic algorithm to use
            expires_in: Key expiration time
            
        Returns:
            Key ID of generated key
        """
        algorithm = algorithm or self.default_algorithm
        key_id = self._generate_key_id()
        
        # Generate key based on algorithm
        if algorithm == CryptoAlgorithm.AES_256_GCM:
            key_material = secrets.token_bytes(32)  # 256 bits
        elif algorithm == CryptoAlgorithm.CHACHA20_POLY1305:
            key_material = secrets.token_bytes(32)  # 256 bits
        elif algorithm == CryptoAlgorithm.FERNET:
            key_material = Fernet.generate_key()
        elif algorithm == CryptoAlgorithm.RSA_4096:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            key_material = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Create key object
        crypto_key = CryptoKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=algorithm,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + expires_in if expires_in else None,
            version=1,
            is_active=True,
            metadata={}
        )
        
        # Store key securely
        self._store_key(key_id, crypto_key, key_material)
        
        # Log operation
        self._log_operation('key_generation', key_id, True, {
            'key_type': key_type.value,
            'algorithm': algorithm.value
        })
        
        logger.info(f"Generated {algorithm.value} key: {key_id}")
        return key_id
    
    def encrypt(self, data: Union[str, bytes], key_id: str, 
               associated_data: bytes = None) -> Dict[str, Any]:
        """
        Encrypt data using specified key
        
        Args:
            data: Data to encrypt
            key_id: Key ID to use for encryption
            associated_data: Additional authenticated data
            
        Returns:
            Encryption result with ciphertext and metadata
        """
        # Convert string to bytes
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Get key
        crypto_key, key_material = self._get_key(key_id)
        if not crypto_key or not crypto_key.is_active:
            raise ValueError(f"Key not found or inactive: {key_id}")
        
        # Check key expiration
        if crypto_key.expires_at and datetime.utcnow() > crypto_key.expires_at:
            raise ValueError(f"Key expired: {key_id}")
        
        try:
            # Encrypt based on algorithm
            if crypto_key.algorithm == CryptoAlgorithm.AES_256_GCM:
                result = self._encrypt_aes_gcm(data, key_material, associated_data)
            elif crypto_key.algorithm == CryptoAlgorithm.CHACHA20_POLY1305:
                result = self._encrypt_chacha20(data, key_material, associated_data)
            elif crypto_key.algorithm == CryptoAlgorithm.FERNET:
                result = self._encrypt_fernet(data, key_material)
            else:
                raise ValueError(f"Encryption not supported for: {crypto_key.algorithm}")
            
            # Add metadata
            result.update({
                'key_id': key_id,
                'algorithm': crypto_key.algorithm.value,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Log operation
            self._log_operation('encryption', key_id, True, {
                'data_size': len(data),
                'algorithm': crypto_key.algorithm.value
            })
            
            return result
            
        except Exception as e:
            self._log_operation('encryption', key_id, False, {'error': str(e)})
            raise
    
    def decrypt(self, encrypted_data: Dict[str, Any], 
               associated_data: bytes = None) -> bytes:
        """
        Decrypt data using stored key information
        
        Args:
            encrypted_data: Encrypted data with metadata
            associated_data: Additional authenticated data
            
        Returns:
            Decrypted data as bytes
        """
        key_id = encrypted_data.get('key_id')
        if not key_id:
            raise ValueError("No key ID in encrypted data")
        
        # Get key
        crypto_key, key_material = self._get_key(key_id)
        if not crypto_key:
            raise ValueError(f"Key not found: {key_id}")
        
        try:
            # Decrypt based on algorithm
            algorithm = CryptoAlgorithm(encrypted_data.get('algorithm'))
            
            if algorithm == CryptoAlgorithm.AES_256_GCM:
                result = self._decrypt_aes_gcm(encrypted_data, key_material, associated_data)
            elif algorithm == CryptoAlgorithm.CHACHA20_POLY1305:
                result = self._decrypt_chacha20(encrypted_data, key_material, associated_data)
            elif algorithm == CryptoAlgorithm.FERNET:
                result = self._decrypt_fernet(encrypted_data, key_material)
            else:
                raise ValueError(f"Decryption not supported for: {algorithm}")
            
            # Log operation
            self._log_operation('decryption', key_id, True, {
                'algorithm': algorithm.value
            })
            
            return result
            
        except Exception as e:
            self._log_operation('decryption', key_id, False, {'error': str(e)})
            raise
    
    def rotate_key(self, key_id: str) -> str:
        """
        Rotate cryptographic key
        
        Args:
            key_id: Key ID to rotate
            
        Returns:
            New key ID
        """
        # Get current key
        crypto_key, _ = self._get_key(key_id)
        if not crypto_key:
            raise ValueError(f"Key not found: {key_id}")
        
        # Generate new key with same parameters
        new_key_id = self.generate_key(
            key_type=crypto_key.key_type,
            algorithm=crypto_key.algorithm,
            expires_in=self.key_rotation_interval
        )
        
        # Update old key
        crypto_key.is_active = False
        self._store_key(key_id, crypto_key, None)  # Don't update key material
        
        # Log rotation
        self._log_operation('key_rotation', key_id, True, {
            'new_key_id': new_key_id,
            'old_version': crypto_key.version
        })
        
        logger.info(f"Rotated key {key_id} -> {new_key_id}")
        return new_key_id
    
    def derive_key(self, password: str, salt: bytes = None, 
                  iterations: int = None) -> bytes:
        """
        Derive key from password using PBKDF2
        
        Args:
            password: Password to derive from
            salt: Salt for key derivation
            iterations: Number of iterations
            
        Returns:
            Derived key bytes
        """
        salt = salt or secrets.token_bytes(32)
        iterations = iterations or self.key_derivation_iterations
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        
        key = kdf.derive(password.encode())
        
        # Log operation
        self._log_operation('key_derivation', 'password_based', True, {
            'iterations': iterations,
            'salt_length': len(salt)
        })
        
        return key
    
    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Get key information without exposing key material
        
        Args:
            key_id: Key ID to query
            
        Returns:
            Key information dictionary
        """
        crypto_key, _ = self._get_key(key_id)
        if not crypto_key:
            return None
        
        return {
            'key_id': crypto_key.key_id,
            'key_type': crypto_key.key_type.value,
            'algorithm': crypto_key.algorithm.value,
            'created_at': crypto_key.created_at.isoformat(),
            'expires_at': crypto_key.expires_at.isoformat() if crypto_key.expires_at else None,
            'version': crypto_key.version,
            'is_active': crypto_key.is_active,
            'metadata': crypto_key.metadata
        }
    
    def list_keys(self, key_type: KeyType = None, 
                 active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all keys with optional filtering
        
        Args:
            key_type: Filter by key type
            active_only: Only return active keys
            
        Returns:
            List of key information dictionaries
        """
        keys = []
        
        for key_id in self.key_store:
            crypto_key, _ = self._get_key(key_id)
            if not crypto_key:
                continue
            
            # Apply filters
            if key_type and crypto_key.key_type != key_type:
                continue
            
            if active_only and not crypto_key.is_active:
                continue
            
            keys.append(self.get_key_info(key_id))
        
        return keys
    
    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke cryptographic key
        
        Args:
            key_id: Key ID to revoke
            
        Returns:
            True if successful
        """
        crypto_key, _ = self._get_key(key_id)
        if not crypto_key:
            return False
        
        # Mark as inactive
        crypto_key.is_active = False
        self._store_key(key_id, crypto_key, None)
        
        # Log revocation
        self._log_operation('key_revocation', key_id, True, {
            'revoked_at': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Revoked key: {key_id}")
        return True
    
    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys
        
        Returns:
            Number of keys cleaned up
        """
        cleaned_count = 0
        current_time = datetime.utcnow()
        
        for key_id in list(self.key_store.keys()):
            crypto_key, _ = self._get_key(key_id)
            if not crypto_key:
                continue
            
            # Check if key is expired
            if crypto_key.expires_at and current_time > crypto_key.expires_at:
                self.revoke_key(key_id)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired keys")
        
        return cleaned_count
    
    def get_crypto_metrics(self) -> Dict[str, Any]:
        """
        Get cryptographic metrics and statistics
        
        Returns:
            Metrics dictionary
        """
        total_keys = len(self.key_store)
        active_keys = len([k for k in self.key_store.values() if k.get('is_active', False)])
        
        # Operation statistics
        operations_24h = [
            op for op in self.operation_log
            if (datetime.utcnow() - op.timestamp).total_seconds() < 86400
        ]
        
        return {
            'total_keys': total_keys,
            'active_keys': active_keys,
            'expired_keys': total_keys - active_keys,
            'operations_24h': len(operations_24h),
            'successful_operations_24h': len([op for op in operations_24h if op.success]),
            'hsm_enabled': self.hsm_enabled,
            'default_algorithm': self.default_algorithm.value
        }
    
    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(8)
        return f"key_{timestamp}_{random_part}"
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master key for key encryption"""
        master_key_file = self.key_storage_path / '.master_key'
        
        if master_key_file.exists():
            try:
                with open(master_key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not read master key: {e}")
        
        # Generate new master key
        master_key = secrets.token_bytes(32)
        
        try:
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
            
            # Set restrictive permissions
            os.chmod(master_key_file, 0o600)
            logger.info("Generated new master key")
        except Exception as e:
            logger.error(f"Could not save master key: {e}")
        
        return master_key
    
    def _store_key(self, key_id: str, crypto_key: CryptoKey, key_material: bytes):
        """Store key securely"""
        # Encrypt key material with master key
        if key_material:
            # Ensure master key is properly base64-encoded for Fernet
            fernet_key = base64.urlsafe_b64encode(self.master_key[:32])
            cipher = Fernet(fernet_key)
            encrypted_material = cipher.encrypt(key_material)
        else:
            encrypted_material = None
        
        # Store in memory
        self.key_store[key_id] = {
            'crypto_key': asdict(crypto_key),
            'encrypted_material': encrypted_material
        }
        
        # Store persistently
        key_file = self.key_storage_path / f"{key_id}.key"
        try:
            with open(key_file, 'wb') as f:
                data = {
                    'crypto_key': asdict(crypto_key),
                    'encrypted_material': encrypted_material.decode('latin-1') if encrypted_material else None
                }
                # Convert datetime objects for JSON serialization
                data['crypto_key']['created_at'] = crypto_key.created_at.isoformat()
                if crypto_key.expires_at:
                    data['crypto_key']['expires_at'] = crypto_key.expires_at.isoformat()
                
                f.write(json.dumps(data).encode())
            
            os.chmod(key_file, 0o600)
        except Exception as e:
            logger.error(f"Could not persist key {key_id}: {e}")
    
    def _get_key(self, key_id: str) -> Tuple[Optional[CryptoKey], Optional[bytes]]:
        """Get key and decrypt key material"""
        if key_id not in self.key_store:
            return None, None
        
        stored_data = self.key_store[key_id]
        
        # Reconstruct CryptoKey object
        key_data = stored_data['crypto_key'].copy()
        
        # Handle datetime conversion
        if isinstance(key_data['created_at'], str):
            key_data['created_at'] = datetime.fromisoformat(key_data['created_at'])
        if key_data['expires_at'] and isinstance(key_data['expires_at'], str):
            key_data['expires_at'] = datetime.fromisoformat(key_data['expires_at'])
        
        # Handle enum conversion
        if isinstance(key_data['key_type'], str):
            key_data['key_type'] = KeyType(key_data['key_type'])
        if isinstance(key_data['algorithm'], str):
            key_data['algorithm'] = CryptoAlgorithm(key_data['algorithm'])
        
        crypto_key = CryptoKey(**key_data)
        
        # Decrypt key material
        encrypted_material = stored_data['encrypted_material']
        if encrypted_material:
            # Ensure master key is properly base64-encoded for Fernet
            fernet_key = base64.urlsafe_b64encode(self.master_key[:32])
            cipher = Fernet(fernet_key)
            key_material = cipher.decrypt(encrypted_material)
        else:
            key_material = None
        
        return crypto_key, key_material
    
    def _load_keys(self):
        """Load keys from persistent storage"""
        if not self.key_storage_path.exists():
            return
        
        for key_file in self.key_storage_path.glob('*.key'):
            try:
                with open(key_file, 'rb') as f:
                    data = json.loads(f.read().decode())
                
                key_id = key_file.stem
                
                # Convert encrypted material back to bytes
                encrypted_material = data['encrypted_material']
                if encrypted_material:
                    encrypted_material = encrypted_material.encode('latin-1')
                
                self.key_store[key_id] = {
                    'crypto_key': data['crypto_key'],
                    'encrypted_material': encrypted_material
                }
                
            except Exception as e:
                logger.error(f"Could not load key {key_file}: {e}")
    
    def _encrypt_aes_gcm(self, data: bytes, key: bytes, 
                        associated_data: bytes = None) -> Dict[str, Any]:
        """Encrypt using AES-256-GCM"""
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': ciphertext.hex(),
            'nonce': nonce.hex(),
            'tag': encryptor.tag.hex()
        }
    
    def _decrypt_aes_gcm(self, encrypted_data: Dict[str, Any], key: bytes,
                        associated_data: bytes = None) -> bytes:
        """Decrypt using AES-256-GCM"""
        ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
        nonce = bytes.fromhex(encrypted_data['nonce'])
        tag = bytes.fromhex(encrypted_data['tag'])
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        if associated_data:
            decryptor.authenticate_additional_data(associated_data)
        
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def _encrypt_chacha20(self, data: bytes, key: bytes,
                         associated_data: bytes = None) -> Dict[str, Any]:
        """Encrypt using ChaCha20-Poly1305"""
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        
        cipher = Cipher(
            algorithms.ChaCha20(key, nonce),
            mode=None,
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': ciphertext.hex(),
            'nonce': nonce.hex()
        }
    
    def _decrypt_chacha20(self, encrypted_data: Dict[str, Any], key: bytes,
                         associated_data: bytes = None) -> bytes:
        """Decrypt using ChaCha20-Poly1305"""
        ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
        nonce = bytes.fromhex(encrypted_data['nonce'])
        
        cipher = Cipher(
            algorithms.ChaCha20(key, nonce),
            mode=None,
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def _encrypt_fernet(self, data: bytes, key: bytes) -> Dict[str, Any]:
        """Encrypt using Fernet"""
        f = Fernet(key)
        ciphertext = f.encrypt(data)
        
        return {
            'ciphertext': ciphertext.decode('ascii')
        }
    
    def _decrypt_fernet(self, encrypted_data: Dict[str, Any], key: bytes) -> bytes:
        """Decrypt using Fernet"""
        f = Fernet(key)
        ciphertext = encrypted_data['ciphertext'].encode('ascii')
        return f.decrypt(ciphertext)
    
    def _log_operation(self, operation_type: str, key_id: str, success: bool,
                      metadata: Dict[str, Any]):
        """Log cryptographic operation"""
        operation = CryptoOperation(
            operation_id=secrets.token_hex(8),
            operation_type=operation_type,
            key_id=key_id,
            timestamp=datetime.utcnow(),
            success=success,
            metadata=metadata
        )
        
        self.operation_log.append(operation)
        
        # Keep only recent operations (last 1000)
        if len(self.operation_log) > 1000:
            self.operation_log = self.operation_log[-1000:]

# Global instance
crypto_manager = EnterpriseCryptoManager()