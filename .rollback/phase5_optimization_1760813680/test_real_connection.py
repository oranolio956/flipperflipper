#!/usr/bin/env python3
"""
Test REAL payload connection - not simulation
"""

import os
import sys
import time
import socket
import subprocess
import threading

def test_simple_c2():
    """Test with a simple C2 server"""
    print("="*70)
    print("TESTING REAL PAYLOAD CONNECTION")
    print("="*70)
    
    # Start a simple C2 listener
    print("\n[1] Starting simple C2 listener on port 4040...")
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('127.0.0.1', 4040))
    server_sock.listen(5)
    server_sock.settimeout(10)  # 10 second timeout
    
    print("[+] Listening on 127.0.0.1:4040")
    
    # Start the payload in background
    print("\n[2] Executing test payload...")
    payload_proc = subprocess.Popen(
        ['python3', '/tmp/simple_payload.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"[+] Payload started (PID: {payload_proc.pid})")
    
    # Wait for connection
    print("\n[3] Waiting for payload connection...")
    
    try:
        client_sock, addr = server_sock.accept()
        print(f"[+] Connection received from {addr}")
        
        # Receive beacon
        data = client_sock.recv(1024)
        print(f"[+] Received: {data.decode().strip()}")
        
        # Send test commands
        print("\n[4] Testing command execution...")
        
        test_commands = [
            ('pwd', 'Get current directory'),
            ('whoami', 'Get current user'),
            ('echo "Hello from C2"', 'Echo test'),
            ('ls -la /tmp | head -5', 'List files'),
        ]
        
        for cmd, description in test_commands:
            print(f"\n  Testing: {description}")
            print(f"  Sending: {cmd}")
            
            client_sock.send((cmd + '\n').encode())
            time.sleep(0.5)
            
            # Receive output
            output = client_sock.recv(4096).decode()
            print(f"  Output: {output[:100]}...")
        
        # Close connection
        client_sock.send(b'exit\n')
        client_sock.close()
        
        print("\n[+] SUCCESS - Payload connected and executed commands!")
        return True
        
    except socket.timeout:
        print("[-] Timeout - no connection received")
        
        # Check if payload is still running
        if payload_proc.poll() is not None:
            stdout, stderr = payload_proc.communicate()
            print("[-] Payload exited:")
            print(f"    stdout: {stdout.decode()[:200]}")
            print(f"    stderr: {stderr.decode()[:200]}")
        return False
        
    except Exception as e:
        print(f"[-] Error: {e}")
        return False
        
    finally:
        # Cleanup
        server_sock.close()
        payload_proc.terminate()
        try:
            payload_proc.wait(timeout=2)
        except Exception:
            payload_proc.kill()

def test_with_stitch_server():
    """Test with the actual Stitch server"""
    print("\n" + "="*70)
    print("TESTING WITH STITCH SERVER")
    print("="*70)
    
    # Start Stitch server
    print("\n[1] Starting Stitch C2 server...")
    
    server_script = '''
import sys
sys.path.insert(0, '/workspace')
from Application.stitch_cmd import stitch_server

server = stitch_server()
server.do_listen('4040')

import time
timeout = time.time() + 15  # 15 second timeout

while time.time() < timeout:
    if server.inf_sock:
        print(f"[+] Connections: {list(server.inf_sock.keys())}")
        break
    time.sleep(1)
else:
    print("[-] No connections received")
'''
    
    with open('/tmp/stitch_server.py', 'w') as f:
        f.write(server_script)
    
    server_proc = subprocess.Popen(
        ['python3', '/tmp/stitch_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Execute Stitch payload
    print("[2] Executing Stitch payload...")
    payload_proc = subprocess.Popen(
        ['python3', '/tmp/stitch_payload.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"[+] Payload started (PID: {payload_proc.pid})")
    
    # Wait and check for output
    print("[3] Waiting for connection...")
    time.sleep(5)
    
    # Get server output
    try:
        stdout, stderr = server_proc.communicate(timeout=10)
        print("\nServer output:")
        print(stdout)
        
        if "[+] Connections:" in stdout:
            print("\n[+] Stitch payload connected!")
            return True
        else:
            print("\n[-] No connection detected")
            
    except subprocess.TimeoutExpired:
        print("[-] Server timeout")
    
    # Cleanup
    payload_proc.terminate()
    server_proc.terminate()
    
    return False

if __name__ == "__main__":
    # Test 1: Simple C2
    success1 = test_simple_c2()
    
    # Test 2: Stitch server
    success2 = test_with_stitch_server()
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"Simple C2 test: {'PASSED ✓' if success1 else 'FAILED ✗'}")
    print(f"Stitch server test: {'PASSED ✓' if success2 else 'FAILED ✗'}")
    
    if success1:
        print("\n✓ Payloads CAN connect and execute commands")
        print("The issue is with the Stitch payload format, not networking")
    
    sys.exit(0 if success1 else 1)