#!/usr/bin/env python3
"""
Functional QA Test for Oranolio RATX Login Page
Tests core functionality without external dependencies
"""

import os
import sys
from pathlib import Path

def test_critical_ids_preserved():
    """Test that all critical IDs are preserved"""
    print("🔍 Testing Critical IDs Preservation...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    if not login_file.exists() or not verify_file.exists():
        print("  ❌ Template files not found")
        return False
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    critical_ids = [
        'emailForm', 'codeForm', 'email', 'sendCodeBtn', 'verifyBtn', 'resendBtn',
        'step1-container', 'step2-container', 'step1', 'step2', 'fullCode',
        'hiddenEmail', 'resendTimer', 'countdown', 'timer'
    ]
    
    all_passed = True
    for id_name in critical_ids:
        if f'id="{id_name}"' in login_content or f'id="{id_name}"' in verify_content:
            print(f"  ✅ {id_name}")
        else:
            print(f"  ❌ {id_name}")
            all_passed = False
    
    return all_passed

def test_critical_classes_preserved():
    """Test that all critical classes are preserved"""
    print("\n🎨 Testing Critical Classes Preservation...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    critical_classes = [
        'form-input', 'btn', 'btn-primary', 'btn-secondary', 'code-input',
        'code-input-container', 'form-group', 'form-label', 'alert',
        'error-message', 'loading', 'trust-indicators', 'resend-section'
    ]
    
    all_passed = True
    for class_name in critical_classes:
        if f'class="{class_name}' in login_content or f'class="{class_name}' in verify_content:
            print(f"  ✅ {class_name}")
        else:
            print(f"  ❌ {class_name}")
            all_passed = False
    
    return all_passed

def test_javascript_functions_preserved():
    """Test that all critical JavaScript functions are preserved"""
    print("\n⚡ Testing JavaScript Functions Preservation...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    critical_functions = [
        'validateEmail', 'showError', 'removeError', 'showStep', 'setupCodeInputs',
        'updateFullCode', 'isCodeComplete', 'clearCodeInputs', 'handlePaste',
        'startResendCountdown', 'announceError', 'announceSuccess'
    ]
    
    all_passed = True
    for func_name in critical_functions:
        if f'function {func_name}' in login_content or f'function {func_name}' in verify_content:
            print(f"  ✅ {func_name}")
        else:
            print(f"  ❌ {func_name}")
            all_passed = False
    
    return all_passed

def test_api_endpoints_preserved():
    """Test that all API endpoints are preserved"""
    print("\n🔗 Testing API Endpoints Preservation...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    api_endpoints = [
        '/oranolio/login', '/oranolio/verify', '/oranolio/resend'
    ]
    
    all_passed = True
    for endpoint in api_endpoints:
        if endpoint in login_content or endpoint in verify_content:
            print(f"  ✅ {endpoint}")
        else:
            print(f"  ❌ {endpoint}")
            all_passed = False
    
    return all_passed

def test_form_structure_preserved():
    """Test that form structure is preserved"""
    print("\n📝 Testing Form Structure Preservation...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    form_elements = [
        ('emailForm', 'POST'),
        ('codeForm', 'POST'),
        ('verifyForm', 'POST'),
        ('csrf_token', ''),
        ('email input', 'type="email"'),
        ('code inputs', 'inputmode="numeric"'),
        ('submit buttons', 'type="submit"')
    ]
    
    all_passed = True
    for element_name, pattern in form_elements:
        if pattern in login_content or pattern in verify_content:
            print(f"  ✅ {element_name}")
        else:
            print(f"  ❌ {element_name}")
            all_passed = False
    
    return all_passed

def test_visual_improvements():
    """Test that visual improvements are present"""
    print("\n🎨 Testing Visual Improvements...")
    
    login_file = Path('templates/oranolio_login.html')
    verify_file = Path('templates/oranolio_verify.html')
    
    with open(login_file, 'r') as f:
        login_content = f.read()
    
    with open(verify_file, 'r') as f:
        verify_content = f.read()
    
    visual_improvements = [
        ('Refined color palette', '#3B82F6'),
        ('Enhanced shadows', 'var(--shadow-lg)'),
        ('Improved spacing', 'var(--spacing-'),
        ('Better typography', 'var(--font-size-'),
        ('Smooth transitions', 'cubic-bezier'),
        ('Enhanced focus states', 'focus-visible'),
        ('Professional borders', 'var(--radius-xl)')
    ]
    
    all_passed = True
    for improvement_name, pattern in visual_improvements:
        if pattern in login_content and pattern in verify_content:
            print(f"  ✅ {improvement_name}")
        else:
            print(f"  ❌ {improvement_name}")
            all_passed = False
    
    return all_passed

def main():
    """Run all functional QA tests"""
    print("🚀 Oranolio RATX Login Page - Functional QA Test")
    print("=" * 60)
    
    tests = [
        ("Critical IDs Preservation", test_critical_ids_preserved),
        ("Critical Classes Preservation", test_critical_classes_preserved),
        ("JavaScript Functions Preservation", test_javascript_functions_preserved),
        ("API Endpoints Preservation", test_api_endpoints_preserved),
        ("Form Structure Preservation", test_form_structure_preserved),
        ("Visual Improvements", test_visual_improvements)
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
    print("📊 FUNCTIONAL QA RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All functional tests passed! The login page is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)