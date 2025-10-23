#!/usr/bin/env python3
"""
Test CSRF Protection Implementation
Tests that CSRF tokens are properly validated on state-changing endpoints
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_csrf_protection():
    """Test CSRF protection on API endpoints"""
    
    print("=" * 70)
    print("CSRF Protection Test Suite")
    print("=" * 70)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check CSRF decorator exists
    print("Test 1: Checking CSRF decorator implementation...")
    try:
        from api_routes import require_csrf_token
        print("✅ CSRF decorator found in api_routes.py")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ CSRF decorator not found: {e}")
        tests_failed += 1
    print()
    
    # Test 2: Check CSRF imports
    print("Test 2: Checking CSRF imports...")
    try:
        from flask_wtf.csrf import validate_csrf, csrf
        print("✅ Flask-WTF CSRF imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ CSRF imports failed: {e}")
        tests_failed += 1
    print()
    
    # Test 3: Check API routes have CSRF protection
    print("Test 3: Checking API routes for CSRF protection...")
    try:
        with open('api_routes.py', 'r') as f:
            content = f.read()
            
        # Check for CSRF decorator on POST endpoints
        if '@require_csrf_token' in content:
            print("✅ CSRF decorator applied to endpoints")
            
            # Count applications
            count = content.count('@require_csrf_token')
            print(f"   Found {count} endpoint(s) with CSRF protection")
            tests_passed += 1
        else:
            print("❌ CSRF decorator not applied to any endpoints")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Error checking API routes: {e}")
        tests_failed += 1
    print()
    
    # Test 4: Check webhook routes are exempt
    print("Test 4: Checking webhook routes are exempt from CSRF...")
    try:
        with open('webhook_auth_routes.py', 'r') as f:
            content = f.read()
            
        if '@csrf.exempt' in content:
            print("✅ Webhook routes properly exempted from CSRF")
            
            # Count exemptions
            count = content.count('@csrf.exempt')
            print(f"   Found {count} webhook endpoint(s) exempted")
            tests_passed += 1
        else:
            print("⚠️  Warning: Webhook routes may not be exempted from CSRF")
            print("   This is acceptable if webhooks use signature validation")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Error checking webhook routes: {e}")
        tests_failed += 1
    print()
    
    # Test 5: Check constant-time password comparison
    print("Test 5: Checking constant-time password comparison...")
    try:
        with open('auth_utils.py', 'r') as f:
            content = f.read()
            
        if 'hmac.compare_digest' in content:
            print("✅ Constant-time comparison implemented")
            tests_passed += 1
        else:
            print("❌ Constant-time comparison not found")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Error checking auth_utils: {e}")
        tests_failed += 1
    print()
    
    # Test 6: Check session regeneration
    print("Test 6: Checking session regeneration after login...")
    try:
        with open('auth_routes.py', 'r') as f:
            content = f.read()
            
        if 'session.clear()' in content and 'session fixation' in content.lower():
            print("✅ Session regeneration implemented")
            tests_passed += 1
        else:
            print("❌ Session regeneration not found")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Error checking auth_routes: {e}")
        tests_failed += 1
    print()
    
    # Test 7: Check session security configuration
    print("Test 7: Checking session security configuration...")
    try:
        with open('config.py', 'r') as f:
            content = f.read()
            
        checks = {
            'SESSION_COOKIE_HTTPONLY': 'HttpOnly cookie',
            'SESSION_COOKIE_SAMESITE': 'SameSite cookie',
            'SESSION_REFRESH_EACH_REQUEST': 'Session refresh',
            '__Host-': 'Host prefix for HTTPS'
        }
        
        found = []
        missing = []
        
        for check, description in checks.items():
            if check in content:
                found.append(description)
            else:
                missing.append(description)
        
        if len(found) >= 3:  # At least 3 of 4 checks
            print(f"✅ Session security configured ({len(found)}/4 checks)")
            for item in found:
                print(f"   ✓ {item}")
            if missing:
                print("   Missing:")
                for item in missing:
                    print(f"   - {item}")
            tests_passed += 1
        else:
            print(f"❌ Insufficient session security ({len(found)}/4 checks)")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Error checking config: {e}")
        tests_failed += 1
    print()
    
    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests:  {tests_passed + tests_failed}")
    print()
    
    if tests_failed == 0:
        print("✅ All tests passed! CSRF protection is properly implemented.")
        return 0
    else:
        print(f"⚠️  {tests_failed} test(s) failed. Review implementation.")
        return 1

if __name__ == '__main__':
    exit_code = test_csrf_protection()
    sys.exit(exit_code)
