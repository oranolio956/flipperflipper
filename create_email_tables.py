#!/usr/bin/env python3
"""
Create database tables for email authentication
Elite passwordless authentication system
"""

import sqlite3
from pathlib import Path
from config import Config

DB_PATH = Config.APPLICATION_DIR / 'stitch.db'

# SQL for users_email table
CREATE_USERS_EMAIL = """
CREATE TABLE IF NOT EXISTS users_email (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    is_verified INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0
);
"""

# SQL for email_verification_codes table
CREATE_EMAIL_CODES = """
CREATE TABLE IF NOT EXISTS email_verification_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    ip_address TEXT,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# SQL for email_auth_audit table
CREATE_EMAIL_AUDIT = """
CREATE TABLE IF NOT EXISTS email_auth_audit (
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

# Indexes
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_email_email ON users_email(email);",
    "CREATE INDEX IF NOT EXISTS idx_email_codes_email ON email_verification_codes(email);",
    "CREATE INDEX IF NOT EXISTS idx_email_codes_expires ON email_verification_codes(expires_at);",
    "CREATE INDEX IF NOT EXISTS idx_email_audit_email ON email_auth_audit(email);",
    "CREATE INDEX IF NOT EXISTS idx_email_audit_timestamp ON email_auth_audit(timestamp);",
]

def create_email_tables():
    """Create all email authentication tables"""
    
    # Ensure directory exists
    Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create users_email table
        print("Creating users_email table...")
        cursor.execute(CREATE_USERS_EMAIL)
        print("✅ users_email created")
        
        # Create email_verification_codes table
        print("Creating email_verification_codes table...")
        cursor.execute(CREATE_EMAIL_CODES)
        print("✅ email_verification_codes created")
        
        # Create email_auth_audit table
        print("Creating email_auth_audit table...")
        cursor.execute(CREATE_EMAIL_AUDIT)
        print("✅ email_auth_audit created")
        
        # Create indexes
        print("Creating indexes...")
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
        print("✅ Indexes created")
        
        # Insert primary email
        cursor.execute("""
            INSERT OR IGNORE INTO users_email (email, is_verified, is_active)
            VALUES (?, 1, 1)
        """, ('brooketogo98@gmail.com',))
        print("✅ Primary email added: brooketogo98@gmail.com")
        
        conn.commit()
        print("\n✅ Email authentication tables created successfully!")
        
        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%email%';")
        tables = cursor.fetchall()
        print("\n📋 Email tables:")
        for table in tables:
            print(f"   - {table[0]}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_email_tables()