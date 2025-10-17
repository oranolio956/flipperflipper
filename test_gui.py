#!/usr/bin/env python3
import os
import sys
import threading
from time import sleep, strftime
import platform
import socket

# Test GUI functionality
def test_meeting_gui():
    """Test the meeting GUI interface"""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        print("[TEST] Creating GUI window...")
        
        root = tk.Tk()
        root.title("Join Meeting - TEST")
        root.geometry("480x320")
        root.resizable(False, False)
        
        # Configure colors (Zoom-like theme)
        bg_color = "#ffffff"
        primary_color = "#2d8cff"
        secondary_color = "#f7f9fa"
        text_color = "#1f2937"
        
        root.configure(bg=bg_color)
        
        # Main container
        main_frame = tk.Frame(root, bg=bg_color, padx=40, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Logo/Title area
        title_frame = tk.Frame(main_frame, bg=bg_color)
        title_frame.pack(fill="x", pady=(0, 30))
        
        # App icon (using text as placeholder)
        icon_label = tk.Label(title_frame, text="📹", font=("Arial", 24), 
                             bg=bg_color, fg=primary_color)
        icon_label.pack()
        
        # Title
        title_label = tk.Label(title_frame, text="Join Meeting", 
                              font=("Arial", 18, "bold"), 
                              bg=bg_color, fg=text_color)
        title_label.pack(pady=(5, 0))
        
        # Meeting ID input area
        input_frame = tk.Frame(main_frame, bg=bg_color)
        input_frame.pack(fill="x", pady=(0, 20))
        
        # Meeting ID label
        id_label = tk.Label(input_frame, text="Meeting ID", 
                           font=("Arial", 11), 
                           bg=bg_color, fg=text_color)
        id_label.pack(anchor="w", pady=(0, 5))
        
        # Meeting ID entry
        id_entry = tk.Entry(input_frame, font=("Arial", 14), 
                           relief="solid", borderwidth=1,
                           highlightthickness=2, highlightcolor=primary_color)
        id_entry.pack(fill="x", ipady=8)
        id_entry.focus()
        
        # Insert placeholder text
        id_entry.insert(0, "123-456-789")
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg=bg_color)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Status label (for testing)
        status_label = tk.Label(main_frame, text="GUI Test - Ready to join meeting", 
                               font=("Arial", 10), 
                               bg=bg_color, fg="green")
        status_label.pack(pady=(10, 0))
        
        meeting_id_result = {"value": ""}
        
        def join_meeting():
            meeting_id = id_entry.get().strip()
            if meeting_id:
                meeting_id_result["value"] = meeting_id
                print(f"[TEST] Meeting ID entered: {meeting_id}")
                
                # Show connecting status
                id_entry.configure(state="disabled")
                join_btn.configure(state="disabled", text="Connecting...")
                status_label.configure(text="Connecting to meeting...", fg="orange")
                
                # Auto-close after 3 seconds
                root.after(3000, root.quit)
            else:
                status_label.configure(text="Please enter a Meeting ID", fg="red")
        
        # Join button
        join_btn = tk.Button(button_frame, text="Join Meeting", 
                            font=("Arial", 11, "bold"),
                            bg=primary_color, fg="white",
                            relief="flat", borderwidth=0,
                            padx=30, pady=10,
                            cursor="hand2",
                            command=join_meeting)
        join_btn.pack(side="right")
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              font=("Arial", 11),
                              bg=secondary_color, fg=text_color,
                              relief="flat", borderwidth=1,
                              padx=30, pady=10,
                              cursor="hand2",
                              command=root.quit)
        cancel_btn.pack(side="right", padx=(0, 10))
        
        print("[TEST] GUI created successfully. Starting mainloop...")
        
        # Auto-click join button after 2 seconds for testing
        root.after(2000, join_meeting)
        
        root.mainloop()
        root.destroy()
        
        print(f"[TEST] GUI test completed. Meeting ID: {meeting_id_result['value']}")
        return meeting_id_result["value"]
        
    except Exception as e:
        print(f"[TEST] GUI Error: {e}")
        return None

if __name__ == "__main__":
    print("="*50)
    print("    TESTING MEETING GUI INTERFACE")
    print("="*50)
    
    # Test with virtual display
    os.environ['DISPLAY'] = ':99'
    
    # Start virtual display
    print("[TEST] Starting virtual display...")
    os.system("Xvfb :99 -screen 0 1024x768x24 &")
    sleep(2)
    
    # Test the GUI
    result = test_meeting_gui()
    
    if result:
        print(f"[TEST] ✅ GUI test PASSED - Meeting ID: {result}")
    else:
        print("[TEST] ❌ GUI test FAILED")
    
    # Cleanup
    os.system("pkill Xvfb")
    print("[TEST] Test completed.")