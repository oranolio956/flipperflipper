#!/usr/bin/env python3
"""
Simple configuration for testing
"""

import os
from pathlib import Path

class Config:
    """Simple configuration class"""
    
    # Base directories
    BASE_DIR = Path(__file__).parent
    APPLICATION_DIR = BASE_DIR / "Application"
    
    # Server Configuration
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
    STITCH_SERVER_PORT = 4040
    
    # Email Configuration
    FROM_EMAIL = 'brooketogo98@gmail.com'
    FROM_NAME = 'Oranolio Security'
    USE_AUTOMATED_EMAIL = True
    AUTHORIZED_EMAILS = ['brooketogo98@gmail.com']
    
    # Security
    SECRET_KEY = 'test-secret-key-for-development-only'
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TIMEOUT_MINUTES = 30
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    COMMANDS_PER_MINUTE = 60
    EXECUTIONS_PER_MINUTE = 30
    API_POLLING_PER_HOUR = 1000
    DEFAULT_RATE_LIMIT_DAY = 10000
    DEFAULT_RATE_LIMIT_HOUR = 1000
    
    # Logging
    MAX_DEBUG_LOGS = 1000
    MAX_COMMAND_HISTORY = 1000
    DEFAULT_LOG_FETCH_LIMIT = 100
    DEFAULT_HISTORY_FETCH_LIMIT = 100