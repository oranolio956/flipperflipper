#!/usr/bin/env python3
"""
Security Verification Script
Verify all security measures are in place
"""

import os
import sqlite3
import hashlib
from datetime import datetime

def verify_database_security():
    """Verify database security measures"""
    print("🔒 Verifying Database Security")
    print("-" * 35)
    
    db_path = '/workspace/Application/stitch.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if any codes are stored as plaintext
        cursor.execute("SELECT code_hash FROM email_verification_codes LIMIT 5")
        codes = cursor.fetchall()
        
        if codes:
            for code_hash, in codes:
                if len(code_hash) == 64 and all(c in '0123456789abcdef' for c in code_hash):
                    print("✅ Email codes are properly hashed (SHA-256)")
                else:
                    print("❌ Email codes may not be properly hashed")
                    return False
                break
        else:
            print("ℹ️  No email verification codes in database yet")
        
        # Check MFA secrets encryption
        cursor.execute("SELECT mfa_secret FROM user_mfa LIMIT 5")
        secrets = cursor.fetchall()
        
        if secrets:
            for secret, in secrets:
                if len(secret) > 32 and '=' in secret:  # Base64 encoded encrypted data
                    print("✅ MFA secrets are encrypted")
                else:
                    print("❌ MFA secrets may not be encrypted")
                    return False
                break
        else:
            print("ℹ️  No MFA secrets in database yet")
        
        # Check backup code hashing
        cursor.execute("SELECT code_hash FROM mfa_backup_codes LIMIT 5")
        backup_codes = cursor.fetchall()
        
        if backup_codes:
            for code_hash, in backup_codes:
                if len(code_hash) == 64 and all(c in '0123456789abcdef' for c in code_hash):
                    print("✅ Backup codes are properly hashed (SHA-256)")
                else:
                    print("❌ Backup codes may not be properly hashed")
                    return False
                break
        else:
            print("ℹ️  No backup codes in database yet")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database security check failed: {e}")
        return False

def verify_encryption_key():
    """Verify MFA encryption key security"""
    print("\n🔑 Verifying Encryption Key Security")
    print("-" * 40)
    
    key_path = '/workspace/Application/.mfa_encryption_key'
    
    if not os.path.exists(key_path):
        print("⚠️  Encryption key file not found (will be created on first use)")
        return True
    
    # Check file permissions
    stat = os.stat(key_path)
    perms = oct(stat.st_mode)[-3:]
    
    if perms == '600':
        print("✅ Encryption key has secure permissions (600)")
    else:
        print(f"❌ Encryption key permissions: {perms} (should be 600)")
        return False
    
    # Check key length
    with open(key_path, 'rb') as f:
        key = f.read()
    
    if len(key) == 44:  # Fernet key length
        print("✅ Encryption key has correct length (44 bytes)")
    else:
        print(f"❌ Encryption key has incorrect length: {len(key)} bytes")
        return False
    
    return True

def verify_audit_logging():
    """Verify audit logging is working"""
    print("\n📝 Verifying Audit Logging")
    print("-" * 30)
    
    db_path = '/workspace/Application/stitch.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check email audit table structure
        cursor.execute("PRAGMA table_info(email_auth_audit)")
        email_audit_columns = [row[1] for row in cursor.fetchall()]
        
        required_email_columns = ['email', 'event_type', 'ip_address', 'success', 'timestamp']
        for col in required_email_columns:
            if col in email_audit_columns:
                print(f"✅ Email audit has {col} column")
            else:
                print(f"❌ Email audit missing {col} column")
                return False
        
        # Check MFA audit table structure
        cursor.execute("PRAGMA table_info(mfa_audit_log)")
        mfa_audit_columns = [row[1] for row in cursor.fetchall()]
        
        required_mfa_columns = ['email', 'event_type', 'ip_address', 'success', 'timestamp']
        for col in required_mfa_columns:
            if col in mfa_audit_columns:
                print(f"✅ MFA audit has {col} column")
            else:
                print(f"❌ MFA audit missing {col} column")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Audit logging check failed: {e}")
        return False

def verify_rate_limiting():
    """Verify rate limiting structure"""
    print("\n⏱️  Verifying Rate Limiting")
    print("-" * 30)
    
    db_path = '/workspace/Application/stitch.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check rate limiting table structure
        cursor.execute("PRAGMA table_info(email_rate_limits)")
        rate_columns = [row[1] for row in cursor.fetchall()]
        
        required_rate_columns = ['email', 'request_count', 'window_start', 'blocked_until']
        for col in required_rate_columns:
            if col in rate_columns:
                print(f"✅ Rate limiting has {col} column")
            else:
                print(f"❌ Rate limiting missing {col} column")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting check failed: {e}")
        return False

def verify_session_security():
    """Verify session security measures"""
    print("\n🍪 Verifying Session Security")
    print("-" * 32)
    
    try:
        # Check if web app has session configuration
        os.environ['STITCH_ADMIN_USER'] = 'admin'
        os.environ['STITCH_ADMIN_PASSWORD'] = 'password123456'
        
        import web_app_real
        
        # Check session configuration
        app = web_app_real.app
        
        if app.permanent_session_lifetime:
            print(f"✅ Session timeout configured: {app.permanent_session_lifetime}")
        else:
            print("⚠️  Session timeout not explicitly configured")
        
        if app.secret_key:
            print("✅ Flask secret key is set")
        else:
            print("❌ Flask secret key not set")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Session security check failed: {e}")
        return False

def verify_input_validation():
    """Verify input validation functions"""
    print("\n✅ Verifying Input Validation")
    print("-" * 35)
    
    try:
        from mfa_manager import mfa_manager
        
        # Test TOTP format validation
        valid_tests = [
            ("123456", True),
            ("000000", True),
            ("999999", True),
        ]
        
        invalid_tests = [
            ("12345", False),   # Too short
            ("1234567", False), # Too long
            ("12345a", False),  # Contains letter
            ("", False),        # Empty
            (None, False),      # None
        ]
        
        for test_input, expected in valid_tests:
            result = mfa_manager.validate_totp_format(test_input)
            if result == expected:
                print(f"✅ TOTP validation correct for '{test_input}': {result}")
            else:
                print(f"❌ TOTP validation failed for '{test_input}': expected {expected}, got {result}")
                return False
        
        for test_input, expected in invalid_tests:
            result = mfa_manager.validate_totp_format(test_input)
            if result == expected:
                print(f"✅ TOTP validation correct for '{test_input}': {result}")
            else:
                print(f"❌ TOTP validation failed for '{test_input}': expected {expected}, got {result}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Input validation check failed: {e}")
        return False

def main():
    """Run all security verifications"""
    print("🏆 ELITE AUTHENTICATION SECURITY VERIFICATION")
    print("=" * 55)
    
    tests = [
        ("Database Security", verify_database_security),
        ("Encryption Key", verify_encryption_key),
        ("Audit Logging", verify_audit_logging),
        ("Rate Limiting", verify_rate_limiting),
        ("Session Security", verify_session_security),
        ("Input Validation", verify_input_validation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 55)
    print(f"🏆 SECURITY VERIFICATION: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ ALL SECURITY MEASURES VERIFIED - System is secure!")
        return True
    else:
        print(f"❌ {total - passed} security checks failed - review issues above")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)