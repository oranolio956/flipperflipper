#!/usr/bin/env python3
"""
Comprehensive Input Validation Module for Stitch RAT
Provides security-focused validation for all user inputs
"""
import re
import os
import ipaddress
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
from urllib.parse import urlparse

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    """Comprehensive input validation class"""
    
    # Security patterns
    DANGEROUS_PATTERNS = [
        r'[;&|`$()]',           # Command injection
        r'\.\./|\.\.\\',        # Path traversal
        r'<script|javascript:', # XSS attempts
        r'union\s+select',      # SQL injection
        r'exec\s*\(',          # Code execution
        r'eval\s*\(',          # Code evaluation
        r'system\s*\(',        # System calls
        r'__import__',         # Python imports
        r'subprocess',         # Process execution
        r'rm\s+-rf\s+/',       # Dangerous rm commands
        r'del\s+/\*',          # Dangerous delete commands
        r'format\s+c:',        # Format commands
        r'dd\s+if=.*of=',      # Disk operations
    ]
    
    # File extension whitelist
    ALLOWED_EXTENSIONS = {
        '.txt', '.log', '.csv', '.json', '.xml', '.yml', '.yaml',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
        '.zip', '.tar', '.gz', '.7z', '.rar',
        '.py', '.js', '.html', '.css', '.md'
    }
    
    # Maximum lengths
    MAX_COMMAND_LENGTH = 500
    MAX_FILENAME_LENGTH = 255
    MAX_PATH_LENGTH = 4096
    MAX_USERNAME_LENGTH = 64
    MAX_HOSTNAME_LENGTH = 253
    MAX_MESSAGE_LENGTH = 1000
    
    @classmethod
    def validate_command(cls, command: str) -> str:
        """
        Validate command input for security and format
        
        Args:
            command: Command string to validate
            
        Returns:
            str: Cleaned command string
            
        Raises:
            ValidationError: If command is invalid or dangerous
        """
        if not command or not isinstance(command, str):
            raise ValidationError("Command cannot be empty or non-string")
        
        # Strip whitespace
        command = command.strip()
        
        if not command:
            raise ValidationError("Command cannot be empty after trimming")
        
        # Length check
        if len(command) > cls.MAX_COMMAND_LENGTH:
            raise ValidationError(f"Command too long (max {cls.MAX_COMMAND_LENGTH} chars)")
        
        # Check for null bytes and control characters
        if any(ord(c) < 32 and c not in '\t\n\r' for c in command):
            raise ValidationError("Command contains invalid control characters")
        
        # Check for dangerous patterns
        command_lower = command.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                raise ValidationError(f"Command contains potentially dangerous pattern: {pattern}")
        
        # Normalize whitespace
        command = ' '.join(command.split())
        
        return command
    
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """
        Validate filename for security and format
        
        Args:
            filename: Filename to validate
            
        Returns:
            str: Cleaned filename
            
        Raises:
            ValidationError: If filename is invalid or dangerous
        """
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename cannot be empty or non-string")
        
        filename = filename.strip()
        
        if not filename:
            raise ValidationError("Filename cannot be empty after trimming")
        
        # Length check
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            raise ValidationError(f"Filename too long (max {cls.MAX_FILENAME_LENGTH} chars)")
        
        # Path traversal check
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("Filename contains path traversal characters")
        
        # Reserved names check (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            raise ValidationError(f"Filename uses reserved name: {name_without_ext}")
        
        # Invalid characters check
        invalid_chars = '<>:"|?*'
        if any(char in filename for char in invalid_chars):
            raise ValidationError(f"Filename contains invalid characters: {invalid_chars}")
        
        return filename
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> str:
        """
        Validate file path for security
        
        Args:
            file_path: File path to validate
            
        Returns:
            str: Cleaned file path
            
        Raises:
            ValidationError: If path is invalid or dangerous
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path cannot be empty or non-string")
        
        file_path = file_path.strip()
        
        if not file_path:
            raise ValidationError("File path cannot be empty after trimming")
        
        # Length check
        if len(file_path) > cls.MAX_PATH_LENGTH:
            raise ValidationError(f"File path too long (max {cls.MAX_PATH_LENGTH} chars)")
        
        # Path traversal check
        normalized_path = os.path.normpath(file_path)
        if '..' in normalized_path.split(os.sep):
            raise ValidationError("File path contains path traversal")
        
        # Absolute path check for security
        if os.path.isabs(file_path):
            # Only allow certain absolute paths
            allowed_prefixes = ['/tmp/', '/var/tmp/', 'C:\\Windows\\Temp\\', 'C:\\Temp\\']
            if not any(file_path.startswith(prefix) for prefix in allowed_prefixes):
                raise ValidationError("Absolute path not in allowed directories")
        
        return file_path
    
    @classmethod
    def validate_ip_address(cls, ip_address: str) -> str:
        """
        Validate IP address format
        
        Args:
            ip_address: IP address to validate
            
        Returns:
            str: Validated IP address
            
        Raises:
            ValidationError: If IP address is invalid
        """
        if not ip_address or not isinstance(ip_address, str):
            raise ValidationError("IP address cannot be empty or non-string")
        
        ip_address = ip_address.strip()
        
        try:
            # This will raise ValueError if invalid
            ipaddress.ip_address(ip_address)
            return ip_address
        except ValueError:
            raise ValidationError(f"Invalid IP address format: {ip_address}")
    
    @classmethod
    def validate_port(cls, port: Union[str, int]) -> int:
        """
        Validate port number
        
        Args:
            port: Port number to validate
            
        Returns:
            int: Validated port number
            
        Raises:
            ValidationError: If port is invalid
        """
        if isinstance(port, str):
            port = port.strip()
            if not port:
                raise ValidationError("Port cannot be empty")
            
            try:
                port = int(port)
            except ValueError:
                raise ValidationError(f"Port must be a number: {port}")
        
        if not isinstance(port, int):
            raise ValidationError("Port must be an integer")
        
        if not (1 <= port <= 65535):
            raise ValidationError(f"Port must be between 1-65535: {port}")
        
        return port
    
    @classmethod
    def validate_hostname(cls, hostname: str) -> str:
        """
        Validate hostname format
        
        Args:
            hostname: Hostname to validate
            
        Returns:
            str: Validated hostname
            
        Raises:
            ValidationError: If hostname is invalid
        """
        if not hostname or not isinstance(hostname, str):
            raise ValidationError("Hostname cannot be empty or non-string")
        
        hostname = hostname.strip().lower()
        
        if not hostname:
            raise ValidationError("Hostname cannot be empty after trimming")
        
        # Length check
        if len(hostname) > cls.MAX_HOSTNAME_LENGTH:
            raise ValidationError(f"Hostname too long (max {cls.MAX_HOSTNAME_LENGTH} chars)")
        
        # Format check
        hostname_pattern = r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$'
        if not re.match(hostname_pattern, hostname):
            raise ValidationError(f"Invalid hostname format: {hostname}")
        
        return hostname
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """
        Validate username format
        
        Args:
            username: Username to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValidationError: If username is invalid
        """
        if not username or not isinstance(username, str):
            raise ValidationError("Username cannot be empty or non-string")
        
        username = username.strip()
        
        if not username:
            raise ValidationError("Username cannot be empty after trimming")
        
        # Length check
        if len(username) > cls.MAX_USERNAME_LENGTH:
            raise ValidationError(f"Username too long (max {cls.MAX_USERNAME_LENGTH} chars)")
        
        # Format check - alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscore, and hyphen")
        
        # Must start with letter or number
        if not re.match(r'^[a-zA-Z0-9]', username):
            raise ValidationError("Username must start with a letter or number")
        
        return username
    
    @classmethod
    def validate_message(cls, message: str) -> str:
        """
        Validate message content
        
        Args:
            message: Message to validate
            
        Returns:
            str: Validated message
            
        Raises:
            ValidationError: If message is invalid
        """
        if not isinstance(message, str):
            raise ValidationError("Message must be a string")
        
        # Allow empty messages for some use cases
        if not message:
            return message
        
        # Length check
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            raise ValidationError(f"Message too long (max {cls.MAX_MESSAGE_LENGTH} chars)")
        
        # Check for dangerous content
        message_lower = message.lower()
        dangerous_patterns = [
            r'<script', r'javascript:', r'vbscript:', r'onload=',
            r'onerror=', r'onclick=', r'onmouseover='
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, message_lower):
                raise ValidationError(f"Message contains potentially dangerous content: {pattern}")
        
        return message
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """
        Check if file extension is allowed
        
        Args:
            filename: Filename to check
            
        Returns:
            bool: True if extension is allowed
        """
        if not filename:
            return False
        
        # Get extension
        _, ext = os.path.splitext(filename.lower())
        
        # Allow files without extension
        if not ext:
            return True
        
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def validate_timestamp(cls, timestamp: str) -> str:
        """
        Validate timestamp format
        
        Args:
            timestamp: Timestamp string to validate
            
        Returns:
            str: Validated timestamp
            
        Raises:
            ValidationError: If timestamp format is invalid
        """
        if not timestamp or not isinstance(timestamp, str):
            raise ValidationError("Timestamp cannot be empty or non-string")
        
        timestamp = timestamp.strip()
        
        # Expected format: MM/DD/YYYY HH:mm:ss
        timestamp_pattern = r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$'
        if not re.match(timestamp_pattern, timestamp):
            raise ValidationError("Timestamp must be in format 'MM/DD/YYYY HH:mm:ss'")
        
        # Additional validation - check if date components are valid
        try:
            from datetime import datetime
            datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
        except ValueError as e:
            raise ValidationError(f"Invalid timestamp: {e}")
        
        return timestamp
    
    @classmethod
    def sanitize_for_log(cls, data: str, max_length: int = 200) -> str:
        """
        Sanitize data for safe logging
        
        Args:
            data: Data to sanitize
            max_length: Maximum length for output
            
        Returns:
            str: Sanitized data safe for logging
        """
        if not isinstance(data, str):
            data = str(data)
        
        # Remove sensitive patterns
        sensitive_patterns = [
            (r'(password|passwd|pwd|pass)[\s=:]+[\S]+', r'\1=[REDACTED]'),
            (r'(key|apikey|api_key|token|secret)[\s=:]+[\S]+', r'\1=[REDACTED]'),
            (r'(auth|authorization|bearer)[\s=:]+[\S]+', r'\1=[REDACTED]'),
        ]
        
        sanitized = data
        for pattern, replacement in sensitive_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + '... [truncated]'
        
        return sanitized

# Convenience functions for common validations
def validate_command_input(command: str) -> str:
    """Validate command input"""
    return InputValidator.validate_command(command)

def validate_connection_id(conn_id: str) -> str:
    """Validate connection ID (IP address)"""
    return InputValidator.validate_ip_address(conn_id)

def validate_upload_filename(filename: str) -> str:
    """Validate uploaded filename"""
    validated = InputValidator.validate_filename(filename)
    
    if not InputValidator.validate_file_extension(filename):
        raise ValidationError(f"File extension not allowed: {filename}")
    
    return validated

def validate_parameter_value(param_name: str, value: str, param_type: str) -> Union[str, int]:
    """
    Validate parameter value based on type
    
    Args:
        param_name: Parameter name
        value: Parameter value
        param_type: Parameter type (text, number, select)
        
    Returns:
        Validated value (string or int)
        
    Raises:
        ValidationError: If validation fails
    """
    if param_type == 'number':
        if param_name == 'port':
            return InputValidator.validate_port(value)
        else:
            try:
                return int(value)
            except ValueError:
                raise ValidationError(f"Parameter {param_name} must be a number")
    
    elif param_type == 'text':
        if param_name in ['hostname', 'ipaddress']:
            if param_name == 'hostname':
                return InputValidator.validate_hostname(value)
            else:
                return InputValidator.validate_ip_address(value)
        elif param_name == 'file':
            return InputValidator.validate_file_path(value)
        elif param_name == 'timestamp':
            return InputValidator.validate_timestamp(value)
        elif param_name == 'message':
            return InputValidator.validate_message(value)
        else:
            # Generic text validation
            if not value or len(value) > 500:
                raise ValidationError(f"Parameter {param_name} invalid length")
            return value.strip()
    
    elif param_type == 'select':
        # For select types, just return the value (options validated elsewhere)
        return value.strip() if isinstance(value, str) else str(value)
    
    else:
        raise ValidationError(f"Unknown parameter type: {param_type}")

# Export main classes and functions
__all__ = [
    'ValidationError',
    'InputValidator', 
    'validate_command_input',
    'validate_connection_id',
    'validate_upload_filename',
    'validate_parameter_value'
]