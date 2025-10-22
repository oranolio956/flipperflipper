#!/usr/bin/env python3
"""
Simple Configuration for MFA Testing
"""

import os
from pathlib import Path
from datetime import timedelta

class Config:
    # Basic app settings
    APP_NAME = "Oranolio RAT"
    APP_VERSION = "1.1.0"
    
    # Directories
    BASE_DIR = Path(__file__).parent
    APPLICATION_DIR = BASE_DIR / "Application"
    LOGS_DIR = BASE_DIR / "Logs"
    TEMP_DIR = BASE_DIR / "Temp"
    UPLOADS_DIR = BASE_DIR / "Uploads"
    DOWNLOADS_DIR = BASE_DIR / "Downloads"
    
    # Server settings
    HOST = os.getenv('STITCH_HOST', '0.0.0.0')
    PORT = int(os.getenv('STITCH_PORT', '5000'))
    DEBUG = os.getenv('STITCH_DEBUG', 'false').lower() in ('true', '1', 'yes')
    
    # Email settings
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'test@example.com')
    FROM_NAME = os.getenv('FROM_NAME', 'Test Security')
    
    # Automated email
    USE_AUTOMATED_EMAIL = os.getenv('USE_AUTOMATED_EMAIL', 'true').lower() in ('true', '1', 'yes')
    
    # Security
    SECRET_KEY = os.getenv('STITCH_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TIMEOUT_MINUTES = 30
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    # Rate limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    
    # Database
    SQLITE_DB_FILE = APPLICATION_DIR / 'stitch.db'