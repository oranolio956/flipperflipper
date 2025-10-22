#!/usr/bin/env python3
"""
Test payload connection to Stitch server
"""

import sys
import time
import socket
import threading
import subprocess
from pathlib import Path

# Add workspace to path
sys.path.insert(0, '/workspace')

def start_stitch_server():
    """Start the Stitch server"""
    print("Starting Stitch server...")
    
    try:
        from Application.stitch_cmd import stitch_server
        
        server = stitch_server()
        server.do_listen('4040')
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is listening
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 4040))
        sock.close()
        
        if result == 0:
            print("✓ Stitch server is listening on port 4040")
            return server
        else:
            print("✗ Stitch server failed to start")
            return None
            
    except Exception as e:
        print(f"✗ Error starting server: {str(e)}")
        return None

def test_payload_connection():
    """Test if payload can connect to server"""
    print("\n=== TESTING PAYLOAD CONNECTION ===")
    
    # Start server
    server = start_stitch_server()
    if not server:
        return False
    
    # Get the generated payload
    payload_path = Path('/workspace/payloads/output/test_linux_python_linux.py')
    if not payload_path.exists():
        print("✗ Payload file not found")
        return False
    
    print(f"✓ Found payload: {payload_path}")
    
    # Execute payload in background
    print("Executing payload...")
    try:
        process = subprocess.Popen([
            'python3', str(payload_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for connection
        time.sleep(5)
        
        # Check if connection was established
        if server.inf_sock:
            print(f"✓ Payload connected! Active connections: {len(server.inf_sock)}")
            for conn_id, sock in server.inf_sock.items():
                print(f"  - Connection: {conn_id}")
            return True
        else:
            print("✗ No connections found")
            return False
            
    except Exception as e:
        print(f"✗ Error executing payload: {str(e)}")
        return False
    finally:
        if 'process' in locals():
            process.terminate()

def main():
    """Main test function"""
    print("=" * 60)
    print("PAYLOAD CONNECTION TEST")
    print("=" * 60)
    
    success = test_payload_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ PAYLOAD CONNECTION TEST PASSED")
    else:
        print("✗ PAYLOAD CONNECTION TEST FAILED")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)