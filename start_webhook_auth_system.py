#!/usr/bin/env python3
"""
Webhook Authentication System Startup Script
Comprehensive startup and validation for the webhook-based authentication system
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("\n" + "="*80)
    print("🔐 WEBHOOK AUTHENTICATION SYSTEM - STARTUP")
    print("="*80)
    print("Secure webhook-based authentication with MFA integration")
    print("="*80 + "\n")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_socketio', 'flask_limiter', 'flask_wtf',
        'pyotp', 'qrcode', 'cryptography', 'requests', 'pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Installing missing packages...")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, check=True)
            print("   ✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install dependencies: {e}")
            return False
    
    return True

def setup_directories():
    """Create required directories"""
    print("\n📁 Setting up directories...")
    
    directories = [
        'Application',
        'Logs', 
        'Uploads',
        'Downloads',
        'backups'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}/")
    
    return True

def run_security_tests():
    """Run security validation tests"""
    print("\n🔒 Running security validation...")
    
    try:
        # Run comprehensive test
        result = subprocess.run([
            sys.executable, 'test_webhook_auth_system.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ System tests passed")
        else:
            print("  ❌ System tests failed")
            print(f"     Error: {result.stderr}")
            return False
        
        # Run security audit
        result = subprocess.run([
            sys.executable, 'security_audit_webhook_auth.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ Security audit passed")
        else:
            print("  ❌ Security audit failed")
            print(f"     Error: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Security validation failed: {e}")
        return False

def start_web_server():
    """Start the web server"""
    print("\n🌐 Starting web server...")
    
    try:
        # Start the web application
        print("  🚀 Launching webhook authentication system...")
        print("  📍 Web interface: http://localhost:5000")
        print("  🔗 Webhook dashboard: http://localhost:5000/webhook-auth/webhook-dashboard")
        print("  🔐 Login page: http://localhost:5000/login")
        print("\n  Press Ctrl+C to stop the server")
        print("  " + "="*60)
        
        # Start the server
        subprocess.run([sys.executable, 'web_app_real.py'])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print_banner()
    
    # Check if we're in the right directory
    if not Path('web_app_real.py').exists():
        print("❌ Error: web_app_real.py not found")
        print("   Please run this script from the project root directory")
        sys.exit(1)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)
    
    # Step 2: Setup directories
    if not setup_directories():
        print("\n❌ Directory setup failed")
        sys.exit(1)
    
    # Step 3: Run security tests
    if not run_security_tests():
        print("\n❌ Security validation failed")
        print("   Please fix security issues before starting the server")
        sys.exit(1)
    
    # Step 4: Start web server
    print("\n✅ All checks passed! Starting webhook authentication system...")
    time.sleep(2)
    
    if not start_web_server():
        print("\n❌ Failed to start web server")
        sys.exit(1)

if __name__ == "__main__":
    main()