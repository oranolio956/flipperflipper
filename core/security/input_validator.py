#!/usr/bin/env python3
"""
Enterprise Input Validation Framework
Advanced input validation and sanitization with enterprise-grade security

Features:
- Multi-layer input validation with sanitization
- Command injection prevention framework
- SQL injection prevention with ORM integration
- XSS prevention with context-aware encoding
- File upload security with deep inspection
- Rate limiting per input type
- Input anomaly detection and blocking
"""

import re
import os
import json
import time
import hashlib
import secrets
import mimetypes
import subprocess
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
from urllib.parse import urlparse, quote, unquote
from html import escape, unescape
from config import Config

# Optional dependencies for advanced features
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, file type detection limited")

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    logging.warning("bleach not available, HTML sanitization limited")

try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False
    logging.warning("sqlparse not available, SQL validation limited")

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Input validation security levels"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    PARANOID = "paranoid"

class InputType(Enum):
    """Input data types for context-aware validation"""
    EMAIL = "email"
    USERNAME = "username"
    PASSWORD = "password"
    URL = "url"
    FILENAME = "filename"
    COMMAND = "command"
    SQL_QUERY = "sql_query"
    HTML_CONTENT = "html_content"
    JSON_DATA = "json_data"
    FILE_UPLOAD = "file_upload"
    IP_ADDRESS = "ip_address"
    PHONE_NUMBER = "phone_number"
    CREDIT_CARD = "credit_card"
    GENERIC_TEXT = "generic_text"

@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: Any
    risk_score: float
    violations: List[str]
    metadata: Dict[str, Any]

@dataclass
class ValidationRule:
    """Input validation rule definition"""
    name: str
    pattern: Optional[str]
    min_length: Optional[int]
    max_length: Optional[int]
    allowed_chars: Optional[str]
    forbidden_patterns: List[str]
    custom_validator: Optional[Callable]
    sanitizer: Optional[Callable]

