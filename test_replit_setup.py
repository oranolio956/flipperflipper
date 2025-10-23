#!/usr/bin/env python3
"""
Test script to verify Replit setup is working correctly
"""

import os
import sys
import time
import socket
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Core Flask
        import flask
        import flask_socketio
        import flask_limiter
        import flask_wtf
        import flask_cors
        print("✅ Flask modules imported")
        
        # Security
        import pycryptodome
        import cryptography
        import pyotp
        import jwt
        print("✅ Security modules imported")
        
        # Database
        import sqlalchemy
        import aiosqlite
        print("✅ Database modules imported")
        
        # Other core modules
        import redis
        import requests
        import qrcode
        import pillow
        import psutil
        import colorama
        print("✅ Core modules imported")
        
        # Optional modules
        try:
            import telethon
            print("✅ Telegram module imported")
        except ImportError:
            print("⚠️  Telegram module not available (optional)")
        
        try:
            import playwright
            print("✅ Playwright module imported")
        except ImportError:
            print("⚠️  Playwright module not available (optional)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_web_app():
    """Test that the web app can be imported and initialized"""
    print("🌐 Testing web application...")
    
    try:
        from web_app_real import app
        print("✅ Web app imported successfully")
        
        # Test basic app properties
        if hasattr(app, 'config'):
            print("✅ App has configuration")
        else:
            print("❌ App missing configuration")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Web app error: {e}")
        return False

def test_backend():
    """Test that backend services can be imported"""
    print("🔧 Testing backend services...")
    
    try:
        from Application.stitch_cmd import stitch_server
        print("✅ Backend services imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    print("📁 Testing directories...")
    
    required_dirs = [
        "Application",
        "Core", 
        "Configuration",
        "templates",
        "static",
        "logs"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def test_environment():
    """Test environment variables"""
    print("⚙️ Testing environment...")
    
    required_env = [
        'STITCH_DEBUG',
        'STITCH_ADMIN_USER',
        'STITCH_ADMIN_PASSWORD'
    ]
    
    all_set = True
    for env_var in required_env:
        if os.getenv(env_var):
            print(f"✅ Environment variable set: {env_var}")
        else:
            print(f"❌ Environment variable missing: {env_var}")
            all_set = False
    
    return all_set

def test_port_availability():
    """Test that required ports are available"""
    print("🔌 Testing port availability...")
    
    def is_port_available(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0
    
    if is_port_available(5000):
        print("✅ Port 5000 is available")
        return True
    else:
        print("❌ Port 5000 is in use")
        return False

def main():
    """Run all tests"""
    print("🧪 Replit Setup Verification")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Web App", test_web_app),
        ("Backend", test_backend),
        ("Directories", test_directories),
        ("Environment", test_environment),
        ("Ports", test_port_availability)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for Replit.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)