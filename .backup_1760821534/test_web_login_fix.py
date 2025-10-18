#!/usr/bin/env python3
"""
Test and fix the web login issue
Research: Login returns 400 because it expects form data, not JSON
"""

import os
import sys
import time
import requests
import subprocess
import re

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securepassword123'

def start_web_server():
    """Start the web server for testing"""
    print("[*] Starting web server...")
    
    proc = subprocess.Popen(
        ['python3', 'web_app_real.py'],
        cwd='/workspace',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Wait for server
    for i in range(10):
        time.sleep(2)
        try:
            resp = requests.get('http://localhost:5000/health')
            if resp.status_code == 200:
                print("[+] Web server running")
                return proc
        except Exception:
            continue
    
    print("[-] Server failed to start")
    proc.terminate()
    return
def test_login_methods():
    """Test different login methods to find what works"""
    
    print("\n[*] Testing login methods...")
    
    session = requests.Session()
    base_url = 'http://localhost:5000'
    
    # Method 1: Form data without CSRF
    print("\n[1] Testing form data without CSRF...")
    login_data = {
        'username': 'admin',
        'password': 'securepassword123'
    }
    
    resp = session.post(
        f'{base_url}/login',
        data=login_data,  # Form data
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        allow_redirects=False
    )
    
    print(f"    Response: {resp.status_code}")
    if resp.status_code in [302, 303]:
        print("    [+] SUCCESS - Form data works!")
        return session
    
    # Method 2: Get CSRF token first
    print("\n[2] Testing with CSRF token...")
    session = requests.Session()
    
    # Get login page
    resp = session.get(f'{base_url}/login')
    
    # Extract CSRF token
    csrf_token = None
    if 'csrf_token' in resp.text:
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
            print(f"    Found CSRF token: {csrf_token[:20]}...")
    
    if csrf_token:
        login_data = {
            'username': 'admin',
            'password': 'securepassword123',
            'csrf_token': csrf_token
        }
        
        resp = session.post(
            f'{base_url}/login',
            data=login_data,
            allow_redirects=False
        )
        
        print(f"    Response: {resp.status_code}")
        if resp.status_code in [302, 303]:
            print("    [+] SUCCESS - CSRF method works!")
            return session
    
    # Method 3: JSON (expected to fail)
    print("\n[3] Testing JSON (should fail)...")
    session = requests.Session()
    
    resp = session.post(
        f'{base_url}/login',
        json=login_data,
        allow_redirects=False
    )
    
    print(f"    Response: {resp.status_code}")
    if resp.status_code == 400:
        print("    [Expected] JSON fails with 400")
    
    return
def test_api_after_login(session):
    """Test API endpoints after login"""
    
    print("\n[*] Testing API endpoints...")
    
    # Test connections endpoint
    resp = session.get('http://localhost:5000/api/connections')
    print(f"  /api/connections: {resp.status_code}")
    
    if resp.status_code == 200:
        connections = resp.json()
        print(f"    Found {len(connections)} connections")
    
    # Test server status
    resp = session.get('http://localhost:5000/api/server/status')
    print(f"  /api/server/status: {resp.status_code}")
    
    if resp.status_code == 200:
        status = resp.json()
        print(f"    Server listening: {status.get('listening')}")
        print(f"    Port: {status.get('port')}")
    
    return True

def create_fixed_test():
    """Create a fixed test that properly logs in"""
    
    test_code = '''#!/usr/bin/env python3
"""
Fixed web test with proper login
"""
import requests
import os

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securepassword123'

def test_web():
    session = requests.Session()
    
    # Login with form data (NOT JSON)
    login_data = {
        'username': os.environ['STITCH_ADMIN_USER'],
        'password': os.environ['STITCH_ADMIN_PASSWORD']
    }
    
    # Use form-encoded data
    resp = session.post(
        'http://localhost:5000/login',
        data=login_data,  # Form data, not json=
        allow_redirects=False
    )
    
    if resp.status_code in [302, 303]:
        print("[+] Login successful")
        
        # Test API
        resp = session.get('http://localhost:5000/api/connections')
        print(f"[+] API test: {resp.status_code}")
        return True
    else:
        print(f"[-] Login failed: {resp.status_code}")
        return False

if __name__ == "__main__":
    test_web()
'''
    
    with open('/workspace/test_web_fixed.py', 'w') as f:
        f.write(test_code)
    
    print("\n[+] Created fixed test: /workspace/test_web_fixed.py")

if __name__ == "__main__":
    print("="*70)
    print("WEB LOGIN FIX TESTING")
    print("="*70)
    
    # Start server
    server_proc = start_web_server()
    
    if server_proc:
        try:
            # Test login methods
            session = test_login_methods()
            
            if session:
                # Test API
                test_api_after_login(session)
                
                # Create fixed test
                create_fixed_test()
                
                print("\n" + "="*70)
                print("SOLUTION FOUND")
                print("="*70)
                print("✓ Login works with form data (data=)")
                print("✗ Login fails with JSON (json=)")
                print("\nFix: Use data= parameter, not json=")
                print("Fix: Content-Type: application/x-www-form-urlencoded")
            else:
                print("\n[-] All login methods failed")
                
        finally:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except Exception:
                server_proc.kill()