class EnterpriseInputValidator:
    """
    Enterprise-grade input validation and sanitization framework
    
    This class provides comprehensive input validation including:
    - Context-aware validation based on input type
    - Multi-layer security with pattern matching
    - Command injection prevention
    - SQL injection prevention
    - XSS prevention with context-aware encoding
    - File upload security with deep inspection
    - Rate limiting and anomaly detection
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize enterprise input validator"""
        self.validation_level = validation_level
        self.validation_rules = self._initialize_validation_rules()
        self.rate_limits = {}
        self.anomaly_detector = InputAnomalyDetector()
        
        # Security patterns
        self.command_injection_patterns = self._load_command_injection_patterns()
        self.sql_injection_patterns = self._load_sql_injection_patterns()
        self.xss_patterns = self._load_xss_patterns()
        
        # File type detection
        self.magic_mime = magic.Magic(mime=True) if MAGIC_AVAILABLE else None
        
        # Allowed file types for uploads
        self.allowed_file_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'document': ['application/pdf', 'text/plain', 'application/msword'],
            'archive': ['application/zip', 'application/x-tar', 'application/gzip']
        }
        
        logger.info(f"Enterprise Input Validator initialized with {validation_level.value} level")
    
    def validate_input(self, input_data: Any, input_type: InputType, 
                      context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate input data with context-aware security checks
        
        Args:
            input_data: Input data to validate
            input_type: Type of input for context-aware validation
            context: Additional context for validation
            
        Returns:
            ValidationResult with validation status and sanitized data
        """
        context = context or {}
        violations = []
        risk_score = 0.0
        
        try:
            # Rate limiting check
            if not self._check_rate_limit(input_type, context):
                return ValidationResult(
                    is_valid=False,
                    sanitized_input=None,
                    risk_score=1.0,
                    violations=['rate_limit_exceeded'],
                    metadata={'blocked': True}
                )
            
            # Anomaly detection
            anomaly_score = self.anomaly_detector.analyze_input(input_data, input_type)
            if anomaly_score > 0.8:
                violations.append('anomaly_detected')
                risk_score += 0.3
            
            # Type-specific validation
            validation_result = self._validate_by_type(input_data, input_type, context)
            violations.extend(validation_result.violations)
            risk_score += validation_result.risk_score
            
            # Security pattern checks
            security_result = self._check_security_patterns(validation_result.sanitized_input, input_type)
            violations.extend(security_result['violations'])
            risk_score += security_result['risk_score']
            
            # Final sanitization
            final_sanitized = self._final_sanitization(
                validation_result.sanitized_input, input_type, context
            )
            
            # Determine if input is valid
            is_valid = len(violations) == 0 and risk_score < 0.5
            
            return ValidationResult(
                is_valid=is_valid,
                sanitized_input=final_sanitized,
                risk_score=min(risk_score, 1.0),
                violations=violations,
                metadata={
                    'input_type': input_type.value,
                    'validation_level': self.validation_level.value,
                    'anomaly_score': anomaly_score
                }
            )
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return ValidationResult(
                is_valid=False,
                sanitized_input=None,
                risk_score=1.0,
                violations=['validation_error'],
                metadata={'error': str(e)}
            )
    
    def validate_command(self, command: str, allowed_commands: List[str] = None) -> ValidationResult:
        """
        Validate command input with command injection prevention
        
        Args:
            command: Command string to validate
            allowed_commands: List of allowed commands (whitelist)
            
        Returns:
            ValidationResult with command validation status
        """
        violations = []
        risk_score = 0.0
        
        # Check against allowed commands whitelist
        if allowed_commands:
            command_parts = command.strip().split()
            if not command_parts or command_parts[0] not in allowed_commands:
                violations.append('command_not_whitelisted')
                risk_score = 1.0
        
        # Check for command injection patterns
        for pattern in self.command_injection_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append('command_injection_detected')
                risk_score = 1.0
                break
        
        # Check for dangerous characters
        dangerous_chars = ['|', '&', ';', '$', '`', '(', ')', '<', '>', '\n', '\r']
        if any(char in command for char in dangerous_chars):
            violations.append('dangerous_characters')
            risk_score += 0.5
        
        # Sanitize command (if validation level allows)
        sanitized_command = self._sanitize_command(command) if risk_score < 1.0 else None
        
        return ValidationResult(
            is_valid=len(violations) == 0 and risk_score < 0.5,
            sanitized_input=sanitized_command,
            risk_score=risk_score,
            violations=violations,
            metadata={'original_command': command}
        )
    
    def validate_sql_query(self, query: str, allowed_operations: List[str] = None) -> ValidationResult:
        """
        Validate SQL query with injection prevention
        
        Args:
            query: SQL query to validate
            allowed_operations: List of allowed SQL operations
            
        Returns:
            ValidationResult with SQL validation status
        """
        violations = []
        risk_score = 0.0
        
        try:
            # Parse SQL query if sqlparse available
            if SQLPARSE_AVAILABLE:
                parsed = sqlparse.parse(query)
                if not parsed:
                    violations.append('invalid_sql_syntax')
                    risk_score = 1.0
                
                # Check allowed operations
                if allowed_operations and parsed:
                    statement = parsed[0]
                    operation = statement.get_type()
                    if operation.upper() not in [op.upper() for op in allowed_operations]:
                        violations.append('sql_operation_not_allowed')
                        risk_score = 1.0
            else:
                # Basic SQL validation without sqlparse
                if allowed_operations:
                    found_operation = False
                    for op in allowed_operations:
                        if query.strip().upper().startswith(op.upper()):
                            found_operation = True
                            break
                    if not found_operation:
                        violations.append('sql_operation_not_allowed')
                        risk_score = 1.0
            
            # Check for SQL injection patterns
            for pattern in self.sql_injection_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    violations.append('sql_injection_detected')
                    risk_score = 1.0
                    break
            
            # Check for dangerous SQL keywords
            dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
            query_upper = query.upper()
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    violations.append(f'dangerous_sql_keyword_{keyword.lower()}')
                    risk_score += 0.3
            
            # Sanitize query (basic sanitization)
            sanitized_query = self._sanitize_sql_query(query) if risk_score < 1.0 else None
            
        except Exception as e:
            violations.append('sql_parsing_error')
            risk_score = 1.0
            sanitized_query = None
        
        return ValidationResult(
            is_valid=len(violations) == 0 and risk_score < 0.5,
            sanitized_input=sanitized_query,
            risk_score=risk_score,
            violations=violations,
            metadata={'original_query': query}
        )
    
    def validate_file_upload(self, file_data: bytes, filename: str, 
                           allowed_types: List[str] = None) -> ValidationResult:
        """
        Validate file upload with deep security inspection
        
        Args:
            file_data: File content as bytes
            filename: Original filename
            allowed_types: List of allowed file types
            
        Returns:
            ValidationResult with file validation status
        """
        violations = []
        risk_score = 0.0
        metadata = {}
        
        # File size check
        file_size = len(file_data)
        max_size = Config.MAX_UPLOAD_SIZE
        if file_size > max_size:
            violations.append('file_too_large')
            risk_score = 1.0
        
        # Filename validation
        filename_result = self._validate_filename(filename)
        violations.extend(filename_result['violations'])
        risk_score += filename_result['risk_score']
        
        # MIME type detection
        detected_mime = self.magic_mime.from_buffer(file_data)
        metadata['detected_mime_type'] = detected_mime
        
        # File extension vs MIME type consistency check
        file_ext = Path(filename).suffix.lower()
        expected_mime = mimetypes.guess_type(filename)[0]
        if expected_mime and detected_mime != expected_mime:
            violations.append('mime_type_mismatch')
            risk_score += 0.4
        
        # Check against allowed types
        if allowed_types and detected_mime not in allowed_types:
            violations.append('file_type_not_allowed')
            risk_score = 1.0
        
        # Malware scanning (basic checks)
        malware_result = self._scan_for_malware(file_data, detected_mime)
        violations.extend(malware_result['violations'])
        risk_score += malware_result['risk_score']
        
        # Content validation based on file type
        content_result = self._validate_file_content(file_data, detected_mime)
        violations.extend(content_result['violations'])
        risk_score += content_result['risk_score']
        
        # Generate safe filename
        safe_filename = self._generate_safe_filename(filename) if risk_score < 1.0 else None
        
        return ValidationResult(
            is_valid=len(violations) == 0 and risk_score < 0.5,
            sanitized_input={'filename': safe_filename, 'content': file_data},
            risk_score=min(risk_score, 1.0),
            violations=violations,
            metadata=metadata
        )
    
    def _initialize_validation_rules(self) -> Dict[InputType, ValidationRule]:
        """Initialize validation rules for different input types"""
        rules = {}
        
        # Email validation
        rules[InputType.EMAIL] = ValidationRule(
            name="email",
            pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            min_length=5,
            max_length=254,
            allowed_chars=None,
            forbidden_patterns=[r'<script', r'javascript:', r'data:'],
            custom_validator=self._validate_email_advanced,
            sanitizer=self._sanitize_email
        )
        
        # Username validation
        rules[InputType.USERNAME] = ValidationRule(
            name="username",
            pattern=r'^[a-zA-Z0-9_.-]+$',
            min_length=3,
            max_length=50,
            allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-",
            forbidden_patterns=[r'admin', r'root', r'system'],
            custom_validator=None,
            sanitizer=self._sanitize_username
        )
        
        # Password validation
        rules[InputType.PASSWORD] = ValidationRule(
            name="password",
            pattern=None,  # Complex password validation in custom validator
            min_length=12,
            max_length=128,
            allowed_chars=None,
            forbidden_patterns=[],
            custom_validator=self._validate_password_strength,
            sanitizer=None  # Passwords should not be sanitized
        )
        
        # URL validation
        rules[InputType.URL] = ValidationRule(
            name="url",
            pattern=r'^https?://[^\s/$.?#].[^\s]*$',
            min_length=10,
            max_length=2048,
            allowed_chars=None,
            forbidden_patterns=[r'javascript:', r'data:', r'file:', r'ftp:'],
            custom_validator=self._validate_url_advanced,
            sanitizer=self._sanitize_url
        )
        
        # Add more rules for other input types...
        
        return rules
    
    def _validate_by_type(self, input_data: Any, input_type: InputType, 
                         context: Dict[str, Any]) -> ValidationResult:
        """Validate input based on its type"""
        violations = []
        risk_score = 0.0
        
        # Get validation rule for input type
        rule = self.validation_rules.get(input_type)
        if not rule:
            # Generic validation for unknown types
            return self._validate_generic(input_data)
        
        # Convert input to string for validation
        input_str = str(input_data) if input_data is not None else ""
        
        # Length validation
        if rule.min_length and len(input_str) < rule.min_length:
            violations.append('input_too_short')
            risk_score += 0.2
        
        if rule.max_length and len(input_str) > rule.max_length:
            violations.append('input_too_long')
            risk_score += 0.3
        
        # Pattern validation
        if rule.pattern and not re.match(rule.pattern, input_str):
            violations.append('pattern_mismatch')
            risk_score += 0.4
        
        # Allowed characters validation
        if rule.allowed_chars:
            for char in input_str:
                if char not in rule.allowed_chars:
                    violations.append('forbidden_character')
                    risk_score += 0.1
                    break
        
        # Forbidden patterns check
        for pattern in rule.forbidden_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                violations.append('forbidden_pattern_detected')
                risk_score += 0.5
        
        # Custom validation
        if rule.custom_validator:
            custom_result = rule.custom_validator(input_str, context)
            violations.extend(custom_result.get('violations', []))
            risk_score += custom_result.get('risk_score', 0.0)
        
        # Sanitization
        sanitized_input = input_str
        if rule.sanitizer and risk_score < 1.0:
            sanitized_input = rule.sanitizer(input_str)
        
        return ValidationResult(
            is_valid=len(violations) == 0 and risk_score < 0.5,
            sanitized_input=sanitized_input,
            risk_score=risk_score,
            violations=violations,
            metadata={'rule_name': rule.name}
        )
    
    def _check_security_patterns(self, input_data: str, input_type: InputType) -> Dict[str, Any]:
        """Check input against security patterns"""
        violations = []
        risk_score = 0.0
        
        # Command injection check
        for pattern in self.command_injection_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                violations.append('command_injection_pattern')
                risk_score += 0.8
                break
        
        # SQL injection check
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                violations.append('sql_injection_pattern')
                risk_score += 0.8
                break
        
        # XSS check
        for pattern in self.xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                violations.append('xss_pattern')
                risk_score += 0.6
                break
        
        return {
            'violations': violations,
            'risk_score': risk_score
        }
    
    def _load_command_injection_patterns(self) -> List[str]:
        """Load command injection detection patterns"""
        return [
            r';\s*rm\s+',
            r';\s*cat\s+',
            r';\s*ls\s+',
            r';\s*ps\s+',
            r';\s*kill\s+',
            r';\s*wget\s+',
            r';\s*curl\s+',
            r'\|\s*nc\s+',
            r'\|\s*netcat\s+',
            r'`[^`]*`',
            r'\$\([^)]*\)',
            r'&&\s*[a-zA-Z]',
            r'\|\|\s*[a-zA-Z]',
            r'>\s*/dev/',
            r'<\s*/dev/',
            r'/bin/sh',
            r'/bin/bash',
            r'cmd\.exe',
            r'powershell',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
            r'passthru\s*\(',
        ]
    
    def _load_sql_injection_patterns(self) -> List[str]:
        """Load SQL injection detection patterns"""
        return [
            r"'\s*OR\s+'",
            r'"\s*OR\s+"',
            r"'\s*AND\s+'",
            r'"\s*AND\s+"',
            r"'\s*UNION\s+",
            r'"\s*UNION\s+',
            r"'\s*;\s*DROP\s+",
            r'"\s*;\s*DROP\s+',
            r"'\s*;\s*DELETE\s+",
            r'"\s*;\s*DELETE\s+',
            r"'\s*;\s*INSERT\s+",
            r'"\s*;\s*INSERT\s+',
            r"'\s*;\s*UPDATE\s+",
            r'"\s*;\s*UPDATE\s+',
            r'--\s*$',
            r'/\*.*\*/',
            r'xp_cmdshell',
            r'sp_executesql',
            r'EXEC\s*\(',
            r'EXECUTE\s*\(',
        ]
    
    def _load_xss_patterns(self) -> List[str]:
        """Load XSS detection patterns"""
        return [
            r'<script[^>]*>',
            r'</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'data:text/html',
            r'data:application/javascript',
        ]
    
    def _validate_email_advanced(self, email: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced email validation"""
        violations = []
        risk_score = 0.0
        
        # Check for disposable email domains
        disposable_domains = ['tempmail.org', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1] if '@' in email else ''
        if domain in disposable_domains:
            violations.append('disposable_email_domain')
            risk_score += 0.3
        
        # Check for suspicious patterns
        if re.search(r'\+.*@', email):  # Plus addressing
            violations.append('plus_addressing_detected')
            risk_score += 0.1
        
        return {'violations': violations, 'risk_score': risk_score}
    
    def _validate_password_strength(self, password: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password strength"""
        violations = []
        risk_score = 0.0
        
        # Length check
        if len(password) < 12:
            violations.append('password_too_short')
            risk_score += 0.5
        
        # Complexity checks
        if not re.search(r'[a-z]', password):
            violations.append('no_lowercase')
            risk_score += 0.2
        
        if not re.search(r'[A-Z]', password):
            violations.append('no_uppercase')
            risk_score += 0.2
        
        if not re.search(r'\d', password):
            violations.append('no_digits')
            risk_score += 0.2
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            violations.append('no_special_chars')
            risk_score += 0.2
        
        # Common password check
        common_passwords = ['password123', 'admin123', 'qwerty123']
        if password.lower() in common_passwords:
            violations.append('common_password')
            risk_score += 0.8
        
        return {'violations': violations, 'risk_score': risk_score}
    
    def _validate_url_advanced(self, url: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced URL validation"""
        violations = []
        risk_score = 0.0
        
        try:
            parsed = urlparse(url)
            
            # Check for suspicious schemes
            if parsed.scheme not in ['http', 'https']:
                violations.append('suspicious_url_scheme')
                risk_score += 0.5
            
            # Check for IP addresses instead of domains
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', parsed.hostname or ''):
                violations.append('ip_address_in_url')
                risk_score += 0.3
            
            # Check for suspicious ports
            if parsed.port and parsed.port in [22, 23, 135, 139, 445]:
                violations.append('suspicious_port')
                risk_score += 0.4
            
        except Exception:
            violations.append('invalid_url_format')
            risk_score += 0.5
        
        return {'violations': violations, 'risk_score': risk_score}
    
    def _sanitize_email(self, email: str) -> str:
        """Sanitize email address"""
        # Convert to lowercase and strip whitespace
        return email.lower().strip()
    
    def _sanitize_username(self, username: str) -> str:
        """Sanitize username"""
        # Remove any non-allowed characters
        return re.sub(r'[^a-zA-Z0-9_.-]', '', username.strip())
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL"""
        # URL encode and validate
        return quote(url.strip(), safe=':/?#[]@!$&\'()*+,;=')
    
    def _sanitize_command(self, command: str) -> str:
        """Sanitize command (very restrictive)"""
        # Only allow alphanumeric characters, spaces, and basic punctuation
        return re.sub(r'[^a-zA-Z0-9\s\-_./]', '', command.strip())
    
    def _sanitize_sql_query(self, query: str) -> str:
        """Basic SQL query sanitization"""
        # Remove comments and normalize whitespace
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        return ' '.join(query.split())
    
    def _final_sanitization(self, input_data: Any, input_type: InputType, 
                           context: Dict[str, Any]) -> Any:
        """Apply final sanitization based on context"""
        if input_type == InputType.HTML_CONTENT:
            # Use bleach for HTML sanitization if available
            if BLEACH_AVAILABLE:
                allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
                return bleach.clean(str(input_data), tags=allowed_tags, strip=True)
            else:
                # Fallback to basic HTML escaping
                return escape(str(input_data))
        
        elif input_type == InputType.JSON_DATA:
            # Validate and sanitize JSON
            try:
                if isinstance(input_data, str):
                    return json.loads(input_data)
                return input_data
            except json.JSONDecodeError:
                return None
        
        return input_data
    
    def _validate_generic(self, input_data: Any) -> ValidationResult:
        """Generic validation for unknown input types"""
        violations = []
        risk_score = 0.0
        
        input_str = str(input_data) if input_data is not None else ""
        
        # Basic length check
        if len(input_str) > 10000:  # 10KB limit
            violations.append('input_too_large')
            risk_score += 0.5
        
        # Check for null bytes
        if '\x00' in input_str:
            violations.append('null_byte_detected')
            risk_score += 0.8
        
        # Basic HTML escape for safety
        sanitized_input = escape(input_str)
        
        return ValidationResult(
            is_valid=len(violations) == 0 and risk_score < 0.5,
            sanitized_input=sanitized_input,
            risk_score=risk_score,
            violations=violations,
            metadata={'generic_validation': True}
        )
    
    def _check_rate_limit(self, input_type: InputType, context: Dict[str, Any]) -> bool:
        """Check rate limiting for input validation"""
        # Simple rate limiting implementation
        client_id = context.get('client_id', 'unknown')
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - 3600  # 1 hour window
        self.rate_limits = {
            k: v for k, v in self.rate_limits.items()
            if v['timestamp'] > cutoff_time
        }
        
        # Check current rate
        key = f"{client_id}:{input_type.value}"
        if key in self.rate_limits:
            if self.rate_limits[key]['count'] > 1000:  # 1000 requests per hour
                return False
            self.rate_limits[key]['count'] += 1
        else:
            self.rate_limits[key] = {'count': 1, 'timestamp': current_time}
        
        return True
    
    def _validate_filename(self, filename: str) -> Dict[str, Any]:
        """Validate filename for security"""
        violations = []
        risk_score = 0.0
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            violations.append('path_traversal_attempt')
            risk_score += 0.8
        
        # Check for dangerous extensions
        dangerous_exts = ['.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js']
        file_ext = Path(filename).suffix.lower()
        if file_ext in dangerous_exts:
            violations.append('dangerous_file_extension')
            risk_score += 0.9
        
        # Check filename length
        if len(filename) > 255:
            violations.append('filename_too_long')
            risk_score += 0.3
        
        return {'violations': violations, 'risk_score': risk_score}
    
    def _scan_for_malware(self, file_data: bytes, mime_type: str) -> Dict[str, Any]:
        """Basic malware scanning"""
        violations = []
        risk_score = 0.0
        
        # Check for suspicious signatures
        suspicious_signatures = [
            b'MZ',  # PE executable header
            b'PK',  # ZIP header (could contain malware)
            b'<script',  # JavaScript in unexpected files
            b'eval(',  # Eval function
        ]
        
        for signature in suspicious_signatures:
            if signature in file_data:
                violations.append('suspicious_file_signature')
                risk_score += 0.5
                break
        
        # Check file size anomalies
        if mime_type.startswith('image/') and len(file_data) > 10 * 1024 * 1024:  # 10MB
            violations.append('unusually_large_image')
            risk_score += 0.3
        
        return {'violations': violations, 'risk_score': risk_score}
    
    def _validate_file_content(self, file_data: bytes, mime_type: str) -> Dict[str, Any]:
        """Validate file content based on MIME type"""
        violations = []
        risk_score = 0.0
        
        try:
            if mime_type.startswith('image/'):
                # Basic image validation
                from PIL import Image
                import io
                
                try:
                    img = Image.open(io.BytesIO(file_data))
                    img.verify()
                except Exception:
                    violations.append('corrupted_image_file')
                    risk_score += 0.4
            
            elif mime_type == 'application/pdf':
                # Basic PDF validation
                if not file_data.startswith(b'%PDF-'):
                    violations.append('invalid_pdf_header')
                    risk_score += 0.5
            
        except ImportError:
            # PIL not available, skip image validation
            pass
        except Exception as e:
            violations.append('file_content_validation_error')
            risk_score += 0.2
        
        return {'violations': violations, 'risk_score': risk_score}
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """Generate safe filename"""
        # Extract extension
        path = Path(original_filename)
        name = path.stem
        ext = path.suffix
        
        # Sanitize name
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
        safe_name = safe_name[:50]  # Limit length
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{safe_name}_{timestamp}{ext}"

class InputAnomalyDetector:
    """Detect anomalous input patterns"""
    
    def __init__(self):
        self.baseline_patterns = {}
        self.anomaly_threshold = 0.8
    
    def analyze_input(self, input_data: Any, input_type: InputType) -> float:
        """Analyze input for anomalies"""
        # Simplified anomaly detection
        # In production, this would use ML models
        
        input_str = str(input_data) if input_data is not None else ""
        
        # Check for unusual length
        avg_length = self.baseline_patterns.get(f"{input_type.value}_avg_length", 50)
        length_ratio = len(input_str) / max(avg_length, 1)
        
        if length_ratio > 5 or length_ratio < 0.1:
            return 0.9
        
        # Check for unusual character distribution
        char_entropy = self._calculate_entropy(input_str)
        if char_entropy > 4.5:  # High entropy might indicate encoded/encrypted data
            return 0.8
        
        return 0.0
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        import math
        from collections import Counter
        
        counter = Counter(text)
        length = len(text)
        
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy

# Global instance
input_validator = EnterpriseInputValidator()