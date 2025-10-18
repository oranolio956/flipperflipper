#!/usr/bin/env python3
"""
Simple test of CSRF with API
"""

import os
import sys
import time
import subprocess
import requests
import re

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpass123456'  # 12+ chars

# Start server
print("[*] Starting server...")
server = subprocess.Popen(
    ['python3', 'web_app_real.py'],
    cwd='/workspace',
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    env=os.environ.copy()
)

time.sleep(8)

try:
    session = requests.Session()
    
    # Get login page
    print("[*] Getting CSRF token...")
    resp = session.get('http://localhost:5000/login')
    
    csrf_token = None
    if 'csrf_token' in resp.text:
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
            print(f"[+] Got CSRF: {csrf_token[:20]}...")
    
    # Login
    print("[*] Logging in...")
    login_data = {
        'username': 'admin',
        'password': 'testpass123456'
    }
    
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    resp = session.post(
        'http://localhost:5000/login',
        data=login_data,
        allow_redirects=False
    )
    
    print(f"[*] Login response: {resp.status_code}")
    
    if resp.status_code in [302, 303]:
        print("[+] Login successful")
        
        # Get dashboard for new CSRF
        resp = session.get('http://localhost:5000/')
        if 'csrf-token' in resp.text:
            match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
            if match:
                csrf_token = match.group(1)
                print(f"[+] Updated CSRF from dashboard")
        
        # Test API with CSRF
        print("\n[*] Testing API with CSRF...")
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }
        
        # Test connections endpoint
        resp = session.get(
            'http://localhost:5000/api/connections',
            headers={'X-CSRFToken': csrf_token}
        )
        
        print(f"  Connections API: {resp.status_code}")
        
        if resp.status_code == 200:
            conns = resp.json()
            print(f"  Found {len(conns)} connections")
        
        # Test payload generation
        payload_config = {
            'platform': 'python',
            'listen_host': '127.0.0.1',
            'listen_port': '4040',
            'enable_listen': True,
            'enable_bind': False,
            'bind_host': '',
            'bind_port': ''
        }
        
        resp = session.post(
            'http://localhost:5000/api/generate-payload',
            json=payload_config,
            headers=headers
        )
        
        print(f"  Generate Payload API: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success'):
                print(f"  [+] Payload generated: {result.get('payload_type')}")
            else:
                print(f"  [-] Failed: {result.get('error') or result.get('message')}")
        else:
            print(f"  [-] Error: {resp.text[:100]}")
        
        print("\n[+] APIs work with CSRF token!")
    
finally:
    server.terminate()
    server.wait(timeout=5)