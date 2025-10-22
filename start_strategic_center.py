#!/usr/bin/env python3
"""
Strategic Command Center - Startup Script
No bullshit design with real-time architecture
"""

import os
import sys
import time
import subprocess
import socket
from pathlib import Path

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def start_redis():
    """Start Redis server"""
    print("🔄 Starting Redis server...")
    try:
        # Try to start Redis
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        
        # Check if it's running
        if check_redis():
            print("✅ Redis server started")
            return True
        else:
            print("❌ Failed to start Redis server")
            return False
    except Exception as e:
        print(f"❌ Error starting Redis: {e}")
        return False

def check_port(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def kill_existing_servers():
    """Kill any existing servers on port 5000"""
    if not check_port(5000):
        print("🔄 Killing existing server on port 5000...")
        try:
            subprocess.run(['pkill', '-f', 'strategic_web_app'], check=False)
            subprocess.run(['pkill', '-f', 'web_app_real'], check=False)
            time.sleep(1)
        except:
            pass

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main startup function"""
    print("🎯 Strategic Command Center - Startup")
    print("=" * 50)
    print("Core Principle: 'Everything has a purpose, nothing is decorative'")
    print("=" * 50)
    
    # Change to workspace directory
    os.chdir('/workspace')
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        return
    
    # Check Redis
    if not check_redis():
        print("⚠️ Redis not running, attempting to start...")
        if not start_redis():
            print("❌ Failed to start Redis. Please install and start Redis manually.")
            print("   Ubuntu/Debian: sudo apt-get install redis-server")
            print("   macOS: brew install redis")
            print("   Then run: redis-server")
            return
    
    # Kill existing servers
    kill_existing_servers()
    
    # Start Strategic Command Center
    print("\n🚀 Starting Strategic Command Center...")
    print("URL: http://localhost:5000")
    print("Design: No Bullshit - Everything has a purpose")
    print("=" * 50)
    
    try:
        from strategic_web_app import init_app, socketio, app
        init_app()
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Strategic Command Center stopped")
    except Exception as e:
        print(f"\n❌ Error starting Strategic Command Center: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()