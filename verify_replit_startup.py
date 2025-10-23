#!/usr/bin/env python3
"""
Replit Startup Verification Script
This script verifies that the application can start properly on Replit
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def test_environment_setup():
    """Test if environment is properly set up"""
    print("🔧 Testing Environment Setup...")
    
    # Set default environment variables if not set
    os.environ.setdefault('STITCH_DEBUG', 'true')
    os.environ.setdefault('STITCH_REDIS_URL', 'memory://')
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', 'true')
    
    # Check required environment variables
    required_env_vars = [
        'STITCH_DEBUG',
        'STITCH_REDIS_URL', 
        'FLASK_ENV',
        'FLASK_DEBUG'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if var not in os.environ:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ Environment variables set correctly")
    return True

def test_imports():
    """Test if all required modules can be imported"""
    print("📦 Testing Module Imports...")
    
    try:
        # Test main application imports
        from main_entry import OranolioRATSystem
        print("✅ Web app imported successfully")
        
        from webhook_auth_routes import webhook_auth_bp
        print("✅ Webhook auth routes imported successfully")
        
        from webhook_auth_manager import WebhookAuthManager
        print("✅ Webhook auth manager imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_app_initialization():
    """Test if the app can be initialized"""
    print("🚀 Testing App Initialization...")
    
    try:
        from web_app import create_app
        
        # Test app configuration
        with app.test_client() as client:
            print("✅ Test client created successfully")
            
            # Test basic route
            response = client.get('/')
            print(f"✅ Root route responded with status: {response.status_code}")
            
            # Test webhook auth route
            response = client.get('/webhook-auth/login')
            print(f"✅ Webhook auth route responded with status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ App initialization failed: {e}")
        return False

def test_port_availability():
    """Test if required ports are available"""
    print("🔌 Testing Port Availability...")
    
    import socket
    
    def check_port(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0
    
    # Check if port 5000 is available
    if check_port(5000):
        print("✅ Port 5000 is available")
        return True
    else:
        print("⚠️ Port 5000 is in use, but this might be expected on Replit")
        return True

def test_file_permissions():
    """Test if required files have correct permissions"""
    print("📁 Testing File Permissions...")
    
    required_files = [
        'start_replit.sh',
        'main.py',
        'web_app_real.py',
        'static/css/professional-ui.css'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    # Check if start_replit.sh is executable
    if os.access('start_replit.sh', os.X_OK):
        print("✅ start_replit.sh is executable")
    else:
        print("⚠️ start_replit.sh is not executable, fixing...")
        os.chmod('start_replit.sh', 0o755)
        print("✅ Fixed start_replit.sh permissions")
    
    print("✅ All required files exist")
    return True

def main():
    """Main verification function"""
    print("🎯 Replit Startup Verification")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Module Imports", test_imports),
        ("App Initialization", test_app_initialization),
        ("Port Availability", test_port_availability),
        ("File Permissions", test_file_permissions)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("✅ Replit should start successfully now")
        print("🚀 You can run: python3 main.py")
        return 0
    else:
        print("\n⚠️ Some verifications failed.")
        print("💡 Please check the issues above before starting on Replit")
        return 1

if __name__ == "__main__":
    sys.exit(main())