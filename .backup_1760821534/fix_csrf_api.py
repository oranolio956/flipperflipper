#!/usr/bin/env python3
"""
Fix CSRF issues with API endpoints
The API endpoints require CSRF tokens but we're not sending them
"""

import os
import sys
import time
import subprocess
import requests
import re
import json

os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

def test_with_csrf():
    """Test API with CSRF tokens"""
    print("[*] Testing API with CSRF tokens...")
    
    session = requests.Session()
    
    # Get CSRF token from login page
    resp = session.get('http://localhost:5000/login')
    csrf_token = None
    if 'csrf_token' in resp.text:
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
            print(f"  [+] Got CSRF token: {csrf_token[:20]}...")
    
    # Login
    login_data = {'username': 'admin', 'password': 'testpassword123'}
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
    
    if resp.status_code in [302, 303]:
        print("  [+] Login successful")
    
    # Get fresh CSRF token from meta tag (if available)
    resp = session.get('http://localhost:5000/')
    
    # Update CSRF token from dashboard if available
    if 'csrf-token' in resp.text:
        match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
            print(f"  [+] Updated CSRF token from dashboard")
    
    # Test payload generation WITH CSRF
    print("\n[1] Testing Payload Generation with CSRF...")
    
    payload_config = {
        'bind_host': '',
        'bind_port': '',
        'listen_host': '127.0.0.1',
        'listen_port': '4040',
        'enable_bind': False,
        'enable_listen': True,
        'platform': 'python'
    }
    
    # Add CSRF token to headers
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token  # Flask-WTF expects this header
    }
    
    resp = session.post(
        'http://localhost:5000/api/generate-payload',
        json=payload_config,
        headers=headers
    )
    
    print(f"  Response: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('success'):
            print(f"  [+] SUCCESS! Payload generated")
            print(f"      Type: {result.get('payload_type')}")
            print(f"      Size: {result.get('payload_size')}")
        else:
            print(f"  [-] Generation failed: {result.get('error') or result.get('message')}")
    else:
        print(f"  [-] API error: {resp.text[:200]}")
    
    # Test command execution WITH CSRF
    print("\n[2] Testing Command Execution with CSRF...")
    
    # Get connections
    resp = session.get('http://localhost:5000/api/connections', headers={'X-CSRFToken': csrf_token})
    
    if resp.status_code == 200:
        connections = resp.json()
        
        # Find online target
        target_id = None
        for conn in connections:
            if conn.get('status') == 'online':
                target_id = conn.get('id') or conn.get('target')
                print(f"  [+] Using target: {target_id}")
                break
        
        if target_id:
            command_data = {
                'connection_id': target_id,
                'command': 'pwd'
            }
            
            resp = session.post(
                'http://localhost:5000/api/execute',
                json=command_data,
                headers=headers  # Include CSRF token
            )
            
            print(f"  Response: {resp.status_code}")
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('success'):
                    output = result.get('output', '')
                    print(f"  [+] SUCCESS! Command executed")
                    print(f"      Output: {output[:100]}...")
                else:
                    print(f"  [-] Command failed: {result.get('error')}")
            else:
                print(f"  [-] API error: {resp.text[:200]}")

def fix_csrf_in_api():
    """Optionally disable CSRF for API endpoints"""
    print("\n[*] Alternative: Disable CSRF for API endpoints...")
    
    # This would modify web_app_real.py to exempt API routes from CSRF
    fix_code = '''
# Add to web_app_real.py after CSRF initialization:

# Exempt API endpoints from CSRF
csrf.exempt('/api/generate-payload')
csrf.exempt('/api/execute')
csrf.exempt('/api/connections')
csrf.exempt('/api/download-payload')

# Or disable CSRF for all /api/* routes:
@app.before_request
def csrf_protect():
    if request.path.startswith('/api/'):
        csrf.exempt(request.endpoint)
'''
    
    print("  Fix option 1: Add X-CSRFToken header to all API requests")
    print("  Fix option 2: Exempt API endpoints from CSRF protection")
    print("\n  Recommended: Use X-CSRFToken header for security")

def create_working_api_client():
    """Create a working API client that handles CSRF"""
    
    client_code = '''#!/usr/bin/env python3
"""
Working API client with CSRF handling
"""
import requests
import re
import json

class StitchAPIClient:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = None
        
    def login(self, username, password):
        """Login and get CSRF token"""
        # Get login page for CSRF
        resp = self.session.get(f'{self.base_url}/login')
        
        # Extract CSRF token
        if 'csrf_token' in resp.text:
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', resp.text)
            if match:
                self.csrf_token = match.group(1)
        
        # Login
        login_data = {
            'username': username,
            'password': password
        }
        
        if self.csrf_token:
            login_data['csrf_token'] = self.csrf_token
        
        resp = self.session.post(
            f'{self.base_url}/login',
            data=login_data,
            allow_redirects=False
        )
        
        if resp.status_code in [302, 303]:
            # Get CSRF token from dashboard
            resp = self.session.get(f'{self.base_url}/')
            if 'csrf-token' in resp.text:
                match = re.search(r'name="csrf-token".*?content="([^"]+)"', resp.text)
                if match:
                    self.csrf_token = match.group(1)
            
            return True
        return False
    
    def generate_payload(self, config):
        """Generate payload with CSRF"""
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': self.csrf_token
        }
        
        resp = self.session.post(
            f'{self.base_url}/api/generate-payload',
            json=config,
            headers=headers
        )
        
        if resp.status_code == 200:
            return resp.json()
        return
    
    def execute_command(self, target_id, command):
        """Execute command with CSRF"""
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': self.csrf_token
        }
        
        data = {
            'connection_id': target_id,
            'command': command
        }
        
        resp = self.session.post(
            f'{self.base_url}/api/execute',
            json=data,
            headers=headers
        )
        
        if resp.status_code == 200:
            return resp.json()
        return
    
    def get_connections(self):
        """Get connections with CSRF"""
        headers = {'X-CSRFToken': self.csrf_token}
        
        resp = self.session.get(
            f'{self.base_url}/api/connections',
            headers=headers
        )
        
        if resp.status_code == 200:
            return resp.json()
        return []

# Example usage
if __name__ == "__main__":
    client = StitchAPIClient()
    
    if client.login('admin', 'testpassword123'):
        print("[+] Logged in")
        
        # Generate payload
        config = {
            'platform': 'python',
            'listen_host': '127.0.0.1',
            'listen_port': '4040',
            'enable_listen': True,
            'enable_bind': False
        }
        
        result = client.generate_payload(config)
        if result and result.get('success'):
            print(f"[+] Payload generated: {result.get('payload_type')}")
        
        # Get connections
        connections = client.get_connections()
        print(f"[+] Found {len(connections)} connections")
        
        # Execute command on first online target
        for conn in connections:
            if conn.get('status') == 'online':
                target = conn.get('id') or conn.get('target')
                result = client.execute_command(target, 'pwd')
                if result and result.get('success'):
                    print(f"[+] Command output: {result.get('output')[:100]}")
                break
'''
    
    with open('/workspace/stitch_api_client.py', 'w') as f:
        f.write(client_code)
    
    print("\n[+] Created working API client: /workspace/stitch_api_client.py")

def main():
    print("="*70)
    print("FIXING CSRF API ISSUES")
    print("="*70)
    
    # Start web server
    print("\n[*] Starting web server...")
    server_proc = subprocess.Popen(
        ['python3', 'web_app_real.py'],
        cwd='/workspace',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Start test payload
    payload_proc = subprocess.Popen(
        ['python3', '/tmp/stitch_payload.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        time.sleep(5)
        
        # Test with CSRF
        test_with_csrf()
        
        # Show fix options
        fix_csrf_in_api()
        
        # Create working client
        create_working_api_client()
        
        print("\n" + "="*70)
        print("SOLUTION")
        print("="*70)
        print("✓ API requires X-CSRFToken header")
        print("✓ Must include CSRF token from login or dashboard")
        print("✓ Created working API client with CSRF handling")
        print("\nAll API calls must include:")
        print('  headers = {"X-CSRFToken": csrf_token}')
        
    finally:
        payload_proc.terminate()
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except Exception:
            server_proc.kill()

if __name__ == "__main__":
    main()