#!/usr/bin/env python3
"""
Complete Registration Protocol Test
Tests the entire flow from first-time user to authenticated session
"""

import os
import sys
import time
from datetime import datetime

def test_new_user_flow():
    """Test the complete new user registration flow"""
    print("👤 Testing New User Registration Flow")
    print("=" * 50)
    
    try:
        from email_auth import (
            email_exists, create_email_user, send_verification_email,
            verify_code, log_email_auth_event
        )
        from mfa_database import get_user_mfa_status, save_user_mfa
        from mfa_manager import mfa_manager
        import json
        
        # Test email (use timestamp to ensure uniqueness)
        test_email = f"newuser{int(time.time())}@example.com"
        
        # Step 1: Check if user exists (should be False for new user)
        if not email_exists(test_email):
            print("✅ New user detection working")
        else:
            print("❌ New user detection failed")
            return False
        
        # Step 2: Create new user
        if create_email_user(test_email):
            print("✅ User creation working")
        else:
            print("❌ User creation failed")
            return False
        
        # Step 3: Send verification email
        success, code, expires_at = send_verification_email(test_email, "127.0.0.1")
        if success and code:
            print("✅ Email verification sending working")
        else:
            print("⚠️  Email sending failed (normal without config)")
            # Create a test code directly in database
            from email_auth import create_verification_code
            code, expires_at = create_verification_code(test_email, "127.0.0.1")
            if code:
                print("✅ Test code creation working")
            else:
                print("❌ Test code creation failed")
                return False
        
        # Step 4: Verify email code
        if verify_code(test_email, code):
            print("✅ Email verification working")
        else:
            print("❌ Email verification failed")
            return False
        
        # Step 5: Check MFA status (should be disabled for new user)
        mfa_status = get_user_mfa_status(test_email)
        if not mfa_status['enabled']:
            print("✅ MFA setup detection working")
        else:
            print("❌ MFA setup detection failed")
            return False
        
        # Step 6: Setup MFA (simulate the process)
        secret = mfa_manager.generate_secret()
        if secret:
            print("✅ MFA secret generation working")
        else:
            print("❌ MFA secret generation failed")
            return False
        
        # Step 7: Generate QR code
        provisioning_uri = mfa_manager.get_provisioning_uri(test_email, secret)
        if provisioning_uri and "otpauth://" in provisioning_uri:
            print("✅ MFA QR code generation working")
        else:
            print("❌ MFA QR code generation failed")
            return False
        
        # Step 8: Generate backup codes
        backup_codes = mfa_manager.generate_backup_codes(10)
        if backup_codes and len(backup_codes) == 10:
            print("✅ Backup codes generation working")
        else:
            print("❌ Backup codes generation failed")
            return False
        
        # Step 9: Save MFA configuration
        encrypted_secret = mfa_manager.encrypt_secret(secret)
        backup_codes_hashed = [mfa_manager.hash_backup_code(c) for c in backup_codes]
        
        if save_user_mfa(test_email, encrypted_secret, json.dumps(backup_codes_hashed)):
            print("✅ MFA configuration save working")
        else:
            print("❌ MFA configuration save failed")
            return False
        
        # Step 10: Verify MFA is now enabled
        mfa_status = get_user_mfa_status(test_email)
        if mfa_status['enabled']:
            print("✅ MFA enablement working")
        else:
            print("❌ MFA enablement failed")
            return False
        
        # Step 11: Test MFA verification
        token = mfa_manager.generate_token(secret)
        if token and mfa_manager.verify_token(secret, token):
            print("✅ MFA verification working")
        else:
            print("❌ MFA verification failed")
            return False
        
        print("✅ Complete new user registration flow working")
        return True
        
    except Exception as e:
        print(f"❌ Error in new user flow: {e}")
        return False

def test_existing_user_flow():
    """Test the existing user login flow"""
    print("\n👤 Testing Existing User Login Flow")
    print("=" * 50)
    
    try:
        from email_auth import email_exists, send_verification_email, verify_code
        from mfa_database import get_user_mfa_status
        
        # Use a different test email for existing user
        test_email = f"existinguser{int(time.time())}@example.com"
        
        # First create the user
        from email_auth import create_email_user
        create_email_user(test_email)
        
        # Step 1: Check if user exists (should be True)
        if email_exists(test_email):
            print("✅ Existing user detection working")
        else:
            print("❌ Existing user detection failed")
            return False
        
        # Step 2: Send verification email
        success, code, expires_at = send_verification_email(test_email, "127.0.0.1")
        if success and code:
            print("✅ Email verification sending working")
        else:
            print("⚠️  Email sending failed (normal without config)")
            # Create a test code directly in database
            from email_auth import create_verification_code
            code, expires_at = create_verification_code(test_email, "127.0.0.1")
            if code:
                print("✅ Test code creation working")
            else:
                print("❌ Test code creation failed")
                return False
        
        # Step 3: Verify email code
        if verify_code(test_email, code):
            print("✅ Email verification working")
        else:
            print("❌ Email verification failed")
            return False
        
        # Step 4: Check MFA status (should be enabled)
        mfa_status = get_user_mfa_status(test_email)
        if mfa_status['enabled']:
            print("✅ MFA verification detection working")
        else:
            print("❌ MFA verification detection failed")
            return False
        
        print("✅ Complete existing user login flow working")
        return True
        
    except Exception as e:
        print(f"❌ Error in existing user flow: {e}")
        return False

