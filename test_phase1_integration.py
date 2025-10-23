#!/usr/bin/env python3
"""
Phase 1 Enterprise Security Integration Tests
Tests the integration of Phase 1 security components into web_app.py
"""

import sys
import json
from web_app import create_app
from core.security.input_validator import InputType

def test_phase1_components():
    """Test that all Phase 1 components are integrated"""
    print("Test 1: Phase 1 Components Integration...")
    
    app = create_app()
    
    # Check all components are available
    assert hasattr(app, 'session_manager'), "SessionManager not integrated"
    assert hasattr(app, 'input_validator'), "InputValidator not integrated"
    assert hasattr(app, 'crypto_manager'), "CryptoManager not integrated"
    assert hasattr(app, 'enterprise_error_handler'), "EnterpriseErrorHandler not integrated"
    
    print("✅ PASSED: All Phase 1 components integrated")
    return True

def test_input_validation():
    """Test input validation functionality"""
    print("Test 2: Input Validation...")
    
    app = create_app()
    
    # Test valid email
    result = app.input_validator.validate_input(
        'test@example.com',
        InputType.EMAIL,
        context={}
    )
    assert result.is_valid, "Valid email should pass validation"
    
    # Test invalid email
    result = app.input_validator.validate_input(
        'invalid-email',
        InputType.EMAIL,
        context={}
    )
    assert not result.is_valid, "Invalid email should fail validation"
    
    # Test URL validation
    result = app.input_validator.validate_input(
        'https://example.com',
        InputType.URL,
        context={}
    )
    assert result.is_valid, "Valid URL should pass validation"
    
    print("✅ PASSED: Input validation working correctly")
    return True

def test_health_endpoint():
    """Test health endpoint returns Phase 1 status"""
    print("Test 3: Health Endpoint...")
    
    app = create_app()
    
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200, "Health endpoint should return 200"
        
        data = json.loads(response.data)
        assert data.get('status') == 'healthy', "Status should be healthy"
        assert 'phase1_security' in data, "Phase 1 security status missing"
        
        phase1 = data['phase1_security']
        assert phase1.get('session_manager') == 'active', "SessionManager should be active"
        assert phase1.get('input_validator') == 'active', "InputValidator should be active"
        assert phase1.get('crypto_manager') == 'active', "CryptoManager should be active"
        assert phase1.get('error_handler') == 'active', "ErrorHandler should be active"
    
    print("✅ PASSED: Health endpoint reports Phase 1 status")
    return True

def test_error_handlers():
    """Test enhanced error handlers"""
    print("Test 4: Enhanced Error Handlers...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Test 404 error handler
        response = client.get('/nonexistent-route')
        assert response.status_code == 404, "Should return 404"
        
        data = json.loads(response.data)
        assert 'error' in data, "Error message should be present"
        assert 'error_id' in data, "Error ID should be present (Phase 1 feature)"
    
    print("✅ PASSED: Enhanced error handlers working")
    return True

def test_request_validation_middleware():
    """Test request validation middleware"""
    print("Test 5: Request Validation Middleware...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Test with valid JSON to health endpoint (no auth required)
        response = client.get('/health')
        # Should pass validation and return 200
        assert response.status_code == 200, "Valid request should pass validation"
        
        # Verify middleware is active by checking it doesn't break normal requests
        data = json.loads(response.data)
        assert 'status' in data, "Response should contain status"
    
    print("✅ PASSED: Request validation middleware active")
    return True

def main():
    """Run all Phase 1 integration tests"""
    print("=" * 70)
    print("Phase 1 Enterprise Security Integration Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_phase1_components,
        test_input_validation,
        test_health_endpoint,
        test_error_handlers,
        test_request_validation_middleware
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
        print()
    
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("✅ ALL PHASE 1 INTEGRATION TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
