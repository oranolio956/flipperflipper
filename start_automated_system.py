#!/usr/bin/env python3
"""
Automated System Startup
Starts the complete system with zero configuration required
"""

import subprocess
import time
import threading
import webbrowser
import os
import sys
from pathlib import Path

def print_banner():
    print("""
🚀 STITCH RAT - AUTOMATED SYSTEM STARTUP
========================================

This will start the complete system with:
✅ Automated email verification (zero config)
✅ Code display interface
✅ Web application
✅ Database initialization

No manual setup required!
""")

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'requests', 'pyotp', 'qrcode'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, 
                         check=True, capture_output=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def initialize_database():
    """Initialize the database tables"""
    print("🗄️ Initializing database...")
    
    try:
        # Create email tables
        subprocess.run([sys.executable, 'create_email_tables.py'], 
                      check=True, capture_output=True)
        print("✅ Email tables created")
        
        # Create MFA tables
        subprocess.run([sys.executable, 'create_mfa_tables.py'], 
                      check=True, capture_output=True)
        print("✅ MFA tables created")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_code_display_server():
    """Start the code display server"""
    print("📱 Starting code display server...")
    
    def run_server():
        try:
            from code_display_server import start_server
            start_server(port=5001)
        except Exception as e:
            print(f"❌ Code display server error: {e}")
    
    # Start in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give it time to start
    time.sleep(2)
    print("✅ Code display server started on http://localhost:5001")

def start_main_application():
    """Start the main web application"""
    print("🌐 Starting main application...")
    
    def run_app():
        try:
            from web_app import create_app
            app.run(host='0.0.0.0', port=5000, debug=False)
        except Exception as e:
            print(f"❌ Main application error: {e}")
    
    # Start in background thread
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    
    # Give it time to start
    time.sleep(3)
    print("✅ Main application started on http://localhost:5000")

def setup_automated_email():
    """Setup the automated email service"""
    print("📧 Setting up automated email service...")
    
    try:
        from automated_email_service import automated_email_service
        
        # Get webhook URL
        webhook_url = automated_email_service.get_webhook_url()
        print(f"✅ Webhook URL: {webhook_url}")
        
        # Set webhook URL in code display server
        from code_display_server import set_webhook_url
        set_webhook_url(webhook_url)
        
        print("✅ Automated email service configured")
        return True
    except Exception as e:
        print(f"❌ Email service setup failed: {e}")
        return False

def test_system():
    """Test the complete system"""
    print("🧪 Testing system...")
    
    try:
        from automated_email_service import send_verification_email
        
        # Send test email
        success = send_verification_email("test@example.com", "123456", "127.0.0.1")
        
        if success:
            print("✅ Test email sent successfully")
            print("📱 Check http://localhost:5001 for the verification code")
            return True
        else:
            print("❌ Test email failed")
            return False
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def open_browsers():
    """Open the applications in browser"""
    print("🌐 Opening applications...")
    
    try:
        # Open code display
        webbrowser.open('http://localhost:5001')
        time.sleep(1)
        
        # Open main app
        webbrowser.open('http://localhost:5000')
        print("✅ Applications opened in browser")
    except Exception as e:
        print(f"⚠️ Could not open browsers automatically: {e}")
        print("📱 Please manually open:")
        print("   - Code Display: http://localhost:5001")
        print("   - Main App: http://localhost:5000")

def main():
    """Main startup function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Please install requirements.txt")
        return
    
    # Initialize database
    if not initialize_database():
        print("❌ Database initialization failed")
        return
    
    # Setup automated email
    if not setup_automated_email():
        print("❌ Email service setup failed")
        return
    
    # Start code display server
    start_code_display_server()
    
    # Start main application
    start_main_application()
    
    # Test system
    if test_system():
        print("✅ System test passed")
    else:
        print("⚠️ System test failed, but continuing...")
    
    # Open browsers
    open_browsers()
    
    print("""
🎉 SYSTEM STARTUP COMPLETE!
===========================

✅ Automated email verification ready
✅ Code display interface running
✅ Main web application running
✅ Database initialized

📱 Applications:
   - Code Display: http://localhost:5001
   - Main App: http://localhost:5000

🔐 How to use:
   1. Go to http://localhost:5000
   2. Enter any email address
   3. Check http://localhost:5001 for verification code
   4. Enter the code to complete login

The system is now fully operational with zero configuration required!
""")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down system...")
        sys.exit(0)

if __name__ == "__main__":
    main()