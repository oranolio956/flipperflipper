#!/usr/bin/env python3
"""
Verify what's happening with command execution
"""

import os
import sys
import time
import subprocess
import requests
import re

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securepassword123'

# Start server
print("[*] Starting server...")
server = subprocess.Popen(
    ['python3', 'web_app_real.py'],
    cwd='/workspace',
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(8)

try:
    session = requests.Session()
    
    # Login
    resp = session.get('http://localhost:5000/login')
    csrf_token = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text).group(1)
    
    login_data = {
        'username': 'admin',
        'password': 'securepassword123',
        'csrf_token': csrf_token
    }
    
    resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
    print(f"[+] Logged in: {resp.status_code}")
    
    # Get updated CSRF
    resp = session.get('http://localhost:5000/')
    csrf_token = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text).group(1)
    
    # Start our working payload
    print("\n[*] Starting working payload...")
    from create_working_payload import create_full_stitch_payload
    
    code = create_full_stitch_payload()
    with open('/tmp/working_payload.py', 'w') as f:
        f.write(code)
    
    payload = subprocess.Popen(['python3', '/tmp/working_payload.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(4)
    
    # Check connections
    headers = {'X-CSRFToken': csrf_token}
    resp = session.get('http://localhost:5000/api/connections', headers=headers)
    
    connections = resp.json()
    print(f"[+] Found {len(connections)} connections")
    
    # Find online target
    target_id = None
    for conn in connections:
        if conn.get('status') == 'online':
            target_id = conn.get('id') or conn.get('target')
            print(f"[+] Using target: {target_id}")
            break
    
    if target_id:
        # Test different commands
        test_commands = [
            ('sessions', 'List sessions'),
            ('help', 'Show help'),
            ('pwd', 'Current directory'),
            ('whoami', 'Current user')
        ]
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }
        
        for cmd, desc in test_commands:
            print(f"\n[*] Testing: {desc} ({cmd})")
            
            data = {
                'connection_id': target_id,
                'command': cmd
            }
            
            resp = session.post(
                'http://localhost:5000/api/execute',
                json=data,
                headers=headers
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('success'):
                    output = result.get('output', '')
                    # Show first few lines
                    lines = output.split('\n')[:5]
                    for line in lines:
                        print(f"    {line[:80]}")
                    
                    if 'Handshake failed' in output:
                        print("    [!] Handshake issue detected")
                    elif 'Error' in output:
                        print("    [!] Error in output")
                    else:
                        print("    [+] Command successful")
                else:
                    print(f"    [-] Failed: {result.get('error')}")
            else:
                print(f"    [-] API error: {resp.status_code}")
    
    # Cleanup
    payload.terminate()

finally:
    server.terminate()
    server.wait(timeout=5)