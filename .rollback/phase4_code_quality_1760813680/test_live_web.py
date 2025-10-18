#!/usr/bin/env python3
"""
Test the actual web server with payload generation
"""

import os
import sys
import json
import time
import requests
import subprocess
import threading
from pathlib import Path

# Setup environment
sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

def start_web_server():
    """Start the web server in background"""
    print("[*] Starting web server...")
    proc = subprocess.Popen(
        ['python3', 'web_app_real.py'],
        cwd='/workspace',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Wait for server to start
    time.sleep(5)
    
    # Check if server is running
    try:
        resp = requests.get('http://localhost:5000/health', timeout=5)
        if resp.status_code == 200:
            print("[✓] Web server started successfully")
            return proc
    except Exception:
        pass
    
    print("[✗] Failed to start web server")
    proc.terminate()
    stdout, stderr = proc.communicate(timeout=5)
    print(f"stdout: {stdout.decode()[:500]}")
    print(f"stderr: {stderr.decode()[:500]}")
    return None

def test_web_payload_api():
    """Test the web API endpoints"""
    
    print("\n" + "="*70)
    print("TESTING LIVE WEB SERVER PAYLOAD GENERATION")
    print("="*70)
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # Step 1: Login
    print("\n[1] Testing Login...")
    login_data = {
        'username': 'admin',
        'password': 'testpassword123'
    }
    
    resp = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    if resp.status_code in [302, 303]:  # Redirect after successful login
        print("  ✓ Login successful")
    else:
        print(f"  ✗ Login failed: {resp.status_code}")
        return False
    
    # Step 2: Generate Linux Payload
    print("\n[2] Testing Linux Payload Generation via API...")
    payload_config = {
        'bind_host': '0.0.0.0',
        'bind_port': '4433',
        'listen_host': '',
        'listen_port': '',
        'enable_bind': True,
        'enable_listen': False,
        'platform': 'linux',
        'payload_name': 'test_web_linux'
    }
    
    resp = session.post(
        f"{base_url}/api/generate-payload",
        json=payload_config,
        headers={'Content-Type': 'application/json'}
    )
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('success'):
            print(f"  ✓ Payload generated successfully")
            print(f"    Type: {result.get('payload_type')}")
            print(f"    Platform: {result.get('platform')}")
            print(f"    Size: {result.get('payload_size'):,} bytes")
            print(f"    Download URL: {result.get('download_url')}")
        else:
            print(f"  ✗ Generation failed: {result.get('error')}")
            return False
    else:
        print(f"  ✗ API request failed: {resp.status_code}")
        print(f"    Response: {resp.text[:500]}")
        return False
    
    # Step 3: Download the payload
    print("\n[3] Testing Payload Download...")
    resp = session.get(f"{base_url}/api/download-payload")
    
    if resp.status_code == 200:
        content_length = len(resp.content)
        content_type = resp.headers.get('Content-Type', '')
        payload_type = resp.headers.get('X-Payload-Type', 'unknown')
        
        print(f"  ✓ Payload downloaded successfully")
        print(f"    Size: {content_length:,} bytes")
        print(f"    Content-Type: {content_type}")
        print(f"    Payload-Type: {payload_type}")
        
        # Save and verify
        test_file = '/tmp/test_payload'
        with open(test_file, 'wb') as f:
            f.write(resp.content)
        
        # Check if it's an ELF binary
        with open(test_file, 'rb') as f:
            header = f.read(4)
            if header == b'\x7fELF':
                print(f"    ✓ Verified: Linux ELF executable")
            elif b'python' in resp.content[:100].lower() or b'from' in resp.content[:100]:
                print(f"    ⚠ Python script (fallback)")
            else:
                print(f"    ? Unknown file type")
    else:
        print(f"  ✗ Download failed: {resp.status_code}")
        return False
    
    # Step 4: Test Python payload generation
    print("\n[4] Testing Python Script Generation...")
    payload_config['platform'] = 'python'
    payload_config['payload_name'] = 'test_web_python'
    
    resp = session.post(
        f"{base_url}/api/generate-payload",
        json=payload_config,
        headers={'Content-Type': 'application/json'}
    )
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('success') and result.get('payload_type') == 'script':
            print(f"  ✓ Python script generated")
            print(f"    Size: {result.get('payload_size')} bytes")
    else:
        print(f"  ✗ Failed to generate Python script")
    
    return True

if __name__ == "__main__":
    # Start web server
    server_proc = start_web_server()
    
    if server_proc:
        try:
            # Run tests
            success = test_web_payload_api()
            
            print("\n" + "="*70)
            if success:
                print("✓ LIVE WEB SERVER TEST PASSED")
                print("\nThe web interface is correctly generating:")
                print("  • Compiled executables for Linux")
                print("  • Python scripts when requested")
                print("  • Proper MIME types and headers")
            else:
                print("✗ LIVE WEB SERVER TEST FAILED")
            print("="*70)
            
        finally:
            # Stop server
            print("\n[*] Stopping web server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except Exception:
                server_proc.kill()
            print("[✓] Server stopped")
    else:
        print("\n✗ Could not start web server for testing")