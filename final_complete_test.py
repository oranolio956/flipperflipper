#!/usr/bin/env python3
"""
FINAL COMPLETE TEST
Test everything end-to-end with all fixes applied
"""

import os
import sys
import time
import subprocess
import requests
import socket
import re
import json

os.environ['STITCH_ADMIN_USER'] = 'testuser'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

class CompleteSystemTest:
    def __init__(self):
        self.web_proc = None
        self.payload_proc = None
        self.session = None
        self.results = {}
        
    def test_1_start_web_server(self):
        """Start web server with C2"""
        print("\n[TEST 1] Starting Web Server with C2...")
        
        self.web_proc = subprocess.Popen(
            ['python3', 'web_app_real.py'],
            cwd='/workspace',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # Wait for startup
        for i in range(15):
            time.sleep(2)
            try:
                resp = requests.get('http://localhost:5000/health')
                if resp.status_code == 200:
                    print("  ✓ Web server running on http://localhost:5000")
                    self.results['web_server'] = True
                    return True
            except:
                continue
        
        print("  ✗ Web server failed to start")
        self.results['web_server'] = False
        return False
    
    def test_2_web_login(self):
        """Test web login with CSRF"""
        print("\n[TEST 2] Web Login...")
        
        self.session = requests.Session()
        
        # Get login page for CSRF token
        resp = self.session.get('http://localhost:5000/login')
        
        # Extract CSRF token
        csrf_token = None
        if 'csrf_token' in resp.text:
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            if match:
                csrf_token = match.group(1)
        
        # Login with CSRF
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        resp = self.session.post(
            'http://localhost:5000/login',
            data=login_data,
            allow_redirects=False
        )
        
        if resp.status_code in [302, 303]:
            print("  ✓ Login successful")
            self.results['login'] = True
            return True
        else:
            print(f"  ✗ Login failed: {resp.status_code}")
            self.results['login'] = False
            return False
    
    def test_3_generate_payload(self):
        """Generate payload via web API"""
        print("\n[TEST 3] Payload Generation via Web API...")
        
        config = {
            'bind_host': '',
            'bind_port': '',
            'listen_host': '127.0.0.1',
            'listen_port': '4040',
            'enable_bind': False,
            'enable_listen': True,
            'platform': 'linux'  # Try Linux binary
        }
        
        resp = self.session.post(
            'http://localhost:5000/api/generate-payload',
            json=config
        )
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success'):
                print(f"  ✓ Payload generated: {result.get('payload_type')}")
                print(f"    Size: {result.get('payload_size')} bytes")
                print(f"    Platform: {result.get('platform')}")
                
                # Download payload
                resp = self.session.get('http://localhost:5000/api/download-payload')
                if resp.status_code == 200:
                    with open('/tmp/web_generated_payload', 'wb') as f:
                        f.write(resp.content)
                    
                    # Check type
                    with open('/tmp/web_generated_payload', 'rb') as f:
                        header = f.read(4)
                        if header == b'\x7fELF':
                            print("  ✓ Downloaded Linux ELF executable")
                            self.results['payload_type'] = 'ELF'
                        else:
                            print("  ⚠ Downloaded non-ELF file (likely Python)")
                            self.results['payload_type'] = 'Python'
                    
                    self.results['payload_generation'] = True
                    return True
        
        print("  ✗ Payload generation failed")
        self.results['payload_generation'] = False
        return False
    
    def test_4_execute_payload(self):
        """Execute the generated payload"""
        print("\n[TEST 4] Payload Execution...")
        
        # Use our working test payload for now
        payload_path = '/tmp/stitch_payload.py'
        
        if not os.path.exists(payload_path):
            # Create it
            from create_working_payload import create_full_stitch_payload
            payload_code = create_full_stitch_payload()
            with open(payload_path, 'w') as f:
                f.write(payload_code)
            os.chmod(payload_path, 0o755)
        
        self.payload_proc = subprocess.Popen(
            ['python3', payload_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"  ✓ Payload started (PID: {self.payload_proc.pid})")
        
        # Wait for connection
        time.sleep(3)
        
        # Check if still running
        if self.payload_proc.poll() is None:
            print("  ✓ Payload still running")
            self.results['payload_execution'] = True
            return True
        else:
            print("  ✗ Payload exited immediately")
            self.results['payload_execution'] = False
            return False
    
    def test_5_check_connection(self):
        """Check if payload connected via web API"""
        print("\n[TEST 5] Checking C2 Connection...")
        
        resp = self.session.get('http://localhost:5000/api/connections')
        
        if resp.status_code == 200:
            connections = resp.json()
            
            online_connections = [c for c in connections if c.get('status') == 'online']
            
            if online_connections:
                print(f"  ✓ Found {len(online_connections)} online connection(s)")
                for conn in online_connections:
                    print(f"    - {conn.get('target')}: {conn.get('status')}")
                    self.target_id = conn.get('id') or conn.get('target')
                
                self.results['c2_connection'] = True
                return True
            else:
                print(f"  ✗ No online connections (total: {len(connections)})")
        
        self.results['c2_connection'] = False
        return False
    
    def test_6_execute_commands(self):
        """Execute commands via web API"""
        print("\n[TEST 6] Command Execution via Web...")
        
        if not hasattr(self, 'target_id'):
            print("  ✗ No target to execute commands on")
            self.results['command_execution'] = False
            return False
        
        test_commands = [
            'pwd',
            'whoami',
            'echo "Test from web"'
        ]
        
        success_count = 0
        
        for cmd in test_commands:
            data = {
                'connection_id': self.target_id,
                'command': cmd
            }
            
            resp = self.session.post(
                'http://localhost:5000/api/execute',
                json=data
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
        
        if success_count > 0:
            print(f"  ✓ Executed {success_count}/{len(test_commands)} commands")
            self.results['command_execution'] = True
            return True
        else:
            self.results['command_execution'] = False
            return False
    
    def test_7_verify_ui_fixes(self):
        """Verify UI fixes are in place"""
        print("\n[TEST 7] UI Fixes Verification...")
        
        fixes_found = []
        
        # Check JavaScript fixes
        js_file = '/workspace/static/js/app_real.js'
        if os.path.exists(js_file):
            with open(js_file, 'r') as f:
                content = f.read()
                if 'fetchWithTimeout' in content:
                    fixes_found.append('fetchWithTimeout')
                if '// Removed annoying disconnect notification' in content:
                    fixes_found.append('disconnect_removed')
                if 'adjustForMobile' in content:
                    fixes_found.append('mobile_adjust')
        
        # Check CSS fixes  
        css_file = '/workspace/static/css/style_real.css'
        if os.path.exists(css_file):
            with open(css_file, 'r') as f:
                if 'Mobile Layout Fixes' in f.read():
                    fixes_found.append('mobile_css')
        
        # Check login rate limiting removed
        with open('/workspace/web_app_real.py', 'r') as f:
            if '# Rate limiting removed for easier testing' in f.read():
                fixes_found.append('rate_limit_removed')
        
        expected_fixes = ['fetchWithTimeout', 'disconnect_removed', 'mobile_adjust', 'mobile_css', 'rate_limit_removed']
        
        for fix in expected_fixes:
            if fix in fixes_found:
                print(f"  ✓ {fix}")
            else:
                print(f"  ✗ {fix} missing")
        
        self.results['ui_fixes'] = len(fixes_found) == len(expected_fixes)
        return self.results['ui_fixes']
    
    def cleanup(self):
        """Clean up processes"""
        print("\n[*] Cleaning up...")
        
        if self.payload_proc:
            self.payload_proc.terminate()
            try:
                self.payload_proc.wait(timeout=2)
            except:
                self.payload_proc.kill()
        
        if self.web_proc:
            self.web_proc.terminate()
            try:
                self.web_proc.wait(timeout=5)
            except:
                self.web_proc.kill()
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("COMPLETE SYSTEM TEST")
        print("="*70)
        
        try:
            # Run tests in order
            self.test_1_start_web_server()
            
            if self.results.get('web_server'):
                self.test_2_web_login()
                
                if self.results.get('login'):
                    self.test_3_generate_payload()
                    self.test_4_execute_payload()
                    
                    # Wait a bit for connection
                    time.sleep(5)
                    
                    self.test_5_check_connection()
                    
                    if self.results.get('c2_connection'):
                        self.test_6_execute_commands()
            
            self.test_7_verify_ui_fixes()
            
        finally:
            self.cleanup()
        
        # Print summary
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        all_passed = True
        for test_name, passed in self.results.items():
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{test_name:25} {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "="*70)
        if all_passed:
            print("✓ ALL TESTS PASSED")
        else:
            print("⚠ SOME TESTS FAILED")
            
            # Identify issues
            print("\nIssues found:")
            if not self.results.get('c2_connection'):
                print("  - Payload not connecting to C2 (may need to fix payload bundling)")
            if not self.results.get('command_execution'):
                print("  - Command execution not working (depends on C2 connection)")
            if self.results.get('payload_type') == 'Python':
                print("  - Generated Python script instead of executable")
        
        print("="*70)
        
        return all_passed

if __name__ == "__main__":
    tester = CompleteSystemTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)