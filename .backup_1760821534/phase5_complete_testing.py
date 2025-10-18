#!/usr/bin/env python3
"""
Phase 5: Complete End-to-End Testing
Full live environment testing with no simulations
"""

import os
import sys
import time
import json
import socket
import requests
import subprocess
import threading
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/workspace')

class CompleteSystemTester:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'errors': [],
            'warnings': []
        }
        self.processes = {}
        
    def start_c2_server(self):
        """Start the C2 server"""
        print("\n[C2 SERVER] Starting...")
        
        # Kill any existing servers
        subprocess.run("pkill -f 'python.*stitch' 2>/dev/null", shell=True, capture_output=True)
        time.sleep(2)
        
        # Create server script
        server_script = '''
import sys
import os
sys.path.insert(0, '/workspace')

# Set environment
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'test123'

from Application.stitch_cmd import stitch_server

print("[C2] Initializing server...")
server = stitch_server()

# Start listening
server.do_listen('4040')
print("[C2] Server listening on port 4040")

# Keep running
import time
    # TODO: Review - infinite loop may need exit condition
while True:
    time.sleep(1)
    # Check for connections
    if hasattr(server, 'inf_sock') and server.inf_sock:
        print(f"[C2] Active connections: {len(server.inf_sock)}")
'''
        
        with open('/tmp/c2_server.py', 'w') as f:
            f.write(server_script)
        
        # Start server
        proc = subprocess.Popen(
            ['python3', '/tmp/c2_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        self.processes['c2_server'] = proc
        
        # Wait for server to start
        time.sleep(3)
        
        # Verify listening
        sock = socket.socket()
        result = sock.connect_ex(('127.0.0.1', 4040))
        sock.close()
        
        success = result == 0
        self.results['tests']['c2_server'] = {
            'status': 'SUCCESS' if success else 'FAILED',
            'port': 4040,
            'pid': proc.pid
        }
        
        print(f"  Status: {'✓ Running' if success else '✗ Failed'}")
        return success
    
    def start_web_interface(self):
        """Start the web interface"""
        print("\n[WEB INTERFACE] Starting...")
        
        # Kill existing web servers
        subprocess.run("pkill -f 'web_app_real' 2>/dev/null", shell=True, capture_output=True)
        time.sleep(2)
        
        # Create web script
        web_script = '''
import sys
import os
sys.path.insert(0, '/workspace')

# Set environment
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'test123'
os.environ['STITCH_CSRF_SSL_STRICT'] = 'False'

from web_app_real import app, socketio

print("[Web] Starting web interface on port 5000...")

# Run Flask app
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
        
        with open('/tmp/web_server.py', 'w') as f:
            f.write(web_script)
        
        # Start web server
        proc = subprocess.Popen(
            ['python3', '/tmp/web_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        self.processes['web_server'] = proc
        
        # Wait for web to start
        time.sleep(5)
        
        # Test if running
        try:
            resp = requests.get('http://localhost:5000/health', timeout=2)
            success = resp.status_code == 200
        except Exception:
            success = False
        
        self.results['tests']['web_interface'] = {
            'status': 'SUCCESS' if success else 'FAILED',
            'port': 5000,
            'pid': proc.pid
        }
        
        print(f"  Status: {'✓ Running' if success else '✗ Failed'}")
        return success
    
    def test_web_login(self):
        """Test web login"""
        print("\n[WEB LOGIN] Testing...")
        
        session = requests.Session()
        
        try:
            # Get login page
            resp = session.get('http://localhost:5000/login')
            
            # Extract CSRF token
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            
            if not csrf_match:
                print("  ✗ No CSRF token found")
                self.results['tests']['web_login'] = {'status': 'FAILED', 'error': 'No CSRF token'}
                return False
            
            csrf_token = csrf_match.group(1)
            
            # Login
            login_data = {
                'username': 'admin',
                'password': 'test123',
                'csrf_token': csrf_token
            }
            
            resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
            
            success = resp.status_code in [302, 303]
            
            self.results['tests']['web_login'] = {
                'status': 'SUCCESS' if success else 'FAILED',
                'response_code': resp.status_code
            }
            
            print(f"  Status: {'✓ Logged in' if success else '✗ Failed'}")
            
            if success:
                # Save session for further tests
                self.session = session
                # Get CSRF for API calls
                resp = session.get('http://localhost:5000/')
                csrf_match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
                    
            return success
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['tests']['web_login'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def test_payload_generation(self):
        """Test payload generation via web"""
        print("\n[PAYLOAD GENERATION] Testing...")
        
        if not hasattr(self, 'session'):
            print("  ✗ Not logged in")
            self.results['tests']['payload_generation'] = {'status': 'SKIPPED'}
            return False
        
        try:
            headers = {'X-CSRFToken': self.csrf_token}
            
            payload_config = {
                'platform': 'linux',
                'host': '127.0.0.1',
                'port': '4040',
                'name': 'test_payload'
            }
            
            resp = self.session.post(
                'http://localhost:5000/api/generate-payload',
                json=payload_config,
                headers=headers
            )
            
            if resp.status_code == 200:
                result = resp.json()
                
                self.results['tests']['payload_generation'] = {
                    'status': 'SUCCESS',
                    'payload_type': result.get('type'),
                    'payload_size': result.get('size'),
                    'download_url': result.get('download_url')
                }
                
                print(f"  ✓ Generated: {result.get('type')} ({result.get('size')} bytes)")
                
                # Download payload
                if result.get('download_url'):
                    dl_resp = self.session.get(f"http://localhost:5000{result['download_url']}")
                    
                    if dl_resp.status_code == 200:
                        # Save payload
                        payload_path = '/tmp/generated_payload'
                        with open(payload_path, 'wb') as f:
                            f.write(dl_resp.content)
                        
                        # Check payload type from headers
                        payload_type = dl_resp.headers.get('X-Payload-Type', 'unknown')
                        
                        if payload_type == 'python':
                            payload_path = f'{payload_path}.py'
                            os.rename('/tmp/generated_payload', payload_path)
                        
                        os.chmod(payload_path, 0o755)
                        
                        print(f"  ✓ Downloaded: {payload_path}")
                        self.generated_payload = payload_path
                        
                        return True
                        
            print(f"  ✗ Generation failed: {resp.status_code}")
            self.results['tests']['payload_generation']['status'] = 'FAILED'
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['tests']['payload_generation'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def test_payload_execution(self):
        """Test executing generated payload"""
        print("\n[PAYLOAD EXECUTION] Testing...")
        
        if not hasattr(self, 'generated_payload'):
            print("  ✗ No payload generated")
            self.results['tests']['payload_execution'] = {'status': 'SKIPPED'}
            return False
        
        try:
            # Determine how to run payload
            if self.generated_payload.endswith('.py'):
                cmd = ['python3', self.generated_payload]
            else:
                cmd = [self.generated_payload]
            
            # Start payload
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            self.processes['payload'] = proc
            
            # Give it time to connect
            time.sleep(3)
            
            # Check if still running
            if proc.poll() is None:
                print(f"  ✓ Payload running (PID: {proc.pid})")
                
                self.results['tests']['payload_execution'] = {
                    'status': 'SUCCESS',
                    'pid': proc.pid,
                    'type': 'python' if '.py' in self.generated_payload else 'binary'
                }
                
                return True
            else:
                print("  ✗ Payload exited")
                stdout, _ = proc.communicate()
                print(f"  Output: {stdout[:200]}")
                
                self.results['tests']['payload_execution'] = {
                    'status': 'FAILED',
                    'exit_code': proc.returncode,
                    'output': stdout[:500]
                }
                
                return False
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['tests']['payload_execution'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def test_c2_connection(self):
        """Test if payload connected to C2"""
        print("\n[C2 CONNECTION] Testing...")
        
        try:
            # Check via web API
            if hasattr(self, 'session'):
                headers = {'X-CSRFToken': self.csrf_token}
                resp = self.session.get('http://localhost:5000/api/connections', headers=headers)
                
                if resp.status_code == 200:
                    connections = resp.json()
                    
                    if connections:
                        print(f"  ✓ {len(connections)} active connections")
                        
                        self.results['tests']['c2_connection'] = {
                            'status': 'SUCCESS',
                            'count': len(connections),
                            'connections': connections
                        }
                        
                        return True
                    else:
                        print("  ✗ No active connections")
                        self.results['tests']['c2_connection'] = {
                            'status': 'FAILED',
                            'count': 0
                        }
                        
                        return False
                        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['tests']['c2_connection'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def test_command_execution(self):
        """Test executing commands on payload"""
        print("\n[COMMAND EXECUTION] Testing...")
        
        if not hasattr(self, 'session'):
            print("  ✗ Not logged in")
            self.results['tests']['command_execution'] = {'status': 'SKIPPED'}
            return False
        
        try:
            headers = {'X-CSRFToken': self.csrf_token}
            
            # Test commands
            test_commands = [
                {'command': 'whoami', 'expected': 'output'},
                {'command': 'pwd', 'expected': '/'},
                {'command': 'echo test123', 'expected': 'test123'}
            ]
            
            results = []
            
            for test in test_commands:
                cmd_data = {
                    'target': '127.0.0.1',
                    'command': test['command']
                }
                
                resp = self.session.post(
                    'http://localhost:5000/api/execute',
                    json=cmd_data,
                    headers=headers
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    output = result.get('output', '')
                    
                    success = test['expected'] in output if test['expected'] else bool(output)
                    
                    results.append({
                        'command': test['command'],
                        'success': success,
                        'output': output[:100]
                    })
                    
                    print(f"  {'✓' if success else '✗'} {test['command']}: {output[:50]}")
                else:
                    results.append({
                        'command': test['command'],
                        'success': False,
                        'error': f"HTTP {resp.status_code}"
                    })
                    
                    print(f"  ✗ {test['command']}: Failed")
            
            # Overall success
            success = any(r['success'] for r in results)
            
            self.results['tests']['command_execution'] = {
                'status': 'SUCCESS' if success else 'FAILED',
                'commands': results
            }
            
            return success
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['tests']['command_execution'] = {'status': 'ERROR', 'error': str(e)}
            return False
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n[CLEANUP] Terminating processes...")
        
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                print(f"  Terminating {name} (PID: {proc.pid})")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("COMPLETE SYSTEM TEST REPORT")
        print("="*70)
        
        # Summary
        total_tests = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'].values() if t.get('status') == 'SUCCESS')
        failed = sum(1 for t in self.results['tests'].values() if t.get('status') == 'FAILED')
        errors = sum(1 for t in self.results['tests'].values() if t.get('status') == 'ERROR')
        skipped = sum(1 for t in self.results['tests'].values() if t.get('status') == 'SKIPPED')
        
        print(f"\n[SUMMARY]")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✓ Passed: {passed}")
        print(f"  ✗ Failed: {failed}")
        print(f"  ⚠ Errors: {errors}")
        print(f"  ⊘ Skipped: {skipped}")
        
        print(f"\n[TEST RESULTS]")
        for test_name, result in self.results['tests'].items():
            status = result.get('status', 'UNKNOWN')
            symbol = '✓' if status == 'SUCCESS' else '✗' if status == 'FAILED' else '⚠'
            print(f"  {symbol} {test_name}: {status}")
            
            # Show details for failures
            if status != 'SUCCESS' and 'error' in result:
                print(f"     Error: {result['error']}")
        
        # Save full report
        report_path = '/workspace/phase5_test_results.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n[+] Full report saved to {report_path}")
        
        # Overall status
        if passed == total_tests:
            print("\n✅ ALL TESTS PASSED - SYSTEM FULLY FUNCTIONAL")
        elif passed > failed:
            print("\n⚠️  PARTIAL SUCCESS - SOME FEATURES WORKING")
        else:
            print("\n❌ CRITICAL FAILURES - MAJOR ISSUES DETECTED")
        
        return passed == total_tests

def main():
    print("="*70)
    print("PHASE 5: COMPLETE END-TO-END TESTING")
    print("="*70)
    print("Running live environment tests - NO SIMULATIONS")
    
    tester = CompleteSystemTester()
    
    try:
        # Run all tests in sequence
        tests = [
            ('C2 Server', tester.start_c2_server),
            ('Web Interface', tester.start_web_interface),
            ('Web Login', tester.test_web_login),
            ('Payload Generation', tester.test_payload_generation),
            ('Payload Execution', tester.test_payload_execution),
            ('C2 Connection', tester.test_c2_connection),
            ('Command Execution', tester.test_command_execution)
        ]
        
        for test_name, test_func in tests:
            if not test_func():
                print(f"\n⚠️  {test_name} failed - continuing with other tests...")
        
        # Generate report
        all_passed = tester.generate_report()
        
        return all_passed
        
    finally:
        # Always cleanup
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)