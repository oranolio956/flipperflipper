#!/usr/bin/env python3
"""
Stitch Startup Script
Validates environment and starts all Stitch services
"""

import sys
import os
import subprocess
import time

def validate_environment():
    """Validate the environment before starting"""
    print("🔍 Validating Stitch environment...")
    
    try:
        result = subprocess.run([
            sys.executable, 'validate_environment.py'
        ], capture_output=True, text=True, cwd='/workspace')
        
        if result.returncode == 0:
            print("✅ Environment validation passed")
            return True
        else:
            print("❌ Environment validation failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Environment validation error: {e}")
        return False

def start_services():
    """Start all Stitch services"""
    print("\n🚀 Starting Stitch services...")
    
    try:
        # Start web app
        print("Starting web application...")
        web_process = subprocess.Popen([
            sys.executable, 'web_app_real.py'
        ], cwd='/workspace')
        
        # Wait for web app to start
        print("Waiting for web app to start...")
        time.sleep(5)
        
        # Test web app
        import requests
        try:
            response = requests.get('http://localhost:5000/', timeout=10)
            if response.status_code == 200:
                print("✅ Web application started successfully")
            else:
                print(f"⚠️ Web application returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Web application may not be ready: {e}")
        
        print("\n" + "="*60)
        print("🎉 STITCH SERVICES STARTED SUCCESSFULLY!")
        print("="*60)
        print("📱 Web Interface: http://localhost:5000")
        print("🔌 Stitch Server: localhost:4040")
        print("📊 Dashboard: http://localhost:5000/dashboard")
        print("\nPress Ctrl+C to stop all services")
        
        # Keep running
        try:
            web_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            web_process.terminate()
            web_process.wait()
            print("✅ Services stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start services: {e}")
        return False

def main():
    """Main startup function"""
    print("="*60)
    print("🔐 STITCH C2 FRAMEWORK STARTUP")
    print("="*60)
    
    # Add workspace to path
    sys.path.insert(0, '/workspace')
    
    # Validate environment
    if not validate_environment():
        print("\n❌ Environment validation failed. Please fix the issues above.")
        return False
    
    # Start services
    if not start_services():
        print("\n❌ Failed to start services.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)