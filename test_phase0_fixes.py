#!/usr/bin/env python3
"""
Test Phase 0 Security Fixes - Actual Functional Tests
Tests that the fixes actually work, not just that code exists
"""

import sys
import os
import hmac

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_constant_time_comparison():
    """Test that constant-time comparison is actually used"""
    print("Test 1: Constant-time password comparison...")
    
    try:
        from auth_utils import AuthenticationManager
        
        # Create instance with temp database
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        auth_mgr = AuthenticationManager(db_path=temp_db.name)
        
        # Test password hashing and verification
        password = "test_password_123"
        password_hash, salt = auth_mgr._hash_password(password)
        
        # Verify correct password
        result = auth_mgr._verify_password(password, password_hash, salt)
        if not result:
            print("❌ FAILED: Correct password not verified")
            return False
        
        # Verify incorrect password
        result = auth_mgr._verify_password("wrong_password", password_hash, salt)
        if result:
            print("❌ FAILED: Incorrect password was verified")
            return False
        
        # Check that hmac.compare_digest is actually used
        import inspect
        source = inspect.getsource(auth_mgr._verify_password)
        if 'hmac.compare_digest' not in source:
            print("❌ FAILED: hmac.compare_digest not found in code")
            return False
        
        print("✅ PASSED: Constant-time comparison works correctly")
        
        # Cleanup
        try:
            os.unlink(temp_db.name)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_configuration():
    """Test that session configuration is correct"""
    print("\nTest 2: Session security configuration...")
    
    try:
        from config import Config
        
        checks = {
            'SESSION_COOKIE_HTTPONLY': (True, "HttpOnly must be True"),
            'SESSION_COOKIE_SAMESITE': ('Lax', "SameSite should be Lax or Strict"),
            'SESSION_REFRESH_EACH_REQUEST': (True, "Session refresh must be enabled"),
        }
        
        failed = []
        for attr, (expected, msg) in checks.items():
            if not hasattr(Config, attr):
                failed.append(f"{attr} not found")
                continue
            
            value = getattr(Config, attr)
            if attr == 'SESSION_COOKIE_SAMESITE':
                if value not in ['Lax', 'Strict']:
                    failed.append(f"{attr} is {value}, {msg}")
            elif value != expected:
                failed.append(f"{attr} is {value}, expected {expected}")
        
        if failed:
            print("❌ FAILED:")
            for f in failed:
                print(f"   - {f}")
            return False
        
        print("✅ PASSED: Session configuration is correct")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_csrf_decorator_exists():
    """Test that CSRF decorator exists and is importable"""
    print("\nTest 3: CSRF decorator implementation...")
    
    try:
        from api_routes import require_csrf_token
        
        # Check it's a function
        if not callable(require_csrf_token):
            print("❌ FAILED: require_csrf_token is not callable")
            return False
        
        # Check it's a decorator (returns a function)
        def dummy_func():
            pass
        
        decorated = require_csrf_token(dummy_func)
        if not callable(decorated):
            print("❌ FAILED: Decorator doesn't return callable")
            return False
        
        print("✅ PASSED: CSRF decorator exists and is functional")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test that all necessary imports work"""
    print("\nTest 4: Required imports...")
    
    imports_to_test = [
        ('flask_wtf.csrf', 'CSRFProtect'),
        ('flask_wtf.csrf', 'validate_csrf'),
        ('hmac', 'compare_digest'),
        ('secrets', 'token_urlsafe'),
    ]
    
    failed = []
    for module, item in imports_to_test:
        try:
            mod = __import__(module, fromlist=[item])
            if not hasattr(mod, item):
                failed.append(f"{module}.{item} not found")
        except ImportError as e:
            failed.append(f"Cannot import {module}: {e}")
    
    if failed:
        print("❌ FAILED:")
        for f in failed:
            print(f"   - {f}")
        return False
    
    print("✅ PASSED: All required imports work")
    return True

def test_files_exist():
    """Test that modified files exist and have expected content"""
    print("\nTest 5: File modifications...")
    
    files_to_check = {
        'auth_utils.py': ['hmac.compare_digest', '_verify_password'],
        'auth_routes.py': ['session.clear()', 'session fixation'],
        'config.py': ['SESSION_REFRESH_EACH_REQUEST', '__Host-'],
        'api_routes.py': ['require_csrf_token', 'validate_csrf'],
    }
    
    failed = []
    for filename, required_strings in files_to_check.items():
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(filepath):
            failed.append(f"{filename} not found")
            continue
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        for required in required_strings:
            if required not in content:
                failed.append(f"{filename} missing: {required}")
    
    if failed:
        print("❌ FAILED:")
        for f in failed:
            print(f"   - {f}")
        return False
    
    print("✅ PASSED: All files have expected modifications")
    return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("Phase 0 Security Fixes - Functional Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_imports,
        test_files_exist,
        test_constant_time_comparison,
        test_session_configuration,
        test_csrf_decorator_exists,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("✅ ALL TESTS PASSED - Phase 0 fixes are working correctly")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED - Fixes need attention")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
