#!/usr/bin/env python3
"""
Debug and fix the remaining API issues:
1. Payload generation API failing
2. Command execution API returning 400
"""

import os
import sys
import time
import subprocess
import requests
import re
import json

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

def start_web_server_with_debug():
    """Start web server with debug output"""
    print("[*] Starting web server with debug output...")
    
    # Create a wrapper script that shows errors
    debug_script = '''
import os
import sys
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'
os.environ['FLASK_ENV'] = 'development'

# Import and run with error handling
try:
    from web_app_real import app, socketio, start_stitch_server
    import threading
    
    # Start background server
    server_thread = threading.Thread(target=start_stitch_server, daemon=True)
    server_thread.start()
    
    # Run web interface
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
'''
    
    with open('/tmp/debug_web.py', 'w') as f:
        f.write(debug_script)
    
    proc = subprocess.Popen(
        ['python3', '/tmp/debug_web.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitor output
    def monitor():
        for line in proc.stdout:
            if 'ERROR' in line or '400' in line or 'Failed' in line:
                print(f"  DEBUG: {line.strip()}")
    
    import threading
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    
    # Wait for server
    time.sleep(5)
    
    return proc

def debug_payload_generation():
    """Debug why payload generation fails"""
    print("\n[DEBUGGING] Payload Generation API...")
    
    session = requests.Session()
    
    # Login first
    resp = session.get('http://localhost:5000/login')
    csrf_token = None
    if 'csrf_token' in resp.text:
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
    
    login_data = {'username': 'admin', 'password': 'testpassword123'}
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
    
    if resp.status_code not in [302, 303]:
        print("  [-] Login failed")
        return
    
    print("  [+] Logged in")
    
    # Try different payload configurations
    test_configs = [
        {
            'name': 'Minimal config',
            'data': {
                'platform': 'python'
            }
        },
        {
            'name': 'Basic listen config',
            'data': {
                'bind_host': '',
                'bind_port': '',
                'listen_host': '127.0.0.1',
                'listen_port': '4040',
                'enable_bind': False,
                'enable_listen': True,
                'platform': 'python'
            }
        },
        {
            'name': 'Full config with strings',
            'data': {
                'bind_host': '',
                'bind_port': '0',  # String zero
                'listen_host': '127.0.0.1',
                'listen_port': '4040',
                'enable_bind': False,
                'enable_listen': True,
                'platform': 'python',
                'payload_name': 'test'
            }
        }
    ]
    
    for config in test_configs:
        print(f"\n  Testing: {config['name']}")
        print(f"    Data: {json.dumps(config['data'], indent=6)}")
        
        resp = session.post(
            'http://localhost:5000/api/generate-payload',
            json=config['data'],
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"    Response: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                result = resp.json()
                if result.get('success'):
                    print(f"    [+] SUCCESS!")
                    print(f"        Type: {result.get('payload_type')}")
                    print(f"        Size: {result.get('payload_size')}")
                else:
                    print(f"    [-] Failed: {result.get('error', result.get('message'))}")
            except Exception:
                print(f"    [-] Non-JSON response: {resp.text[:200]}")
        elif resp.status_code == 500:
            try:
                error = resp.json()
                print(f"    [-] Server error: {error.get('error', 'Unknown')}")
            except Exception:
                print(f"    [-] Server error: {resp.text[:200]}")
        else:
            print(f"    [-] Unexpected status: {resp.text[:200]}")

def debug_command_execution():
    """Debug why command execution returns 400"""
    print("\n[DEBUGGING] Command Execution API...")
    
    session = requests.Session()
    
    # Login
    resp = session.get('http://localhost:5000/login')
    csrf_token = None
    if 'csrf_token' in resp.text:
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
    
    login_data = {'username': 'admin', 'password': 'testpassword123'}
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
    print("  [+] Logged in")
    
    # Get connections first
    resp = session.get('http://localhost:5000/api/connections')
    if resp.status_code == 200:
        connections = resp.json()
        print(f"  [+] Found {len(connections)} connections")
        
        # Find online connection
        target_id = None
        for conn in connections:
            if conn.get('status') == 'online':
                target_id = conn.get('id') or conn.get('target')
                print(f"  [+] Using target: {target_id}")
                break
        
        if target_id:
            # Test different command formats
            test_commands = [
                {
                    'name': 'Basic command',
                    'data': {
                        'connection_id': target_id,
                        'command': 'pwd'
                    }
                },
                {
                    'name': 'Without connection_id',
                    'data': {
                        'command': 'pwd'
                    }
                },
                {
                    'name': 'With target instead',
                    'data': {
                        'target': target_id,
                        'command': 'pwd'
                    }
                },
                {
                    'name': 'Different field names',
                    'data': {
                        'conn_id': target_id,
                        'cmd': 'pwd'
                    }
                }
            ]
            
            for test in test_commands:
                print(f"\n  Testing: {test['name']}")
                print(f"    Data: {json.dumps(test['data'], indent=6)}")
                
                # Try with JSON
                resp = session.post(
                    'http://localhost:5000/api/execute',
                    json=test['data'],
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"    JSON Response: {resp.status_code}")
                
                if resp.status_code == 400:
                    print(f"      Error: {resp.text[:200]}")
                elif resp.status_code == 200:
                    result = resp.json()
                    if result.get('success'):
                        print(f"      [+] SUCCESS: {result.get('output', '')[:50]}")
                
                # Try with form data
                resp = session.post(
                    'http://localhost:5000/api/execute',
                    data=test['data']
                )
                
                print(f"    Form Response: {resp.status_code}")
                
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('success'):
                        print(f"      [+] SUCCESS: {result.get('output', '')[:50]}")

def check_api_code():
    """Check the actual API code for issues"""
    print("\n[CHECKING] API Implementation...")
    
    # Check execute endpoint
    with open('/workspace/web_app_real.py', 'r') as f:
        content = f.read()
    
    # Find execute endpoint
    import re
    execute_match = re.search(r"@app\.route\('/api/execute'.*?\n(.*?)^@app\.route", content, re.DOTALL | re.MULTILINE)
    
    if execute_match:
        execute_code = execute_match.group(0)
        
        # Check what it expects
        if 'request.json' in execute_code:
            print("  [+] Execute endpoint expects JSON")
        if 'request.form' in execute_code:
            print("  [+] Execute endpoint expects form data")
        if 'connection_id' in execute_code:
            print("  [+] Expects 'connection_id' field")
        if 'command' in execute_code:
            print("  [+] Expects 'command' field")
    
    # Check generate-payload endpoint
    generate_match = re.search(r"@app\.route\('/api/generate-payload'.*?\n(.*?)^@app\.route", content, re.DOTALL | re.MULTILINE)
    
    if generate_match:
        generate_code = generate_match.group(0)
        
        # Look for the issue
        if 'web_payload_generator' in generate_code:
            print("  [+] Uses web_payload_generator module")
        if 'web_payload_gen' in generate_code:
            print("  [+] Uses web_payload_gen instance")

def main():
    print("="*70)
    print("DEBUGGING API ISSUES")
    print("="*70)
    
    # Check code first
    check_api_code()
    
    # Start server
    server_proc = start_web_server_with_debug()
    
    try:
        # Wait for server
        time.sleep(5)
        
        # Start a test payload for command testing
        print("\n[*] Starting test payload...")
        payload_proc = subprocess.Popen(
            ['python3', '/tmp/stitch_payload.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(3)
        
        # Debug issues
        debug_payload_generation()
        debug_command_execution()
        
        # Cleanup payload
        payload_proc.terminate()
        
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except Exception:
            server_proc.kill()
    
    print("\n" + "="*70)
    print("FINDINGS")
    print("="*70)

if __name__ == "__main__":
    main()