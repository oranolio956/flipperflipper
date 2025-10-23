#!/usr/bin/env python3
"""
Access Key Authentication Manager
Production-ready implementation with security, performance, and error handling
"""

import os
import sys
import sqlite3
import hashlib
import secrets
import hmac
import json
import time
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config


class AuthErrorCode(Enum):
    """Authentication error codes"""
    INVALID_FORMAT = "INVALID_FORMAT"
    KEY_NOT_FOUND = "KEY_NOT_FOUND"
    KEY_REVOKED = "KEY_REVOKED"
    KEY_EXPIRED = "KEY_EXPIRED"
    USAGE_LIMIT = "USAGE_LIMIT"
    IP_DENIED = "IP_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"


@dataclass
class AuthResult:
    """Authentication result"""
    success: bool
    error_code: Optional[AuthErrorCode] = None
    error_message: Optional[str] = None
    key_id: Optional[str] = None
    permissions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AccessKey:
    """Access key data model"""
    id: str
    key_hash: str
    name: str
    created_by: str
    created_at: int
    last_used_at: Optional[int]
    expires_at: Optional[int]
    is_active: bool
    usage_count: int
    max_uses: Optional[int]
    ip_whitelist: Optional[List[str]]
    permissions: List[str]
    metadata: Optional[Dict[str, Any]]


