#!/usr/bin/env python3
"""
Test Authentication Flow - Bypass config issues
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from automated_email_service import automated_email_service

# Use simple config
from simple_config import Config

DB_PATH = Config.APPLICATION_DIR / 'stitch.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_verification_code(length=6):
    """Generate cryptographically secure numeric code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

def hash_code(code):
    """Hash verification code for secure storage"""
    return hashlib.sha256(code.encode()).hexdigest()

def create_verification_code(email, ip_address=""):
    """Generate and store verification code for email"""
    code = generate_verification_code(6)
    code_hash = hash_code(code)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO email_verification_codes 
            (email, code_hash, ip_address, expires_at)
            VALUES (?, ?, ?, ?)
        """, (email, code_hash, ip_address, expires_at))
        
        conn.commit()
        return code, expires_at
    
    except Exception as e:
        print(f"Error creating verification code: {e}")
        conn.rollback()
        return None, None
    
    finally:
        conn.close()

def check_rate_limit(email, hours=1, max_codes=3):
    """Check if email has exceeded rate limit"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM email_verification_codes
            WHERE email = ? AND created_at > ?
        """, (email, since))
        
        row = cursor.fetchone()
        count = row['count'] if row else 0
        
        return count < max_codes
    
    finally:
        conn.close()

def email_exists(email):
    """Check if email exists in database"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users_email WHERE email = ?", (email,))
        return cursor.fetchone() is not None
    
    finally:
        conn.close()

def send_verification_email(email, ip_address=""):
    """Generate code and send verification email"""
    print(f"🔐 Testing authentication for: {email}")
    
    # Check rate limit
    if not check_rate_limit(email):
        print("❌ Rate limit exceeded")
        return False, None, None
    
    # Generate and store code
    code, expires_at = create_verification_code(email, ip_address)
    
    if not code:
        print("❌ Failed to generate code")
        return False, None, None
    
    # Send email via automated methods
    success = automated_email_service.send_verification_email(email, code, ip_address)
    
    if success:
        print(f"✅ Code sent successfully: {code}")
        print(f"🔗 Webhook URL: {automated_email_service.get_webhook_url()}")
        return True, code, expires_at
    else:
        print("❌ Failed to send email")
        return False, None, None

def verify_code(email, code):
    """Verify email verification code"""
    code_hash = hash_code(code)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, expires_at, used, attempts 
            FROM email_verification_codes
            WHERE email = ? AND code_hash = ? AND used = 0
            ORDER BY created_at DESC
            LIMIT 1
        """, (email, code_hash))
        
        row = cursor.fetchone()
        
        if not row:
            print("❌ Code not found")
            return False
        
        # Check expiration
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            print("❌ Code expired")
            return False
        
        # Check attempts
        if row['attempts'] >= 5:
            print("❌ Too many attempts")
            return False
        
        # Mark as used
        cursor.execute("""
            UPDATE email_verification_codes 
            SET used = 1
            WHERE id = ?
        """, (row['id'],))
        
        conn.commit()
        print("✅ Code verified successfully")
        return True
    
    except Exception as e:
        print(f"❌ Error verifying code: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 TESTING AUTHENTICATION FLOW")
    print("=" * 50)
    
    email = "brooketogo98@gmail.com"
    
    # Test 1: Check if email exists
    print(f"\n1. Checking if email exists: {email}")
    exists = email_exists(email)
    print(f"   Result: {'✅ Exists' if exists else '❌ Not found'}")
    
    # Test 2: Check rate limit
    print(f"\n2. Checking rate limit for: {email}")
    rate_ok = check_rate_limit(email)
    print(f"   Result: {'✅ Within limit' if rate_ok else '❌ Rate limited'}")
    
    # Test 3: Send verification email
    print(f"\n3. Sending verification email to: {email}")
    success, code, expires = send_verification_email(email, "127.0.0.1")
    
    if success:
        print(f"   ✅ Email sent successfully!")
        print(f"   📧 Code: {code}")
        print(f"   ⏰ Expires: {expires}")
        
        # Test 4: Verify the code
        print(f"\n4. Verifying code: {code}")
        verify_success = verify_code(email, code)
        print(f"   Result: {'✅ Verification successful' if verify_success else '❌ Verification failed'}")
    else:
        print("   ❌ Failed to send email")
    
    print("\n" + "=" * 50)
    print("🎯 AUTHENTICATION FLOW TEST COMPLETE")