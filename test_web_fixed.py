#!/usr/bin/env python3
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
