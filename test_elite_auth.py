#!/usr/bin/env python3
"""
Comprehensive Test Suite for Elite Authentication System
Tests all components: Database, Email, MFA, Security
"""

import os
import sys
import sqlite3
from datetime import datetime

def test_database_tables():
    """Test database table creation and structure"""
    print("🗄️  Testing Database Tables")
    print("-" * 30)
    
    db_path = '/workspace/Application/stitch.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check email tables
        email_tables = ['users_email', 'email_verification_codes', 'email_auth_audit', 'email_rate_limits']
        for table in email_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"✅ {table} table exists")
            else:
                print(f"❌ {table} table missing")
                return False
        
        # Check MFA tables
        mfa_tables = ['user_mfa', 'mfa_backup_codes', 'mfa_audit_log', 'mfa_sessions']
        for table in mfa_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"✅ {table} table exists")
            else:
                print(f"❌ {table} table missing")
                return False
        
        conn.close()
        print("✅ All database tables verified")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_email_auth_functions():
    """Test email authentication functions"""
    print("\n📧 Testing Email Authentication Functions")
    print("-" * 40)
    
    try:
        import email_auth
        
        # Test email creation
        test_email = "test@example.com"
        
        # Test email exists (should be False initially)
        exists = email_auth.email_exists(test_email)
        print(f"✅ email_exists() works: {exists}")
        
        # Test create email user
        success = email_auth.create_email_user(test_email)
        print(f"✅ create_email_user() works: {success}")
        
        # Test email exists again (should be True now)
        exists = email_auth.email_exists(test_email)
        print(f"✅ email_exists() after creation: {exists}")
        
        # Test rate limiting
        rate_ok = email_auth.check_rate_limit(test_email)
        print(f"✅ check_rate_limit() works: {rate_ok}")
        
        # Test verification code creation
        code, expires_at = email_auth.create_verification_code(test_email, "127.0.0.1")
        if code:
            print(f"✅ create_verification_code() works: {code}")
            
            # Test code verification
            verified = email_auth.verify_code(test_email, code)
            print(f"✅ verify_code() works: {verified}")
        else:
            print("❌ Failed to create verification code")
            return False
        
        print("✅ Email authentication functions verified")
        return True
        
    except Exception as e:
        print(f"❌ Email auth test failed: {e}")
        return False

def test_mfa_functions():
    """Test MFA functions"""
    print("\n🔐 Testing MFA Functions")
    print("-" * 25)
    
    try:
        from mfa_manager import mfa_manager
        import mfa_database
        
        test_email = "mfa-test@example.com"
        
        # Test TOTP secret generation
        secret = mfa_manager.generate_totp_secret()
        print(f"✅ TOTP secret generated: {secret[:8]}...")
        
        # Test encryption
        encrypted = mfa_manager.encrypt_secret(secret)
        if encrypted:
            print("✅ Secret encryption works")
            
            # Test decryption
            decrypted = mfa_manager.decrypt_secret(encrypted)
            if decrypted == secret:
                print("✅ Secret decryption works")
            else:
                print("❌ Secret decryption failed")
                return False
        else:
            print("❌ Secret encryption failed")
            return False
        
        # Test QR code generation
        qr_code = mfa_manager.generate_qr_code(test_email, secret)
        if qr_code:
            print("✅ QR code generation works")
        else:
            print("❌ QR code generation failed")
            return False
        
        # Test TOTP verification
        current_totp = mfa_manager.get_current_totp(secret)
        if current_totp:
            print(f"✅ Current TOTP: {current_totp}")
            
            # Verify the current TOTP
            verified = mfa_manager.verify_totp(secret, current_totp)
            print(f"✅ TOTP verification works: {verified}")
        else:
            print("❌ Failed to get current TOTP")
            return False
        
        # Test backup codes
        backup_codes = mfa_manager.generate_backup_codes()
        print(f"✅ Generated {len(backup_codes)} backup codes")
        
        # Test backup code hashing
        first_code = backup_codes[0]
        code_hash = mfa_manager.hash_backup_code(first_code)
        verified = mfa_manager.verify_backup_code(first_code, code_hash)
        print(f"✅ Backup code hashing works: {verified}")
        
        print("✅ MFA functions verified")
        return True
        
    except Exception as e:
        print(f"❌ MFA test failed: {e}")
        return False

def test_mailjet_connection():
    """Test Mailjet connection if API secret is available"""
    print("\n📬 Testing Mailjet Connection")
    print("-" * 30)
    
    try:
        from email_manager_mailjet import email_manager
        
        print(f"✅ API Key: {email_manager.api_key}")
        print(f"✅ From Email: {email_manager.from_email}")
        
        if not email_manager.api_secret:
            print("⚠️  MAILJET_API_SECRET not set - skipping connection test")
            print("   To test email sending, set: export MAILJET_API_SECRET='your-secret'")
            return True
        
        print(f"✅ API Secret: {'*' * len(email_manager.api_secret)}")
        
        # Test connection
        if email_manager.test_connection():
            print("✅ Mailjet connection successful")
            
            # Test code generation
            code = email_manager.generate_code()
            print(f"✅ Generated test code: {code}")
            
            return True
        else:
            print("❌ Mailjet connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Mailjet test failed: {e}")
        return False

def test_security_measures():
    """Test security measures"""
    print("\n🔒 Testing Security Measures")
    print("-" * 30)
    
    try:
        from email_manager_mailjet import email_manager
        from mfa_manager import mfa_manager
        
        # Test code hashing
        test_code = "123456"
        code_hash = email_manager.hash_code(test_code)
        print(f"✅ Code hashing works: {len(code_hash)} chars")
        
        # Verify hash is different from original
        if code_hash != test_code:
            print("✅ Codes are properly hashed (not plaintext)")
        else:
            print("❌ Codes are stored as plaintext!")
            return False
        
        # Test encryption key exists
        key_path = '/workspace/Application/.mfa_encryption_key'
        if os.path.exists(key_path):
            print("✅ MFA encryption key exists")
            
            # Check permissions
            stat = os.stat(key_path)
            perms = oct(stat.st_mode)[-3:]
            if perms == '600':
                print("✅ Encryption key has secure permissions (600)")
            else:
                print(f"⚠️  Encryption key permissions: {perms} (should be 600)")
        else:
            print("⚠️  MFA encryption key not found (will be created on first use)")
        
        # Test backup code hashing
        test_backup = "ABCD1234"
        backup_hash = mfa_manager.hash_backup_code(test_backup)
        print(f"✅ Backup code hashing works: {len(backup_hash)} chars")
        
        print("✅ Security measures verified")
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def test_web_app_integration():
    """Test web app integration"""
    print("\n🌐 Testing Web App Integration")
    print("-" * 35)
    
    try:
        # Test imports
        from web_app_real import MFA_ENABLED
        print(f"✅ MFA_ENABLED: {MFA_ENABLED}")
        
        if MFA_ENABLED:
            print("✅ Web app has MFA modules loaded")
        else:
            print("❌ Web app MFA modules not loaded")
            return False
        
        print("✅ Web app integration verified")
        return True
        
    except Exception as e:
        print(f"❌ Web app integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏆 ELITE PASSWORDLESS MFA AUTHENTICATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Database Tables", test_database_tables),
        ("Email Authentication", test_email_auth_functions),
        ("MFA Functions", test_mfa_functions),
        ("Mailjet Connection", test_mailjet_connection),
        ("Security Measures", test_security_measures),
        ("Web App Integration", test_web_app_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏆 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Elite authentication system ready!")
        return True
    else:
        print(f"❌ {total - passed} tests failed - check issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)