class AccessKeyManager:
    """
    Manages access key authentication with enterprise-grade security
    """
    
    KEY_PREFIX = "orat_"
    KEY_LENGTH = 32
    HASH_ALGORITHM = "sha256"
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize access key manager"""
        self.db_path = db_path or str(Config.APPLICATION_DIR / 'access_keys.db')
        self._ensure_database()
        self._rate_limit_cache = {}  # In-memory rate limiting (use Redis in production)
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Access keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_keys (
                id TEXT PRIMARY KEY,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                last_used_at INTEGER,
                expires_at INTEGER,
                is_active INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                max_uses INTEGER,
                ip_whitelist TEXT,
                permissions TEXT DEFAULT 'read,write',
                metadata TEXT
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_key_hash 
            ON access_keys(key_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_active_keys 
            ON access_keys(is_active, expires_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_by 
            ON access_keys(created_by)
        """)
        
        # Access links table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_links (
                id TEXT PRIMARY KEY,
                access_key_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                created_by TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                last_used_at INTEGER,
                last_used_ip TEXT,
                FOREIGN KEY (access_key_id) REFERENCES access_keys(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_token_hash 
            ON access_links(token_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_link_active 
            ON access_links(is_active, expires_at)
        """)
        
        # Auth attempts table for security monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                key_prefix TEXT,
                success INTEGER NOT NULL,
                failure_reason TEXT,
                user_agent TEXT,
                timestamp INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auth_ip_time 
            ON auth_attempts(ip_address, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auth_success 
            ON auth_attempts(success, timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def generate_access_key(
        self,
        name: str,
        created_by: str,
        expires_in_days: Optional[int] = None,
        max_uses: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Generate a new access key
        
        Returns:
            Tuple of (key_id, plaintext_key)
        """
        # Generate secure random key
        random_bytes = secrets.token_urlsafe(self.KEY_LENGTH)
        plaintext_key = f"{self.KEY_PREFIX}{random_bytes}"
        
        # Hash for storage
        key_hash = self._hash_key(plaintext_key)
        
        # Generate unique ID
        key_id = secrets.token_urlsafe(16)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = int(time.time()) + (expires_in_days * 86400)
        
        # Prepare data
        permissions_str = ','.join(permissions or ['read', 'write'])
        ip_whitelist_json = json.dumps(ip_whitelist) if ip_whitelist else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO access_keys (
                    id, key_hash, name, created_by, created_at,
                    expires_at, max_uses, ip_whitelist, permissions, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key_id, key_hash, name, created_by, int(time.time()),
                expires_at, max_uses, ip_whitelist_json, permissions_str, metadata_json
            ))
            
            conn.commit()
            return key_id, plaintext_key
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"Failed to create access key: {e}")
        finally:
            conn.close()
    
    def authenticate(
        self,
        key: str,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> AuthResult:
        """
        Authenticate with access key
        
        Returns:
            AuthResult with success status and details
        """
        # Step 1: Input validation
        if not key or len(key) < 10:
            self._log_auth_attempt(ip_address, None, False, "Invalid key format", user_agent)
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.INVALID_FORMAT,
                error_message="Invalid access key format"
            )
        
        # Step 2: Rate limiting check
        if self._is_rate_limited(ip_address):
            remaining = self._get_rate_limit_reset_time(ip_address)
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.RATE_LIMITED,
                error_message=f"Too many attempts. Try again in {remaining} seconds"
            )
        
        # Step 3: Normalize key
        key = key.strip().replace(" ", "")
        
        if not key.startswith(self.KEY_PREFIX):
            self._log_auth_attempt(ip_address, key[:10], False, "Invalid prefix", user_agent)
            self._increment_rate_limit(ip_address)
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.INVALID_FORMAT,
                error_message=f"Invalid access key format. Keys must start with '{self.KEY_PREFIX}'"
            )
        
        # Step 4: Hash and lookup
        key_hash = self._hash_key(key)
        key_record = self._get_key_by_hash(key_hash)
        
        if not key_record:
            self._log_auth_attempt(ip_address, key[:10], False, "Key not found", user_agent)
            self._increment_rate_limit(ip_address)
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.KEY_NOT_FOUND,
                error_message="Invalid access key"
            )
        
        # Step 5: Validate key status
        validation_result = self._validate_key(key_record, ip_address)
        if not validation_result.success:
            self._log_auth_attempt(
                ip_address, key[:10], False, 
                validation_result.error_message, user_agent
            )
            return validation_result
        
        # Step 6: Success - update key usage
        self._update_key_usage(key_record['id'])
        
        # Step 7: Log success
        self._log_auth_attempt(ip_address, key[:10], True, None, user_agent)
        
        # Step 8: Return success result
        permissions = key_record['permissions'].split(',') if key_record['permissions'] else []
        metadata = json.loads(key_record['metadata']) if key_record['metadata'] else None
        
        return AuthResult(
            success=True,
            key_id=key_record['id'],
            permissions=permissions,
            metadata=metadata
        )
    
    def _validate_key(self, key_record: sqlite3.Row, ip_address: str) -> AuthResult:
        """Validate key constraints"""
        # Check if active
        if not key_record['is_active']:
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.KEY_REVOKED,
                error_message="This access key has been revoked"
            )
        
        # Check expiration
        if key_record['expires_at'] and key_record['expires_at'] < time.time():
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.KEY_EXPIRED,
                error_message="This access key has expired"
            )
        
        # Check usage limit
        if key_record['max_uses'] and key_record['usage_count'] >= key_record['max_uses']:
            return AuthResult(
                success=False,
                error_code=AuthErrorCode.USAGE_LIMIT,
                error_message="Usage limit reached for this key"
            )
        
        # Check IP whitelist
        if key_record['ip_whitelist']:
            whitelist = json.loads(key_record['ip_whitelist'])
            if not self._ip_in_whitelist(ip_address, whitelist):
                return AuthResult(
                    success=False,
                    error_code=AuthErrorCode.IP_DENIED,
                    error_message="Access denied from this IP address"
                )
        
        return AuthResult(success=True)
    
    def _hash_key(self, key: str) -> str:
        """Hash key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _get_key_by_hash(self, key_hash: str) -> Optional[sqlite3.Row]:
        """Lookup key by hash"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM access_keys WHERE key_hash = ?
        """, (key_hash,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def _update_key_usage(self, key_id: str):
        """Update key usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE access_keys 
            SET usage_count = usage_count + 1, last_used_at = ?
            WHERE id = ?
        """, (int(time.time()), key_id))
        
        conn.commit()
        conn.close()
    
    def _ip_in_whitelist(self, ip: str, whitelist: List[str]) -> bool:
        """Check if IP is in whitelist (supports CIDR notation)"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for allowed in whitelist:
                if '/' in allowed:
                    # CIDR notation
                    if ip_obj in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:
                    # Single IP
                    if ip_obj == ipaddress.ip_address(allowed):
                        return True
            return False
        except ValueError:
            return False
    
    def _is_rate_limited(self, ip: str) -> bool:
        """Check if IP is rate limited"""
        key = f"rate_limit:{ip}"
        if key in self._rate_limit_cache:
            attempts, reset_time = self._rate_limit_cache[key]
            if time.time() < reset_time:
                return attempts >= 5
            else:
                # Reset expired
                del self._rate_limit_cache[key]
        return False
    
    def _increment_rate_limit(self, ip: str):
        """Increment rate limit counter"""
        key = f"rate_limit:{ip}"
        if key in self._rate_limit_cache:
            attempts, reset_time = self._rate_limit_cache[key]
            self._rate_limit_cache[key] = (attempts + 1, reset_time)
        else:
            reset_time = time.time() + 900  # 15 minutes
            self._rate_limit_cache[key] = (1, reset_time)
    
    def _get_rate_limit_reset_time(self, ip: str) -> int:
        """Get seconds until rate limit resets"""
        key = f"rate_limit:{ip}"
        if key in self._rate_limit_cache:
            _, reset_time = self._rate_limit_cache[key]
            return max(0, int(reset_time - time.time()))
        return 0
    
    def _log_auth_attempt(
        self,
        ip_address: str,
        key_prefix: Optional[str],
        success: bool,
        failure_reason: Optional[str],
        user_agent: Optional[str]
    ):
        """Log authentication attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO auth_attempts (
                ip_address, key_prefix, success, failure_reason, user_agent, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (ip_address, key_prefix, int(success), failure_reason, user_agent, int(time.time())))
        
        conn.commit()
        conn.close()
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an access key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE access_keys SET is_active = 0 WHERE id = ?
        """, (key_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def list_keys(
        self,
        created_by: Optional[str] = None,
        active_only: bool = False
    ) -> List[AccessKey]:
        """List access keys"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM access_keys WHERE 1=1"
        params = []
        
        if created_by:
            query += " AND created_by = ?"
            params.append(created_by)
        
        if active_only:
            query += " AND is_active = 1"
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        keys = []
        for row in rows:
            keys.append(AccessKey(
                id=row['id'],
                key_hash=row['key_hash'],
                name=row['name'],
                created_by=row['created_by'],
                created_at=row['created_at'],
                last_used_at=row['last_used_at'],
                expires_at=row['expires_at'],
                is_active=bool(row['is_active']),
                usage_count=row['usage_count'],
                max_uses=row['max_uses'],
                ip_whitelist=json.loads(row['ip_whitelist']) if row['ip_whitelist'] else None,
                permissions=row['permissions'].split(',') if row['permissions'] else [],
                metadata=json.loads(row['metadata']) if row['metadata'] else None
            ))
        
        return keys


# Global instance
access_key_manager = AccessKeyManager()


if __name__ == "__main__":
    # Test the manager
    print("Access Key Manager - Test")
    print("=" * 60)
    
    # Generate a test key
    key_id, plaintext_key = access_key_manager.generate_access_key(
        name="Test Key",
        created_by="admin",
        expires_in_days=365
    )
    
    print(f"✓ Generated key: {plaintext_key}")
    print(f"  Key ID: {key_id}")
    
    # Test authentication
    result = access_key_manager.authenticate(plaintext_key, "127.0.0.1")
    
    if result.success:
        print(f"✓ Authentication successful")
        print(f"  Permissions: {result.permissions}")
    else:
        print(f"✗ Authentication failed: {result.error_message}")
