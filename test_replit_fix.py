#!/usr/bin/env python3
"""
Test script to verify Replit configuration fixes
"""

import os
import sys
import subprocess
import json

def test_replit_config():
    """Test Replit configuration"""
    print("🔍 Testing Replit Configuration...")
    
    # Check if .replit file exists and is valid
    if not os.path.exists('.replit'):
        print("❌ .replit file not found")
        return False
    
    # Try to parse .replit file
    try:
        with open('.replit', 'r') as f:
            content = f.read()
        print("✅ .replit file exists and is readable")
    except Exception as e:
        print(f"❌ Error reading .replit: {e}")
        return False
    
    # Check if replit.nix exists
    if not os.path.exists('replit.nix'):
        print("❌ replit.nix file not found")
        return False
    else:
        print("✅ replit.nix file exists")
    
    # Check if start_replit.sh exists and is executable
    if not os.path.exists('start_replit.sh'):
        print("❌ start_replit.sh file not found")
        return False
    else:
        print("✅ start_replit.sh file exists")
        
        # Check if it's executable
        if os.access('start_replit.sh', os.X_OK):
            print("✅ start_replit.sh is executable")
        else:
            print("⚠️ start_replit.sh is not executable, fixing...")
            os.chmod('start_replit.sh', 0o755)
            print("✅ Fixed start_replit.sh permissions")
    
    # Check if main.py exists
    if not os.path.exists('main.py'):
        print("❌ main.py file not found")
        return False
    else:
        print("✅ main.py file exists")
    
    # Check if requirements.txt exists
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt file not found")
        return False
    else:
        print("✅ requirements.txt file exists")
    
    return True

def test_python_imports():
    """Test if critical Python modules can be imported"""
    print("\n🐍 Testing Python Imports...")
    
    critical_modules = [
        'flask',
        'flask_socketio',
        'flask_cors',
        'werkzeug',
        'Crypto',
        'pyotp',
        'qrcode',
        'PIL',
        'requests',
        'psutil',
        'colorama'
    ]
    
    failed_imports = []
    
    for module in critical_modules:
        try:
            if module == 'Crypto':
                import Crypto
            elif module == 'PIL':
                from PIL import Image
            else:
                __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️ Failed imports: {failed_imports}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    return True

def test_web_app():
    """Test if web app can be imported and initialized"""
    print("\n🌐 Testing Web App...")
    
    try:
        # Test web app import
        from web_app import create_app
        print("✅ Web app imported successfully")
        
        # Test app configuration
        if hasattr(app, 'config'):
            print("✅ App has configuration")
        else:
            print("❌ App missing configuration")
            return False
        
        # Test if app can be created
        with app.test_client() as client:
            print("✅ Test client created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Web app test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Replit Configuration Test")
    print("=" * 40)
    
    tests = [
        ("Replit Config", test_replit_config),
        ("Python Imports", test_python_imports),
        ("Web App", test_web_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Replit should work now.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())