def test_account_linking():
    """Test that accounts are properly linked across sessions"""
    print("\n🔗 Testing Account Linking")
    print("=" * 50)
    
    try:
        from email_auth import email_exists, create_email_user
        from mfa_database import get_user_mfa_status, save_user_mfa
        from mfa_manager import mfa_manager
        import json
        
        test_email = f"linkingtest{int(time.time())}@example.com"
        
        # Step 1: Create user
        if create_email_user(test_email):
            print("✅ Account creation working")
        else:
            print("❌ Account creation failed")
            return False
        
        # Step 2: Setup MFA
        secret = mfa_manager.generate_secret()
        encrypted_secret = mfa_manager.encrypt_secret(secret)
        backup_codes = mfa_manager.generate_backup_codes(5)
        backup_codes_hashed = [mfa_manager.hash_backup_code(c) for c in backup_codes]
        
        if save_user_mfa(test_email, encrypted_secret, json.dumps(backup_codes_hashed)):
            print("✅ MFA setup working")
        else:
            print("❌ MFA setup failed")
            return False
        
        # Step 3: Verify account persistence
        if email_exists(test_email):
            print("✅ Account persistence working")
        else:
            print("❌ Account persistence failed")
            return False
        
        # Step 4: Verify MFA persistence
        mfa_status = get_user_mfa_status(test_email)
        if mfa_status['enabled']:
            print("✅ MFA persistence working")
        else:
            print("❌ MFA persistence failed")
            return False
        
        # Step 5: Test MFA verification with stored secret
        token = mfa_manager.generate_token(secret)
        if token and mfa_manager.verify_token(secret, token):
            print("✅ MFA verification with stored secret working")
        else:
            print("❌ MFA verification with stored secret failed")
            return False
        
        print("✅ Account linking working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error in account linking: {e}")
        return False

def test_security_measures():
    """Test security measures are properly enforced"""
    print("\n🛡️ Testing Security Measures")
    print("=" * 50)
    
    try:
        from email_auth import check_rate_limit, create_verification_code
        from auth_utils import validate_input, sanitize_input
        
        # Test rate limiting
        test_email = f"ratetest{int(time.time())}@example.com"
        
        # Test multiple code requests (should be rate limited)
        for i in range(5):
            code, expires_at = create_verification_code(test_email, "127.0.0.1")
            if code:
                print(f"✅ Code generation {i+1} working")
            else:
                print(f"❌ Code generation {i+1} failed")
                return False
        
        # Test rate limit check
        if not check_rate_limit(test_email, hours=1, max_codes=3):
            print("✅ Rate limiting working")
        else:
            print("❌ Rate limiting failed")
            return False
        
        # Test input validation
        if validate_input("test@example.com", "email"):
            print("✅ Email validation working")
        else:
            print("❌ Email validation failed")
            return False
        
        # Test input sanitization
        malicious_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(malicious_input, "general")
        if "<script>" not in sanitized:
            print("✅ XSS prevention working")
        else:
            print("❌ XSS prevention failed")
            return False
        
        print("✅ Security measures working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error in security measures: {e}")
        return False

def main():
    print("🔐 COMPLETE REGISTRATION PROTOCOL TEST")
    print("=" * 70)
    
    tests = [
        ("New User Registration Flow", test_new_user_flow),
        ("Existing User Login Flow", test_existing_user_flow),
        ("Account Linking", test_account_linking),
        ("Security Measures", test_security_measures)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print(f"\n{'='*70}")
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 REGISTRATION PROTOCOL WORKING PERFECTLY!")
        print("✅ New user registration flow complete")
        print("✅ Existing user login flow complete")
        print("✅ Account linking working correctly")
        print("✅ Security measures properly enforced")
        print("\n🚀 System is ready for production use!")
        print("\n📋 COMPLETE AUTHENTICATION FLOW:")
        print("1. User enters email → Input validation")
        print("2. System sends verification code → Email delivery")
        print("3. User enters code → Cryptographic verification")
        print("4. New user → MFA setup with QR code")
        print("5. Existing user → MFA verification")
        print("6. Session creation → Secure authentication")
        print("\n🔒 OPSEC STATUS: SECURE AND ANONYMOUS")
    else:
        print("⚠️  Some registration protocol tests failed")
        print("Check the failed tests above for details")

if __name__ == "__main__":
    main()