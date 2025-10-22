#!/usr/bin/env python3
"""
Create Email Authentication Database Tables
Ultra-secure email verification system
"""

import sqlite3
import os
from datetime import datetime

def create_email_tables():
    """Create all email authentication database tables"""
    
    # Database path
    db_path = '/workspace/Application/stitch.db'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating email authentication tables...")
        
        # 1. Users Email Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_email (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP NULL,
                UNIQUE(email)
            )
        ''')
        
        # 2. Email Verification Codes Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP NULL,
                is_used BOOLEAN DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                FOREIGN KEY (email) REFERENCES users_email(email)
            )
        ''')
        
        # 3. Email Authentication Audit Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_auth_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                event_type TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users_email(email)
            )
        ''')
        
        # 4. Rate Limiting Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                request_count INTEGER DEFAULT 1,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                blocked_until TIMESTAMP NULL,
                UNIQUE(email, ip_address)
            )
        ''')
        
        # Create indexes for performance
        print("📊 Creating database indexes...")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_codes_email ON email_verification_codes(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_codes_expires ON email_verification_codes(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_codes_used ON email_verification_codes(is_used)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_audit_email ON email_auth_audit(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_audit_timestamp ON email_auth_audit(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_email ON email_rate_limits(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email_active ON users_email(email, is_active)')
        
        # Commit changes
        conn.commit()
        
        # Verify tables created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%email%'")
        tables = cursor.fetchall()
        
        print("✅ Email authentication tables created successfully:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Show table counts
        for table_name in ['users_email', 'email_verification_codes', 'email_auth_audit', 'email_rate_limits']:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
        
        conn.close()
        
        print(f"📁 Database location: {db_path}")
        print("🔐 Email authentication system ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating email tables: {e}")
        return False

if __name__ == "__main__":
    success = create_email_tables()
    if success:
        print("\n🏆 Email database setup complete!")
    else:
        print("\n💥 Email database setup failed!")
        exit(1)