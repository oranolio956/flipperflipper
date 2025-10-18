#!/usr/bin/env python3
"""
ACTUAL verification test - no assumptions, just real testing
"""

import os
import sys
import time
import subprocess
import requests
import re
import json
import socket

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securepassword123'

print("="*70)
print("ACTUAL VERIFICATION TEST - NO ASSUMPTIONS")
print("="*70)

results = {}

# Test 1: Can we start the server?
print("\n[TEST 1] Starting web server...")
server_proc = subprocess.Popen(
    ['python3', 'web_app_real.py'],
    cwd='/workspace',
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait and check
server_started = False
for i in range(10):
    time.sleep(2)
    try:
        resp = requests.get('http://localhost:5000/health', timeout=2)
        if resp.status_code == 200:
            server_started = True
            break
    except Exception:
        continue

if server_started:
    print("  ✓ Server started")
    results['server_start'] = True
else:
    print("  ✗ Server failed to start")
    # Get error output
    stdout, stderr = server_proc.communicate(timeout=2)
    print(f"  Error: {stderr[:500]}")
    results['server_start'] = False
    server_proc.terminate()
    sys.exit(1)

# Test 2: Can we login?
print("\n[TEST 2] Testing login...")
session = requests.Session()

resp = session.get('http://localhost:5000/login')
csrf_token = None
if 'csrf_token' in resp.text:
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
    if match:
        csrf_token = match.group(1)
        print(f"  Got CSRF token")

login_data = {
    'username': 'admin',
    'password': 'securepassword123'
}

if csrf_token:
    login_data['csrf_token'] = csrf_token

resp = session.post(
    'http://localhost:5000/login',
    data=login_data,
    allow_redirects=False
)

if resp.status_code in [302, 303]:
    print("  ✓ Login successful")
    results['login'] = True
    
    # Get updated CSRF
    resp = session.get('http://localhost:5000/')
    if 'csrf-token' in resp.text:
        match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
else:
    print(f"  ✗ Login failed: {resp.status_code}")
    results['login'] = False

# Test 3: Can we generate a payload?
print("\n[TEST 3] Testing payload generation...")
if results.get('login'):
    config = {
        'bind_host': '',
        'bind_port': '',
        'listen_host': '127.0.0.1',
        'listen_port': '4040',
        'enable_bind': False,
        'enable_listen': True,
        'platform': 'python'  # Start with Python for simplicity
    }
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    resp = session.post(
        'http://localhost:5000/api/generate-payload',
        json=config,
        headers=headers
    )
    
    if resp.status_code == 200:
        try:
            result = resp.json()
            if result.get('success'):
                print(f"  ✓ Payload generated: {result.get('payload_type')}")
                results['payload_gen'] = True
            else:
                print(f"  ✗ Generation failed: {result.get('message')}")
                results['payload_gen'] = False
        except Exception:
            print(f"  ✗ Invalid response")
            results['payload_gen'] = False
    else:
        print(f"  ✗ API error: {resp.status_code}")
        print(f"    Response: {resp.text[:200]}")
        results['payload_gen'] = False
else:
    print("  Skipped (login failed)")
    results['payload_gen'] = False

# Test 4: Can we check connections?
print("\n[TEST 4] Testing connections API...")
if results.get('login'):
    headers = {'X-CSRFToken': csrf_token}
    
    resp = session.get(
        'http://localhost:5000/api/connections',
        headers=headers
    )
    
    if resp.status_code == 200:
        try:
            connections = resp.json()
            print(f"  ✓ Got {len(connections)} connections")
            results['connections_api'] = True
        except Exception:
            print(f"  ✗ Invalid response")
            results['connections_api'] = False
    else:
        print(f"  ✗ API error: {resp.status_code}")
        results['connections_api'] = False
else:
    print("  Skipped (login failed)")
    results['connections_api'] = False

# Test 5: Start a simple payload
print("\n[TEST 5] Starting test payload...")

# Create simple payload that definitely works
simple_payload = '''#!/usr/bin/env python3
import socket
import time
import sys

print("[Payload] Starting...")
while True:
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 4040))
        print("[Payload] Connected!")
        s.send(b"TEST_BEACON\\n")
        time.sleep(5)
        s.close()
        break
    except Exception as e:
        print(f"[Payload] Failed: {e}")
        time.sleep(2)
'''

with open('/tmp/test_beacon.py', 'w') as f:
    f.write(simple_payload)

payload_proc = subprocess.Popen(
    ['python3', '/tmp/test_beacon.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print(f"  Started PID: {payload_proc.pid}")
time.sleep(5)

# Check if it's still running
if payload_proc.poll() is None:
    print("  ✓ Payload still running")
    results['payload_runs'] = True
    
    # Check if it connected
    if results.get('login'):
        resp = session.get(
            'http://localhost:5000/api/connections',
            headers={'X-CSRFToken': csrf_token}
        )
        
        if resp.status_code == 200:
            connections = resp.json()
            online = [c for c in connections if c.get('status') == 'online']
            if online:
                print(f"  ✓ Payload connected! ({len(online)} online)")
                results['payload_connects'] = True
            else:
                print(f"  ✗ No online connections")
                results['payload_connects'] = False
else:
    stdout, stderr = payload_proc.communicate(timeout=1)
    print(f"  ✗ Payload exited")
    print(f"    Output: {stdout[:200]}")
    print(f"    Error: {stderr[:200]}")
    results['payload_runs'] = False
    results['payload_connects'] = False

# Test 6: Can we execute commands?
print("\n[TEST 6] Testing command execution...")
if results.get('login') and results.get('payload_connects'):
    # Get target ID
    resp = session.get(
        'http://localhost:5000/api/connections',
        headers={'X-CSRFToken': csrf_token}
    )
    
    target_id = None
    if resp.status_code == 200:
        connections = resp.json()
        for conn in connections:
            if conn.get('status') == 'online':
                target_id = conn.get('id') or conn.get('target')
                break
    
    if target_id:
        data = {
            'connection_id': target_id,
            'command': 'pwd'
        }
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }
        
        resp = session.post(
            'http://localhost:5000/api/execute',
            json=data,
            headers=headers
        )
        
        if resp.status_code == 200:
            try:
                result = resp.json()
                if result.get('success'):
                    print(f"  ✓ Command executed")
                    print(f"    Output: {result.get('output', '')[:50]}")
                    results['command_exec'] = True
                else:
                    print(f"  ✗ Command failed: {result.get('error')}")
                    results['command_exec'] = False
            except Exception:
                print(f"  ✗ Invalid response")
                results['command_exec'] = False
        else:
            print(f"  ✗ API error: {resp.status_code}")
            results['command_exec'] = False
    else:
        print(f"  ✗ No target found")
        results['command_exec'] = False
else:
    print("  Skipped (no connection)")
    results['command_exec'] = False

# Cleanup
print("\n[*] Cleaning up...")
if 'payload_proc' in locals():
    payload_proc.terminate()
server_proc.terminate()
try:
    server_proc.wait(timeout=5)
except Exception:
    server_proc.kill()

# Final results
print("\n" + "="*70)
print("ACTUAL RESULTS")
print("="*70)

for test, passed in results.items():
    status = "✓ WORKS" if passed else "✗ BROKEN"
    print(f"{test:20} {status}")

working_count = sum(1 for v in results.values() if v)
total_count = len(results)

print(f"\n{working_count}/{total_count} tests passed")

if working_count == total_count:
    print("\n✓ EVERYTHING IS ACTUALLY WORKING")
else:
    print(f"\n✗ {total_count - working_count} THINGS ARE STILL BROKEN")