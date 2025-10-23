#!/usr/bin/env python3
"""
Enterprise Session Management Framework
Advanced session security with enterprise-grade features

Features:
- Session regeneration with cryptographic security
- Multi-device session management
- Session encryption and integrity protection
- Advanced session timeout with sliding windows
- Session fingerprinting and anomaly detection
- Secure session storage with Redis clustering
- Session audit trail and monitoring
"""

import os
import json
import time
import hashlib
import secrets
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis
import logging
from flask import request, session as flask_session
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Session information structure"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    device_fingerprint: str
    is_active: bool
    security_level: str
    permissions: List[str]
    metadata: Dict[str, Any]

@dataclass
class SessionSecurity:
    """Session security metrics"""
    risk_score: float
    anomaly_flags: List[str]
    geo_location: Optional[str]
    device_trust_level: str
    authentication_strength: str

class EnterpriseSessionManager:
    """
    Enterprise-grade session management with advanced security features
    
    This class provides comprehensive session management including:
    - Cryptographically secure session generation
    - Session fixation prevention
    - Multi-device session tracking
    - Anomaly detection and response
    - Audit trail and compliance logging
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize enterprise session manager"""
        self.redis_client = redis_client or self._create_redis_client()
        self.session_key = self._derive_session_key()
        self.cipher = Fernet(self.session_key)
        
        # Session configuration
        self.session_timeout = Config.SESSION_TIMEOUT_MINUTES * 60
        self.max_sessions_per_user = 5
        self.session_regeneration_interval = 1800  # 30 minutes
        self.anomaly_threshold = 0.7
        
        # Security settings
        self.require_device_fingerprint = True
        self.enable_geo_tracking = True
        self.enable_anomaly_detection = True
        
        logger.info("Enterprise Session Manager initialized")
    
    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client for session storage"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()  # Test connection
            logger.info("Redis connection established")
            return client
        except Exception as e:
            logger.warning(f"Redis unavailable, using memory fallback: {e}")
            # Fallback to in-memory storage (not recommended for production)
            return self._create_memory_fallback()
    
    def _create_memory_fallback(self):
        """Create in-memory fallback for development"""
        class MemoryRedis:
            def __init__(self):
                self.data = {}
                self.expiry = {}
            
            def set(self, key, value, ex=None):
                self.data[key] = value
                if ex:
                    self.expiry[key] = time.time() + ex
            
            def get(self, key):
                if key in self.expiry and time.time() > self.expiry[key]:
                    del self.data[key]
                    del self.expiry[key]
                    return None
                return self.data.get(key)
            
            def delete(self, key):
                self.data.pop(key, None)
                self.expiry.pop(key, None)
            
            def exists(self, key):
                return key in self.data
            
            def keys(self, pattern):
                import fnmatch
                return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]
        
        return MemoryRedis()
    
    def _derive_session_key(self) -> bytes:
        """Derive session encryption key from master key"""
        master_key = Config.SECRET_KEY.encode()
        salt = b'session_encryption_salt_v1'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(master_key)
        # Fernet requires base64-encoded key
        return base64.urlsafe_b64encode(key)
    
    def create_session(self, user_id: str, security_level: str = 'standard',
                      permissions: List[str] = None) -> Tuple[str, SessionInfo]:
        """
        Create new secure session with advanced security features
        
        Args:
            user_id: User identifier
            security_level: Security level (standard, high, critical)
            permissions: List of permissions for this session
            
        Returns:
            Tuple of (session_token, session_info)
        """
        # Generate cryptographically secure session ID
        session_id = self._generate_secure_session_id()
        
        # Get request context information
        ip_address = self._get_client_ip()
        user_agent = request.headers.get('User-Agent', '') if request else ''
        device_fingerprint = self._generate_device_fingerprint(ip_address, user_agent)
        
        # Create session info
        now = datetime.utcnow()
        session_info = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            is_active=True,
            security_level=security_level,
            permissions=permissions or [],
            metadata={}
        )
        
        # Check session limits
        self._enforce_session_limits(user_id)
        
        # Store session securely
        self._store_session(session_id, session_info)
        
        # Generate session token
        session_token = self._generate_session_token(session_id)
        
        # Log session creation
        self._log_session_event('session_created', session_info)
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        return session_token, session_info
    
    def validate_session(self, session_token: str) -> Optional[SessionInfo]:
        """
        Validate session token and return session info
        
        Args:
            session_token: Session token to validate
            
        Returns:
            SessionInfo if valid, None if invalid
        """
        try:
            # Extract session ID from token
            session_id = self._extract_session_id(session_token)
            if not session_id:
                return None
            
            # Retrieve session info
            session_info = self._get_session(session_id)
            if not session_info:
                return None
            
            # Check if session is active
            if not session_info.is_active:
                return None
            
            # Check session timeout
            if self._is_session_expired(session_info):
                self._invalidate_session(session_id)
                return None
            
            # Perform security checks
            security_result = self._perform_security_checks(session_info)
            if security_result.risk_score > self.anomaly_threshold:
                self._handle_suspicious_session(session_info, security_result)
                return None
            
            # Update last activity
            session_info.last_activity = datetime.utcnow()
            self._store_session(session_id, session_info)
            
            # Check if session regeneration is needed
            if self._should_regenerate_session(session_info):
                new_token, new_info = self._regenerate_session(session_info)
                return new_info
            
            return session_info
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def regenerate_session(self, session_token: str) -> Optional[Tuple[str, SessionInfo]]:
        """
        Regenerate session to prevent session fixation
        
        Args:
            session_token: Current session token
            
        Returns:
            Tuple of (new_session_token, session_info) if successful
        """
        # Validate current session
        session_info = self.validate_session(session_token)
        if not session_info:
            return None
        
        # Regenerate session
        return self._regenerate_session(session_info)
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate session and clean up
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id = self._extract_session_id(session_token)
            if session_id:
                return self._invalidate_session(session_id)
            return False
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active sessions
        """
        try:
            pattern = f"session:*"
            session_keys = self.redis_client.keys(pattern)
            
            user_sessions = []
            for key in session_keys:
                session_data = self.redis_client.get(key)
                if session_data:
                    session_info = self._deserialize_session(session_data)
                    if session_info and session_info.user_id == user_id and session_info.is_active:
                        user_sessions.append(session_info)
            
            return user_sessions
        except Exception as e:
            logger.error(f"Error retrieving user sessions: {e}")
            return []
    
    def invalidate_user_sessions(self, user_id: str, except_session: str = None) -> int:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User identifier
            except_session: Session ID to keep active
            
        Returns:
            Number of sessions invalidated
        """
        sessions = self.get_user_sessions(user_id)
        invalidated = 0
        
        for session_info in sessions:
            if except_session and session_info.session_id == except_session:
                continue
            
            if self._invalidate_session(session_info.session_id):
                invalidated += 1
        
        logger.info(f"Invalidated {invalidated} sessions for user {user_id}")
        return invalidated
    
    def _generate_secure_session_id(self) -> str:
        """Generate cryptographically secure session ID"""
        # Use multiple sources of entropy
        entropy_sources = [
            secrets.token_bytes(32),
            str(time.time_ns()).encode(),
            os.urandom(16)
        ]
        
        # Combine entropy sources
        combined_entropy = b''.join(entropy_sources)
        
        # Generate session ID using SHA-256
        session_id = hashlib.sha256(combined_entropy).hexdigest()
        
        # Add timestamp and random suffix for uniqueness
        timestamp = str(int(time.time()))
        random_suffix = secrets.token_hex(8)
        
        return f"{session_id}_{timestamp}_{random_suffix}"
    
    def _generate_session_token(self, session_id: str) -> str:
        """Generate encrypted session token"""
        # Create token payload
        payload = {
            'session_id': session_id,
            'timestamp': int(time.time()),
            'nonce': secrets.token_hex(16)
        }
        
        # Encrypt payload
        encrypted_payload = self.cipher.encrypt(json.dumps(payload).encode())
        
        # Encode as base64 for URL safety
        import base64
        return base64.urlsafe_b64encode(encrypted_payload).decode()
    
    def _extract_session_id(self, session_token: str) -> Optional[str]:
        """Extract session ID from encrypted token"""
        try:
            import base64
            
            # Decode from base64
            encrypted_payload = base64.urlsafe_b64decode(session_token.encode())
            
            # Decrypt payload
            decrypted_payload = self.cipher.decrypt(encrypted_payload)
            payload = json.loads(decrypted_payload.decode())
            
            # Validate timestamp (token expires in 24 hours)
            token_age = time.time() - payload['timestamp']
            if token_age > 86400:  # 24 hours
                return None
            
            return payload['session_id']
            
        except Exception as e:
            logger.warning(f"Invalid session token: {e}")
            return None
    
    def _get_client_ip(self) -> str:
        """Get client IP address with proxy support"""
        if not request:
            return 'unknown'
        
        # Check for forwarded headers (reverse proxy)
        forwarded_ips = request.headers.get('X-Forwarded-For')
        if forwarded_ips:
            return forwarded_ips.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def _generate_device_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """Generate device fingerprint for tracking"""
        fingerprint_data = f"{ip_address}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def _store_session(self, session_id: str, session_info: SessionInfo):
        """Store session securely in Redis"""
        key = f"session:{session_id}"
        data = self._serialize_session(session_info)
        self.redis_client.set(key, data, ex=self.session_timeout)
    
    def _get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve session from storage"""
        key = f"session:{session_id}"
        data = self.redis_client.get(key)
        
        if data:
            return self._deserialize_session(data)
        return None
    
    def _serialize_session(self, session_info: SessionInfo) -> str:
        """Serialize session info for storage"""
        data = asdict(session_info)
        # Convert datetime objects to ISO format
        data['created_at'] = session_info.created_at.isoformat()
        data['last_activity'] = session_info.last_activity.isoformat()
        return json.dumps(data)
    
    def _deserialize_session(self, data: str) -> Optional[SessionInfo]:
        """Deserialize session info from storage"""
        try:
            session_dict = json.loads(data)
            # Convert ISO format back to datetime
            session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
            session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
            return SessionInfo(**session_dict)
        except Exception as e:
            logger.error(f"Session deserialization error: {e}")
            return None
    
    def _is_session_expired(self, session_info: SessionInfo) -> bool:
        """Check if session has expired"""
        now = datetime.utcnow()
        
        # Check absolute timeout
        if (now - session_info.created_at).total_seconds() > self.session_timeout:
            return True
        
        # Check inactivity timeout
        inactivity_timeout = 3600  # 1 hour
        if (now - session_info.last_activity).total_seconds() > inactivity_timeout:
            return True
        
        return False
    
    def _perform_security_checks(self, session_info: SessionInfo) -> SessionSecurity:
        """Perform security checks on session"""
        risk_score = 0.0
        anomaly_flags = []
        
        # Check IP address consistency
        current_ip = self._get_client_ip()
        if current_ip != session_info.ip_address:
            risk_score += 0.3
            anomaly_flags.append('ip_change')
        
        # Check user agent consistency
        current_ua = request.headers.get('User-Agent', '') if request else ''
        if current_ua != session_info.user_agent:
            risk_score += 0.2
            anomaly_flags.append('user_agent_change')
        
        # Check session age
        session_age = (datetime.utcnow() - session_info.created_at).total_seconds()
        if session_age > 86400:  # 24 hours
            risk_score += 0.1
            anomaly_flags.append('old_session')
        
        # Check activity patterns
        if self._detect_unusual_activity(session_info):
            risk_score += 0.4
            anomaly_flags.append('unusual_activity')
        
        return SessionSecurity(
            risk_score=risk_score,
            anomaly_flags=anomaly_flags,
            geo_location=self._get_geo_location(current_ip),
            device_trust_level='trusted' if risk_score < 0.3 else 'suspicious',
            authentication_strength=session_info.security_level
        )
    
    def _detect_unusual_activity(self, session_info: SessionInfo) -> bool:
        """Detect unusual activity patterns"""
        # This is a simplified implementation
        # In production, this would use ML models and historical data
        
        # Check for rapid requests (potential bot activity)
        last_activity_age = (datetime.utcnow() - session_info.last_activity).total_seconds()
        if last_activity_age < 1:  # Less than 1 second between requests
            return True
        
        return False
    
    def _get_geo_location(self, ip_address: str) -> Optional[str]:
        """Get geographical location from IP address"""
        # This would integrate with a GeoIP service in production
        # For now, return None
        return None
    
    def _should_regenerate_session(self, session_info: SessionInfo) -> bool:
        """Check if session should be regenerated"""
        session_age = (datetime.utcnow() - session_info.created_at).total_seconds()
        return session_age > self.session_regeneration_interval
    
    def _regenerate_session(self, old_session_info: SessionInfo) -> Tuple[str, SessionInfo]:
        """Regenerate session with new ID"""
        # Create new session
        new_token, new_session_info = self.create_session(
            user_id=old_session_info.user_id,
            security_level=old_session_info.security_level,
            permissions=old_session_info.permissions
        )
        
        # Copy metadata from old session
        new_session_info.metadata = old_session_info.metadata.copy()
        
        # Invalidate old session
        self._invalidate_session(old_session_info.session_id)
        
        # Log regeneration
        self._log_session_event('session_regenerated', new_session_info, {
            'old_session_id': old_session_info.session_id
        })
        
        return new_token, new_session_info
    
    def _invalidate_session(self, session_id: str) -> bool:
        """Invalidate session and clean up"""
        try:
            # Get session info for logging
            session_info = self._get_session(session_id)
            
            # Remove from storage
            key = f"session:{session_id}"
            self.redis_client.delete(key)
            
            # Log invalidation
            if session_info:
                self._log_session_event('session_invalidated', session_info)
            
            return True
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False
    
    def _enforce_session_limits(self, user_id: str):
        """Enforce maximum sessions per user"""
        user_sessions = self.get_user_sessions(user_id)
        
        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest session
            oldest_session = min(user_sessions, key=lambda s: s.created_at)
            self._invalidate_session(oldest_session.session_id)
            logger.info(f"Removed oldest session for user {user_id} due to limit")
    
    def _handle_suspicious_session(self, session_info: SessionInfo, 
                                 security_result: SessionSecurity):
        """Handle suspicious session activity"""
        # Log security event
        self._log_session_event('suspicious_activity', session_info, {
            'risk_score': security_result.risk_score,
            'anomaly_flags': security_result.anomaly_flags
        })
        
        # Invalidate session
        self._invalidate_session(session_info.session_id)
        
        # Could trigger additional security measures here
        logger.warning(f"Suspicious session activity detected: {session_info.session_id}")
    
    def _log_session_event(self, event_type: str, session_info: SessionInfo, 
                          extra_data: Dict[str, Any] = None):
        """Log session events for audit trail"""
        log_data = {
            'event_type': event_type,
            'session_id': session_info.session_id,
            'user_id': session_info.user_id,
            'ip_address': session_info.ip_address,
            'timestamp': datetime.utcnow().isoformat(),
            'security_level': session_info.security_level
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        # Store in audit log
        audit_key = f"audit:session:{int(time.time())}:{secrets.token_hex(8)}"
        self.redis_client.set(audit_key, json.dumps(log_data), ex=2592000)  # 30 days
        
        logger.info(f"Session event logged: {event_type} for {session_info.session_id}")

# Global instance
session_manager = EnterpriseSessionManager()