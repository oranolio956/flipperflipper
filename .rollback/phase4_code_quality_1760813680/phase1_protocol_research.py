#!/usr/bin/env python3
"""
Phase 1.1: Deep Protocol Analysis
Research the Stitch C2 protocol to understand why handshake fails
"""

import os
import sys
import socket
import time
import subprocess
import struct
import base64
import threading

sys.path.insert(0, '/workspace')

class ProtocolAnalyzer:
    def __init__(self):
        self.findings = []
        
    def analyze_handshake_code(self):
        """Research the handshake implementation"""
        print("[RESEARCH] Analyzing handshake protocol...")
        
        # Check the actual handshake implementation
        from Application import stitch_lib
        import inspect
        
        # Get handshake related functions
        handshake_functions = []
        for name, obj in inspect.getmembers(stitch_lib):
            if 'handshake' in name.lower() or 'receive' in name.lower() or 'send' in name.lower():
                handshake_functions.append((name, obj))
        
        print(f"  Found {len(handshake_functions)} protocol functions")
        for name, obj in handshake_functions:
            print(f"    - {name}")
            
        self.findings.append(f"Protocol functions identified: {len(handshake_functions)}")
        
    def trace_actual_connection(self):
        """Trace a real connection to see protocol flow"""
        print("\n[RESEARCH] Tracing actual connection flow...")
        
        # Start a simple server to capture protocol
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('127.0.0.1', 9999))
        server_sock.listen(1)
        
        # Start a simple client
        def client():
            time.sleep(1)
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(('127.0.0.1', 9999))
            
            # Send what Stitch expects
            # Based on web_app_real.py line 1027: confirm = base64.b64encode(b'stitch_shell')
            client_sock.send(base64.b64encode(b'stitch_shell'))
            client_sock.send(b'\n')
            
            # Send AES ID
            client_sock.send(b'default\n')
            
            # Wait for response
            time.sleep(1)
            client_sock.close()
        
        client_thread = threading.Thread(target=client)
        client_thread.start()
        
        # Accept connection
        conn, addr = server_sock.accept()
        print(f"  Connection from: {addr}")
        
        # Read protocol messages
        messages = []
        conn.settimeout(2)
        
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                messages.append(data)
                print(f"  Received: {data[:50]}...")
        except socket.timeout:
            pass
        
        conn.close()
        server_sock.close()
        client_thread.join()
        
        self.findings.append(f"Protocol messages captured: {len(messages)}")
        
    def analyze_stitch_server_code(self):
        """Analyze the actual Stitch server implementation"""
        print("\n[RESEARCH] Analyzing Stitch server code...")
        
        # Read key server files
        server_files = [
            '/workspace/Application/stitch_cmd.py',
            '/workspace/Application/stitch_lib.py',
            '/workspace/web_app_real.py'
        ]
        
        protocol_patterns = []
        
        for filepath in server_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                # Look for protocol-related code
                if 'receive' in content and 'send' in content:
                    # Count protocol operations
                    receive_count = content.count('receive(')
                    send_count = content.count('send(')
                    protocol_patterns.append({
                        'file': os.path.basename(filepath),
                        'receives': receive_count,
                        'sends': send_count
                    })
        
        for pattern in protocol_patterns:
            print(f"  {pattern['file']}: {pattern['receives']} receives, {pattern['sends']} sends")
            
        self.findings.append(f"Protocol patterns found in {len(protocol_patterns)} files")
        
    def test_real_handshake(self):
        """Test the actual handshake with Stitch server"""
        print("\n[RESEARCH] Testing real handshake...")
        
        # Start Stitch server
        server_script = '''
import sys
sys.path.insert(0, '/workspace')
from Application.stitch_cmd import stitch_server

server = stitch_server()
server.do_listen('7777')

import time
time.sleep(10)
'''
        
        with open('/tmp/test_server.py', 'w') as f:
            f.write(server_script)
        
        server_proc = subprocess.Popen(
            ['python3', '/tmp/test_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        time.sleep(3)
        
        # Try to connect with proper protocol
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 7777))
            print("  Connected to Stitch server")
            
            # Send expected protocol
            # From research: expects base64 encoded 'stitch_shell'
            confirm = base64.b64encode(b'stitch_shell')
            sock.send(confirm + b'\n')
            print(f"  Sent confirmation: {confirm}")
            
            # Send AES ID
            sock.send(b'default\n')
            print("  Sent AES ID: default")
            
            # Try to receive response
            sock.settimeout(2)
            try:
                response = sock.recv(1024)
                print(f"  Server response: {response[:100]}")
                self.findings.append("Handshake response received")
            except socket.timeout:
                print("  No response from server")
                self.findings.append("Handshake timeout")
                
            sock.close()
            
        except Exception as e:
            print(f"  Connection error: {e}")
            self.findings.append(f"Connection failed: {e}")
            
        server_proc.terminate()
        
    def analyze_aes_implementation(self):
        """Research the AES encryption implementation"""
        print("\n[RESEARCH] Analyzing AES implementation...")
        
        # Check for AES library
        aes_lib_path = '/workspace/Application/Stitch_Vars/st_aes_lib.ini'
        
        if os.path.exists(aes_lib_path):
            import configparser
            config = configparser.ConfigParser()
            config.read(aes_lib_path)
            
            print(f"  AES keys found: {len(config.sections())}")
            for section in config.sections():
                print(f"    - {section}")
                
            self.findings.append(f"AES keys configured: {len(config.sections())}")
        else:
            print("  AES library not found")
            self.findings.append("AES library missing")
            
    def research_payload_requirements(self):
        """Research what payloads actually need"""
        print("\n[RESEARCH] Analyzing payload requirements...")
        
        # Check what the generated payloads import
        config_dir = '/workspace/Configuration'
        
        if os.path.exists(config_dir):
            py_files = [f for f in os.listdir(config_dir) if f.endswith('.py')]
            
            imports_needed = set()
            for pyfile in py_files:
                filepath = os.path.join(config_dir, pyfile)
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                # Find imports
                import_lines = [line for line in content.split('\n') if 'import' in line]
                for line in import_lines:
                    imports_needed.add(line.strip())
            
            print(f"  Unique imports required: {len(imports_needed)}")
            for imp in list(imports_needed)[:5]:
                print(f"    - {imp}")
                
            self.findings.append(f"Payload imports: {len(imports_needed)} unique")
            
    def generate_report(self):
        """Generate research findings report"""
        print("\n" + "="*70)
        print("PROTOCOL RESEARCH FINDINGS")
        print("="*70)
        
        for i, finding in enumerate(self.findings, 1):
            print(f"{i}. {finding}")
            
        print("\n[KEY INSIGHTS]")
        print("1. Handshake expects: base64('stitch_shell') + AES ID")
        print("2. AES encryption is required for communication")
        print("3. Multiple protocol functions handle send/receive")
        print("4. Payload needs proper imports and dependencies")
        
        return self.findings

def main():
    print("="*70)
    print("PHASE 1.1: PROTOCOL RESEARCH")
    print("="*70)
    
    analyzer = ProtocolAnalyzer()
    
    # Run all research methods
    analyzer.analyze_handshake_code()
    analyzer.trace_actual_connection()
    analyzer.analyze_stitch_server_code()
    analyzer.test_real_handshake()
    analyzer.analyze_aes_implementation()
    analyzer.research_payload_requirements()
    
    # Generate report
    findings = analyzer.generate_report()
    
    # Save findings
    with open('/workspace/phase1_findings.txt', 'w') as f:
        f.write("PHASE 1 PROTOCOL RESEARCH FINDINGS\n")
        f.write("="*50 + "\n")
        for finding in findings:
            f.write(f"- {finding}\n")
    
    print("\n[+] Research complete. Findings saved to phase1_findings.txt")

if __name__ == "__main__":
    main()