#!/usr/bin/env python3
"""
Live Testing Suite - No simulations
Tests all implemented features with real execution
"""

import os
import sys
import subprocess
import time
import socket
import requests
import json
import base64

sys.path.insert(0, '/workspace')

class LiveTestSuite:
    def __init__(self):
        self.test_results = {}
        
    def test_obfuscation(self):
        """Test payload obfuscation"""
        print("[TEST] Testing obfuscation...")
        
        try:
            import payload_obfuscator
            
            # Create test script
            test_code = 'print("Hello from payload")'
            
            # Obfuscate it
            obfuscated = payload_obfuscator.obfuscate_code(test_code)
            
            # Try to execute obfuscated code
            exec_result = subprocess.run(
                ['python3', '-c', obfuscated],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            success = 'Hello from payload' in exec_result.stdout
            self.test_results['obfuscation'] = success
            
            print(f"  {'✓' if success else '✗'} Obfuscation works")
            
            return success
            
        except Exception as e:
            print(f"  ✗ Obfuscation failed: {e}")
            self.test_results['obfuscation'] = False
            return False
            
    def test_api_endpoints(self):
        """Test new API endpoints"""
        print("[TEST] Testing API endpoints...")
        
        # Start test server
        server_script = """
import sys
sys.path.insert(0, '/workspace')
from web_app_real import app
app.run(port=8888, debug=False)
"""
        
        with open('/tmp/test_server.py', 'w') as f:
            f.write(server_script)
            
        proc = subprocess.Popen(
            ['python3', '/tmp/test_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(3)
        
        try:
            # Test system-info endpoint
            resp = requests.get('http://localhost:8888/api/system-info')
            
            success = resp.status_code in [200, 401]  # 401 if auth required
            self.test_results['api_endpoints'] = success
            
            print(f"  {'✓' if success else '✗'} API endpoints respond")
            
        except Exception as e:
            print(f"  ✗ API test failed: {e}")
            self.test_results['api_endpoints'] = False
            
        finally:
            proc.terminate()
            
        return self.test_results.get('api_endpoints', False)
        
    def test_encryption(self):
        """Test AES encryption"""
        print("[TEST] Testing encryption...")
        
        try:
            from Configuration.st_encryption import StitchEncryption
            
            # Create encryptor
            enc = StitchEncryption('test_key')
            
            # Test data
            plaintext = "Secret message for testing"
            
            # Encrypt
            encrypted = enc.encrypt(plaintext)
            
            # Decrypt
            decrypted = enc.decrypt(encrypted)
            
            success = decrypted == plaintext
            self.test_results['encryption'] = success
            
            print(f"  {'✓' if success else '✗'} Encryption works: {decrypted[:20]}...")
            
            return success
            
        except Exception as e:
            print(f"  ✗ Encryption failed: {e}")
            self.test_results['encryption'] = False
            return False
            
    def test_payload_modules(self):
        """Test payload modules"""
        print("[TEST] Testing payload modules...")
        
        modules_ok = []
        
        # Test persistence module
        try:
            from Configuration import st_persistence
            modules_ok.append('persistence')
            print("  ✓ Persistence module loads")
        except:
            print("  ✗ Persistence module failed")
            
        # Test screenshot module
        try:
            from Configuration import st_screenshot
            # Don't actually take screenshot, just verify import
            modules_ok.append('screenshot')
            print("  ✓ Screenshot module loads")
        except:
            print("  ✗ Screenshot module failed")
            
        self.test_results['payload_modules'] = len(modules_ok) >= 1
        
        return len(modules_ok) >= 1
        
    def run_all_tests(self):
        """Run all live tests"""
        print("="*70)
        print("LIVE TESTING SUITE")
        print("="*70)
        
        tests = [
            ('Obfuscation', self.test_obfuscation),
            ('API Endpoints', self.test_api_endpoints),
            ('Encryption', self.test_encryption),
            ('Payload Modules', self.test_payload_modules)
        ]
        
        for test_name, test_func in tests:
            print(f"\nRunning: {test_name}")
            try:
                test_func()
            except Exception as e:
                print(f"  Test error: {e}")
                self.test_results[test_name.lower()] = False
                
        # Summary
        print("\n" + "="*70)
        print("TEST RESULTS")
        print("="*70)
        
        passed = sum(1 for v in self.test_results.values() if v)
        total = len(self.test_results)
        
        for test, result in self.test_results.items():
            print(f"  {'✓' if result else '✗'} {test}")
            
        print(f"\nTotal: {passed}/{total} passed")
        
        return passed == total

if __name__ == "__main__":
    suite = LiveTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
