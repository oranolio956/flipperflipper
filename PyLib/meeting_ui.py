# Copyright (c) 2017, Nathan Lopez
# Stitch is under the MIT license. See the LICENSE file at the root of the project for the detailed license terms.

import os
import sys
import threading
from time import sleep

# Cross-platform GUI imports
try:
    if win_client():
        import tkinter as tk
        from tkinter import ttk, messagebox, font
    else:
        import Tkinter as tk
        import ttk
        import tkMessageBox as messagebox
        import tkFont as font
except ImportError:
    # Fallback for older Python versions
    try:
        import Tkinter as tk
        import ttk
        import tkMessageBox as messagebox
        import tkFont as font
    except ImportError:
        # If no GUI available, create a simple console version
        tk = None

class MeetingUI:
    def __init__(self):
        self.meeting_id = ""
        self.root = None
        self.setup_gui()
    
    def setup_gui(self):
        if tk is None:
            # Fallback to console version
            self.console_meeting_prompt()
            return
            
        self.root = tk.Tk()
        self.root.title("Join Meeting")
        self.root.geometry("480x320")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Configure colors (Zoom-like theme)
        bg_color = "#ffffff"
        primary_color = "#2d8cff"
        secondary_color = "#f7f9fa"
        text_color = "#1f2937"
        
        self.root.configure(bg=bg_color)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=bg_color, padx=40, pady=30)
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
        self.id_entry = tk.Entry(input_frame, font=("Arial", 14), 
                                relief="solid", borderwidth=1,
                                highlightthickness=2, highlightcolor=primary_color)
        self.id_entry.pack(fill="x", ipady=8)
        self.id_entry.focus()
        
        # Placeholder text
        self.id_entry.insert(0, "Enter Meeting ID")
        self.id_entry.configure(fg="gray")
        self.id_entry.bind("<FocusIn>", self.clear_placeholder)
        self.id_entry.bind("<FocusOut>", self.add_placeholder)
        self.id_entry.bind("<Return>", lambda e: self.join_meeting())
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg=bg_color)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Join button
        self.join_btn = tk.Button(button_frame, text="Join Meeting", 
                                 font=("Arial", 11, "bold"),
                                 bg=primary_color, fg="white",
                                 relief="flat", borderwidth=0,
                                 padx=30, pady=10,
                                 cursor="hand2",
                                 command=self.join_meeting)
        self.join_btn.pack(side="right")
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              font=("Arial", 11),
                              bg=secondary_color, fg=text_color,
                              relief="flat", borderwidth=1,
                              padx=30, pady=10,
                              cursor="hand2",
                              command=self.cancel_meeting)
        cancel_btn.pack(side="right", padx=(0, 10))
        
        # Status frame (initially hidden)
        self.status_frame = tk.Frame(main_frame, bg=bg_color)
        
        self.status_label = tk.Label(self.status_frame, text="", 
                                    font=("Arial", 10), 
                                    bg=bg_color, fg="green")
        self.status_label.pack()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def clear_placeholder(self, event):
        if self.id_entry.get() == "Enter Meeting ID":
            self.id_entry.delete(0, tk.END)
            self.id_entry.configure(fg="black")
            
    def add_placeholder(self, event):
        if not self.id_entry.get():
            self.id_entry.insert(0, "Enter Meeting ID")
            self.id_entry.configure(fg="gray")
            
    def join_meeting(self):
        meeting_id = self.id_entry.get().strip()
        if not meeting_id or meeting_id == "Enter Meeting ID":
            messagebox.showerror("Error", "Please enter a Meeting ID")
            return
            
        self.meeting_id = meeting_id
        
        # Show connecting status
        self.status_frame.pack(fill="x", pady=(10, 0))
        self.status_label.configure(text=f"Connecting to meeting {meeting_id}...")
        self.join_btn.configure(state="disabled", text="Connecting...")
        
        # Simulate connection delay
        self.root.after(2000, self.connection_complete)
        
    def connection_complete(self):
        self.status_label.configure(text="Connected successfully!", fg="green")
        self.root.after(1500, self.close_window)
        
    def cancel_meeting(self):
        self.close_window()
        
    def close_window(self):
        if self.root:
            self.root.quit()
            self.root.destroy()
            
    def on_closing(self):
        self.close_window()
        
    def console_meeting_prompt(self):
        """Fallback console version if GUI is not available"""
        print("\n" + "="*50)
        print("           📹 JOIN MEETING")
        print("="*50)
        try:
            meeting_id = raw_input("Enter Meeting ID: ").strip()
        except NameError:
            meeting_id = input("Enter Meeting ID: ").strip()
            
        if meeting_id:
            self.meeting_id = meeting_id
            print(f"Connecting to meeting {meeting_id}...")
            sleep(2)
            print("Connected successfully!")
            sleep(1)
        else:
            print("No meeting ID entered. Exiting...")
            
    def show(self):
        """Display the meeting UI"""
        if self.root:
            self.root.mainloop()
        return self.meeting_id

def show_meeting_ui():
    """Main function to show the meeting UI"""
    try:
        ui = MeetingUI()
        meeting_id = ui.show()
        return meeting_id
    except Exception as e:
        # Fallback to simple console prompt
        print(f"GUI Error: {e}")
        print("\n" + "="*40)
        print("         JOIN MEETING")
        print("="*40)
        try:
            meeting_id = raw_input("Enter Meeting ID: ").strip()
        except NameError:
            meeting_id = input("Enter Meeting ID: ").strip()
        return meeting_id

# For testing
if __name__ == "__main__":
    meeting_id = show_meeting_ui()
    print(f"Meeting ID entered: {meeting_id}")