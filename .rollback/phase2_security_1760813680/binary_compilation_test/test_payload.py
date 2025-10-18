#!/usr/bin/env python3
import socket
import sys
import os
import time
import subprocess
import platform

def main():
    print(f"[Payload] Running on {platform.system()}")
    print(f"[Payload] Python: {sys.version}")
    print(f"[Payload] Executable: {sys.executable}")
    
    # Try to connect
    try:
        sock = socket.socket()
        sock.settimeout(2)
        sock.connect(('127.0.0.1', 4040))
        print("[Payload] Connected to C2")
        sock.close()
    except:
        print("[Payload] Could not connect to C2")
    
    print("[Payload] Exiting...")
    
if __name__ == "__main__":
    main()
