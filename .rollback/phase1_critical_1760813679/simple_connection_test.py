#!/usr/bin/env python3
"""
Simple test - just get a connection registered in inf_sock
"""

import socket
import time
import subprocess
import threading
import sys
import os

sys.path.insert(0, '/workspace')

def run_server():
    """Run server in thread"""
    from Application.stitch_cmd import stitch_server
    
    global server_instance
    server_instance = stitch_server()
    server_instance.do_listen('4040')
    
    # Keep checking for connections
    for i in range(30):
        time.sleep(1)
        if server_instance.inf_sock:
            print(f"[Server] Connections detected: {list(server_instance.inf_sock.keys())}")

def simple_client():
    """Simple client that just connects"""
    time.sleep(3)  # Let server start
    
    print("[Client] Connecting to 127.0.0.1:4040...")
    sock = socket.socket()
    
    try:
        sock.connect(('127.0.0.1', 4040))
        print("[Client] Connected!")
        
        # Just stay connected
        time.sleep(5)
        
        print("[Client] Closing...")
        sock.close()
        
    except Exception as e:
        print(f"[Client] Error: {e}")

def main():
    print("="*70)
    print("SIMPLE CONNECTION TEST")
    print("="*70)
    
    # Start server in thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("[Main] Server thread started")
    time.sleep(2)
    
    # Start client
    client_thread = threading.Thread(target=simple_client)
    client_thread.start()
    
    print("[Main] Client thread started")
    
    # Wait for client to finish
    client_thread.join()
    
    # Check server connections
    time.sleep(1)
    
    global server_instance
    if 'server_instance' in globals() and hasattr(server_instance, 'inf_sock'):
        if server_instance.inf_sock:
            print(f"\n✓ SUCCESS: Connections in inf_sock: {list(server_instance.inf_sock.keys())}")
            return True
        else:
            print("\n✗ FAILED: No connections in inf_sock")
            return False
    else:
        print("\n✗ FAILED: Server not initialized")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)