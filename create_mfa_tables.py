#!/usr/bin/env python3
"""
Create MFA (Multi-Factor Authentication) Database Tables
TOTP + Backup Codes with enterprise-grade security
"""

import sqlite3
import os
from datetime import datetime

def create_mfa_tables():
    """Create all MFA database tables"""
    
    # Database path
    db_path = '/workspace/Application/stitch.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating MFA authentication tables...")
        
        # 1. User MFA Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_mfa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                mfa_secret TEXT NOT NULL,
                backup_codes TEXT,
                is_enabled BOOLEAN DEFAULT 0,
                setup_completed_at TIMESTAMP NULL,
                last_totp_used INTEGER DEFAULT 0,
                recovery_codes_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users_email(email),
                UNIQUE(email)
            )
        ''')
        
        # 2. MFA Backup Codes Table (separate for better security)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_backup_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                is_used BOOLEAN DEFAULT 0,
                used_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users_email(email)
            )
        ''')
        
        # 3. MFA Audit Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                event_type TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                totp_code TEXT NULL,
                success BOOLEAN NOT NULL,
                failure_reason TEXT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users_email(email)
            )
        ''')
        
        # 4. MFA Session Tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (email) REFERENCES users_email(email)
            )
        ''')
        
        # Create indexes for performance
        print("📊 Creating MFA database indexes...")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_mfa_email ON user_mfa(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_mfa_enabled ON user_mfa(email, is_enabled)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_backup_codes_email ON mfa_backup_codes(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_backup_codes_used ON mfa_backup_codes(email, is_used)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_audit_email ON mfa_audit_log(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_audit_timestamp ON mfa_audit_log(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_sessions_email ON mfa_sessions(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_sessions_token ON mfa_sessions(session_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mfa_sessions_active ON mfa_sessions(is_active, expires_at)')
        
        # Commit changes
        conn.commit()
        
        # Verify tables created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%mfa%'")
        tables = cursor.fetchall()
        
        print("✅ MFA authentication tables created successfully:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Show table counts
        for table_name in ['user_mfa', 'mfa_backup_codes', 'mfa_audit_log', 'mfa_sessions']:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
        
        conn.close()
        
        print(f"📁 Database location: {db_path}")
        print("🔐 MFA system ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating MFA tables: {e}")
        return False

if __name__ == "__main__":
    success = create_mfa_tables()
    if success:
        print("\n🏆 MFA database setup complete!")
    else:
        print("\n💥 MFA database setup failed!")
        exit(1)