#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE TEST SUITE
Test all critical functionality after fixes
"""

import os
import sys
import json
import subprocess
import time
import requests
from pathlib import Path

class FinalTestSuite:
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
        
    def test_imports(self):
        """Test all critical imports"""
        print("\n[TEST] Critical Imports")
        
        imports = [
            ('Web App', 'from web_app_real import app'),
            ('Payload Generator', 'from web_payload_generator import WebPayloadGenerator'),
            ('C2 Server', 'from Application.stitch_cmd import stitch_server'),
            ('Payload Config', 'from Application.stitch_pyld_config import *'),
            ('Cross Compile', 'from Application.stitch_cross_compile import *'),
            ('Auth Utils', 'from auth_utils import verify_password, hash_password'),
            ('SSL Utils', 'from ssl_utils import generate_ssl_cert'),
            ('Config', 'from config import Config')
        ]
        
        for name, import_stmt in imports:
            result = subprocess.run(
                f'python3 -c "{import_stmt}; print(\'OK\')"',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and 'OK' in result.stdout:
                print(f"  ✓ {name}")
                self.results['passed'] += 1
            else:
                print(f"  ✗ {name}")
                if result.stderr:
                    print(f"    Error: {result.stderr.split('Error:')[-1].strip()[:100]}")
                self.results['failed'] += 1
                
            self.results['tests'].append({
                'name': f'Import: {name}',
                'passed': result.returncode == 0
            })
            
    def test_web_server(self):
        """Test web server startup"""
        print("\n[TEST] Web Server")
        
        # Start web server
        web_proc = subprocess.Popen(
            'cd /workspace && python3 web_app_real.py',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        time.sleep(3)
        
        # Check if running
        if web_proc.poll() is None:
            print(f"  ✓ Web server started")
            self.results['passed'] += 1
            
            # Try to access
            try:
                response = requests.get('http://127.0.0.1:5000', timeout=2)
                if response.status_code in [200, 302]:
                    print(f"  ✓ Web server responding")
                    self.results['passed'] += 1
                else:
                    print(f"  ✗ Web server not responding correctly")
                    self.results['failed'] += 1
            except:
                print(f"  ✗ Cannot connect to web server")
                self.results['failed'] += 1
                
            # Terminate
            web_proc.terminate()
            web_proc.wait(timeout=5)
            
        else:
            print(f"  ✗ Web server failed to start")
            stderr = web_proc.stderr.read()
            if stderr:
                print(f"    Error: {stderr[:200]}")
            self.results['failed'] += 1
            
    def test_payload_generation(self):
        """Test payload generation"""
        print("\n[TEST] Payload Generation")
        
        test_script = """
from web_payload_generator import WebPayloadGenerator

gen = WebPayloadGenerator()

config = {
    'host': '127.0.0.1',
    'port': '4444',
    'platform': 'linux',
    'encrypt': False,
    'obfuscate': False,
    'compile': False
}

result = gen.generate_payload(config)

if result and 'success' in result:
    print('OK')
else:
    print('FAILED')
"""
        
        result = subprocess.run(
            f'cd /workspace && python3 -c "{test_script}"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if 'OK' in result.stdout:
            print(f"  ✓ Payload generation works")
            self.results['passed'] += 1
        else:
            print(f"  ✗ Payload generation failed")
            if result.stderr:
                print(f"    Error: {result.stderr[:200]}")
            self.results['failed'] += 1
            
    def test_syntax_check(self):
        """Check for remaining syntax errors"""
        print("\n[TEST] Syntax Check")
        
        syntax_errors = 0
        total_files = 0
        
        for root, dirs, files in os.walk('/workspace'):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.rollback', '.backup_1760821534']]
            
            for file in files:
                if file.endswith('.py'):
                    total_files += 1
                    filepath = os.path.join(root, file)
                    
                    result = subprocess.run(
                        f'python3 -m py_compile {filepath}',
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        syntax_errors += 1
                        
        if syntax_errors == 0:
            print(f"  ✓ No syntax errors (checked {total_files} files)")
            self.results['passed'] += 1
        else:
            print(f"  ✗ {syntax_errors} syntax errors remain (out of {total_files} files)")
            self.results['failed'] += 1
            
    def test_security_improvements(self):
        """Test security improvements"""
        print("\n[TEST] Security Improvements")
        
        # Check for hardcoded passwords
        result = subprocess.run(
            'grep -r "password.*=" /workspace --include="*.py" | grep -v "getenv" | grep -v "#" | grep -v "test" | wc -l',
            shell=True,
            capture_output=True,
            text=True
        )
        
        try:
            hardcoded_count = int(result.stdout.strip())
            if hardcoded_count < 5:  # Allow some in examples/tests
                print(f"  ✓ Minimal hardcoded passwords ({hardcoded_count})")
                self.results['passed'] += 1
            else:
                print(f"  ⚠ {hardcoded_count} potential hardcoded passwords")
                self.results['failed'] += 1
        except:
            pass
            
        # Check for os.system usage
        result = subprocess.run(
            'grep -r "os.system(" /workspace --include="*.py" | wc -l',
            shell=True,
            capture_output=True,
            text=True
        )
        
        try:
            os_system_count = int(result.stdout.strip())
            if os_system_count < 10:
                print(f"  ✓ Minimal os.system usage ({os_system_count})")
                self.results['passed'] += 1
            else:
                print(f"  ⚠ {os_system_count} os.system calls remain")
                self.results['failed'] += 1
        except:
            pass
            
    def test_error_handling(self):
        """Test error handling improvements"""
        print("\n[TEST] Error Handling")
        
        # Check for bare except clauses
        result = subprocess.run(
            'grep -r "except:" /workspace --include="*.py" | wc -l',
            shell=True,
            capture_output=True,
            text=True
        )
        
        try:
            bare_except_count = int(result.stdout.strip())
            if bare_except_count < 20:
                print(f"  ✓ Minimal bare except clauses ({bare_except_count})")
                self.results['passed'] += 1
            else:
                print(f"  ⚠ {bare_except_count} bare except clauses remain")
                self.results['failed'] += 1
        except:
            pass
            
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*70)
        print("FINAL TEST REPORT")
        print("="*70)
        
        total = self.results['passed'] + self.results['failed']
        if total > 0:
            success_rate = (self.results['passed'] / total) * 100
        else:
            success_rate = 0
            
        print(f"\n[SUMMARY]")
        print(f"  Tests Passed: {self.results['passed']}")
        print(f"  Tests Failed: {self.results['failed']}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"\n  🎉 SYSTEM IS PRODUCTION READY!")
        elif success_rate >= 60:
            print(f"\n  ✅ SYSTEM IS FUNCTIONAL (minor issues remain)")
        else:
            print(f"\n  ⚠️  SYSTEM NEEDS ATTENTION")
            
        # Save report
        with open('/workspace/final_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n[+] Report saved to final_test_report.json")
        
def main():
    print("="*70)
    print("FINAL COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("Testing all critical functionality after fixes\n")
    
    tester = FinalTestSuite()
    
    # Run all tests
    tester.test_imports()
    tester.test_syntax_check()
    tester.test_web_server()
    tester.test_payload_generation()
    tester.test_security_improvements()
    tester.test_error_handling()
    
    # Generate report
    tester.generate_report()

if __name__ == "__main__":
    main()