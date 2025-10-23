#!/usr/bin/env python3
"""
Create MFA database tables
Elite passwordless authentication system with TOTP MFA
"""

import sqlite3
from pathlib import Path
from config import Config

# Database path
DB_PATH = Config.APPLICATION_DIR / 'stitch.db'

# SQL to create tables
CREATE_USER_MFA_TABLE = """
CREATE TABLE IF NOT EXISTS user_mfa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    mfa_secret TEXT NOT NULL,
    mfa_enabled INTEGER DEFAULT 0,
    backup_codes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    FOREIGN KEY (email) REFERENCES users_email(email) ON DELETE CASCADE
);
"""

CREATE_MFA_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS mfa_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    action TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    success INTEGER DEFAULT 1,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_user_mfa_email ON user_mfa(email);",
    "CREATE INDEX IF NOT EXISTS idx_mfa_audit_email ON mfa_audit_log(email);",
    "CREATE INDEX IF NOT EXISTS idx_mfa_audit_timestamp ON mfa_audit_log(timestamp);",
]

def create_mfa_tables():
    """Create MFA tables in database"""
    
    # Ensure directory exists
    Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Database path: {DB_PATH}")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create user_mfa table
        print("Creating user_mfa table...")
        cursor.execute(CREATE_USER_MFA_TABLE)
        print("✅ user_mfa table created")
        
        # Create mfa_audit_log table
        print("Creating mfa_audit_log table...")
        cursor.execute(CREATE_MFA_AUDIT_TABLE)
        print("✅ mfa_audit_log table created")
        
        # Create indexes
        print("Creating indexes...")
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
        print("✅ Indexes created")
        
        # Commit changes
        conn.commit()
        print("\n✅ MFA database tables created successfully!")
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%mfa%';")
        tables = cursor.fetchall()
        print("\n📋 MFA tables in database:")
        for table in tables:
            print(f"   - {table[0]}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_mfa_tables()