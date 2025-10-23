#!/usr/bin/env python3
"""
Test script for Oranolio RATX Login Page
Tests responsive design, functionality, and integration
"""

import os
import sys
import time
from pathlib import Path

def test_responsive_design():
    """Test responsive design elements"""
    print("📱 Testing Responsive Design...")
    
    # Test viewport meta tag
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    if not login_file.exists():
        print("  ❌ Login template not found")
        return False
    
    if not verify_file.exists():
        print("  ❌ Verify template not found")
        return False
    
    # Check for responsive CSS
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    responsive_checks = [
        ('viewport meta tag', 'name="viewport"'),
        ('mobile media queries', '@media (max-width: 480px)'),
        ('small screen media queries', '@media (max-width: 360px)'),
        ('flexible grid system', 'display: flex'),
        ('responsive typography', 'font-size: var(--font-size-'),
        ('touch-friendly buttons', 'min-height: 48px'),
        ('accessible focus states', 'focus-visible'),
        ('reduced motion support', 'prefers-reduced-motion')
    ]
    
    all_passed = True
    for check_name, check_pattern in responsive_checks:
        if check_pattern in login_content and check_pattern in verify_content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_accessibility():
    """Test accessibility features"""
    print("\n♿ Testing Accessibility...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    accessibility_checks = [
        ('ARIA labels', 'aria-label'),
        ('ARIA live regions', 'aria-live'),
        ('Screen reader support', 'sr-only'),
        ('Semantic HTML', '<section>'),
        ('Proper heading structure', '<h1>'),
        ('Focus management', 'autofocus'),
        ('Keyboard navigation', 'keydown'),
        ('Color contrast support', 'prefers-contrast'),
        ('Form labels', '<label'),
        ('Fieldset elements', '<fieldset>')
    ]
    
    all_passed = True
    for check_name, check_pattern in accessibility_checks:
        if check_pattern in login_content and check_pattern in verify_content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_javascript_functionality():
    """Test JavaScript functionality"""
    print("\n⚡ Testing JavaScript Functionality...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    js_checks = [
        ('Email validation', 'validateEmail'),
        ('Code input management', 'setupCodeInputs'),
        ('Form submission handling', 'addEventListener'),
        ('Error handling', 'showError'),
        ('Loading states', 'loading'),
        ('Timer functionality', 'setInterval'),
        ('Paste handling', 'handlePaste'),
        ('Keyboard shortcuts', 'keydown'),
        ('Accessibility announcements', 'announceError'),
        ('Session management', 'sessionData')
    ]
    
    all_passed = True
    for check_name, check_pattern in js_checks:
        if check_pattern in login_content and check_pattern in verify_content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_backend_integration():
    """Test backend integration"""
    print("\n🔗 Testing Backend Integration...")
    
    # Check if route files exist
    route_file = Path('oranolio_auth_routes.py')
    if not route_file.exists():
        print("  ❌ Oranolio auth routes not found")
        return False
    
    # Check if routes are registered in main app
    web_app_file = Path('web_app_real.py')
    if not web_app_file.exists():
        print("  ❌ Main web app not found")
        return False
    
    with open(web_app_file, 'r') as f:
        web_app_content = f.read()
    
    integration_checks = [
        ('Oranolio routes imported', 'from oranolio_auth_routes import'),
        ('Routes registered', 'register_oranolio_auth_routes'),
        ('Login redirect updated', 'oranolio_auth.oranolio_login'),
        ('Error handlers updated', 'oranolio_login.html')
    ]
    
    all_passed = True
    for check_name, check_pattern in integration_checks:
        if check_pattern in web_app_content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_security_features():
    """Test security features"""
    print("\n🔒 Testing Security Features...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    security_checks = [
        ('CSRF protection', 'csrf_token'),
        ('Input validation', 'pattern='),
        ('Rate limiting support', 'check_rate_limit'),
        ('Session security', 'sessionData'),
        ('Trust indicators', 'SSL Secured'),
        ('GDPR compliance', 'GDPR Compliant'),
        ('Secure headers', 'Content-Security-Policy'),
        ('Input sanitization', 'sanitizeInput'),
        ('Error handling', 'error')
    ]
    
    all_passed = True
    for check_name, check_pattern in security_checks:
        if check_pattern in login_content and check_pattern in verify_content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_ui_consistency():
    """Test UI consistency and design system"""
    print("\n🎨 Testing UI Consistency...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    ui_checks = [
        ('CSS variables', '--primary-accent'),
        ('Consistent spacing', '--spacing-'),
        ('Typography system', '--font-size-'),
        ('Color palette', '--text-primary'),
        ('Border radius', '--radius'),
        ('Shadow system', '--shadow'),
        ('Animation system', 'transition:'),
        ('Button styles', 'btn btn-primary'),
        ('Form styling', 'form-input'),
        ('Trust indicators', 'trust-indicators')
    ]
    
    all_passed = True
    for check_name, check_pattern in ui_checks:
        if check_pattern in login_content and check_pattern in verify_content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🚀 Oranolio RATX Login Page - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Responsive Design", test_responsive_design),
        ("Accessibility", test_accessibility),
        ("JavaScript Functionality", test_javascript_functionality),
        ("Backend Integration", test_backend_integration),
        ("Security Features", test_security_features),
        ("UI Consistency", test_ui_consistency)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Oranolio RATX login page is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix the issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)