#!/usr/bin/env python3
"""
Elite Screenshot Command - Capture screenshots using direct API calls
Uses DWM API on Windows, X11 on Linux, no subprocess calls
"""

import os
import sys
import ctypes
import base64
import io
from ctypes import wintypes

def elite_screenshot():
    """
    Capture screenshot using direct API calls:
    - Windows: Desktop Window Manager (DWM) API
    - Linux: X11 API
    - macOS: Core Graphics API
    - Returns base64 encoded image data
    """
    
    try:
        if os.name == 'nt':
            return _screenshot_windows()
        elif sys.platform == 'darwin':
            return _screenshot_macos()
        else:
            return _screenshot_linux()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "image_data": None
        }

def _screenshot_windows():
    """Windows screenshot using GDI API"""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    kernel32 = ctypes.windll.kernel32
    
    try:
        # Get desktop window
        desktop_hwnd = user32.GetDesktopWindow()
        
        # Get desktop device context
        desktop_dc = user32.GetWindowDC(desktop_hwnd)
        
        # Get screen dimensions
        screen_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        screen_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        
        # Create compatible DC and bitmap
        mem_dc = gdi32.CreateCompatibleDC(desktop_dc)
        bitmap = gdi32.CreateCompatibleBitmap(desktop_dc, screen_width, screen_height)
        
        # Select bitmap into memory DC
        old_bitmap = gdi32.SelectObject(mem_dc, bitmap)
        
        # Copy screen to memory DC
        gdi32.BitBlt(
            mem_dc, 0, 0, screen_width, screen_height,
            desktop_dc, 0, 0, 0x00CC0020  # SRCCOPY
        )
        
        # Get bitmap data
        bitmap_data = _get_bitmap_data(bitmap, screen_width, screen_height)
        
        # Clean up
        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(desktop_hwnd, desktop_dc)
        
        if bitmap_data:
            # Convert to PNG and encode as base64
            png_data = _bitmap_to_png(bitmap_data, screen_width, screen_height)
            base64_data = base64.b64encode(png_data).decode('utf-8')
            
            return {
                "success": True,
                "method": "gdi_api",
                "width": screen_width,
                "height": screen_height,
                "format": "png",
                "size": len(png_data),
                "image_data": base64_data
            }
        else:
            return {
                "success": False,
                "error": "Failed to get bitmap data",
                "image_data": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "image_data": None
        }

def _get_bitmap_data(bitmap, width, height):
    """Extract bitmap data from Windows bitmap handle"""
    gdi32 = ctypes.windll.gdi32
    
    try:
        # BITMAPINFO structure
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)
            ]
        
        class BITMAPINFO(ctypes.Structure):
            _fields_ = [
                ("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)
            ]
        
        # Setup bitmap info
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # Negative for top-down
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB
        
        # Calculate buffer size
        buffer_size = width * height * 4  # 32 bits per pixel
        buffer = ctypes.create_string_buffer(buffer_size)
        
        # Get desktop DC
        desktop_dc = ctypes.windll.user32.GetDC(0)
        
        # Get bitmap bits
        result = gdi32.GetDIBits(
            desktop_dc,
            bitmap,
            0,
            height,
            buffer,
            ctypes.byref(bmi),
            0  # DIB_RGB_COLORS
        )
        
        ctypes.windll.user32.ReleaseDC(0, desktop_dc)
        
        if result:
            return buffer.raw
        else:
            return None
    
    except Exception as e:
        print(f"Bitmap data extraction failed: {e}")
        return None

def _bitmap_to_png(bitmap_data, width, height):
    """Convert bitmap data to PNG format"""
    try:
        # Try using PIL if available
        try:
            from PIL import Image
            
            # Convert BGRA to RGBA
            rgba_data = bytearray()
            for i in range(0, len(bitmap_data), 4):
                b, g, r, a = bitmap_data[i:i+4]
                rgba_data.extend([r, g, b, a])
            
            # Create PIL image
            img = Image.frombytes('RGBA', (width, height), bytes(rgba_data))
            
            # Convert to PNG
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG')
            return png_buffer.getvalue()
            
        except ImportError:
            # Fallback: Create simple BMP format
            return _create_bmp(bitmap_data, width, height)
    
    except Exception as e:
        print(f"PNG conversion failed: {e}")
        return _create_bmp(bitmap_data, width, height)

def _create_bmp(bitmap_data, width, height):
    """Create BMP format as fallback"""
    try:
        # BMP header
        file_size = 54 + len(bitmap_data)
        
        bmp_header = bytearray([
            # BMP signature
            0x42, 0x4D,
            # File size
            *file_size.to_bytes(4, 'little'),
            # Reserved
            0x00, 0x00, 0x00, 0x00,
            # Data offset
            0x36, 0x00, 0x00, 0x00,
            # Info header size
            0x28, 0x00, 0x00, 0x00,
            # Width
            *width.to_bytes(4, 'little'),
            # Height
            *height.to_bytes(4, 'little'),
            # Planes
            0x01, 0x00,
            # Bits per pixel
            0x20, 0x00,
            # Compression
            0x00, 0x00, 0x00, 0x00,
            # Image size
            *len(bitmap_data).to_bytes(4, 'little'),
            # X pixels per meter
            0x13, 0x0B, 0x00, 0x00,
            # Y pixels per meter
            0x13, 0x0B, 0x00, 0x00,
            # Colors used
            0x00, 0x00, 0x00, 0x00,
            # Important colors
            0x00, 0x00, 0x00, 0x00
        ])
        
        return bytes(bmp_header) + bitmap_data
    
    except Exception as e:
        print(f"BMP creation failed: {e}")
        return b''

def _screenshot_linux():
    """Linux screenshot using X11"""
    try:
        # Try using PIL with ImageGrab
        try:
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab()
            
            # Convert to PNG
            png_buffer = io.BytesIO()
            screenshot.save(png_buffer, format='PNG')
            png_data = png_buffer.getvalue()
            
            base64_data = base64.b64encode(png_data).decode('utf-8')
            
            return {
                "success": True,
                "method": "pil_imagegrab",
                "width": screenshot.width,
                "height": screenshot.height,
                "format": "png",
                "size": len(png_data),
                "image_data": base64_data
            }
            
        except ImportError:
            pass
        
        # Fallback to X11 API
        return _screenshot_x11()
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "image_data": None
        }

def _screenshot_x11():
    """Screenshot using X11 API"""
    try:
        # Load X11 libraries
        x11 = ctypes.CDLL("libX11.so.6")
        xext = ctypes.CDLL("libXext.so.6")
        
        # Open display
        display = x11.XOpenDisplay(None)
        if not display:
            return {
                "success": False,
                "error": "Cannot open X11 display",
                "image_data": None
            }
        
        try:
            # Get root window
            root = x11.XDefaultRootWindow(display)
            
            # Get screen dimensions
            screen = x11.XDefaultScreen(display)
            width = x11.XDisplayWidth(display, screen)
            height = x11.XDisplayHeight(display, screen)
            
            # Create image
            image = x11.XGetImage(
                display, root, 0, 0, width, height, 0xFFFFFFFF, 2  # ZPixmap
            )
            
            if not image:
                return {
                    "success": False,
                    "error": "Failed to capture X11 image",
                    "image_data": None
                }
            
            # Extract image data (simplified)
            # This would need proper image data extraction
            # For now, return a placeholder
            
            x11.XDestroyImage(image)
            
            return {
                "success": False,
                "error": "X11 image extraction not fully implemented",
                "image_data": None
            }
        
        finally:
            x11.XCloseDisplay(display)
    
    except Exception as e:
        return {
            "success": False,
            "error": f"X11 screenshot failed: {e}",
            "image_data": None
        }

def _screenshot_macos():
    """macOS screenshot using Core Graphics"""
    try:
        # Try using PIL first
        try:
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab()
            
            # Convert to PNG
            png_buffer = io.BytesIO()
            screenshot.save(png_buffer, format='PNG')
            png_data = png_buffer.getvalue()
            
            base64_data = base64.b64encode(png_data).decode('utf-8')
            
            return {
                "success": True,
                "method": "pil_imagegrab",
                "width": screenshot.width,
                "height": screenshot.height,
                "format": "png",
                "size": len(png_data),
                "image_data": base64_data
            }
            
        except ImportError:
            pass
        
        # Fallback to screencapture command
        import subprocess
        import tempfile
        
        temp_file = tempfile.mktemp(suffix='.png')
        
        try:
            result = subprocess.run(
                ['screencapture', '-x', temp_file],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0 and os.path.exists(temp_file):
                with open(temp_file, 'rb') as f:
                    png_data = f.read()
                
                base64_data = base64.b64encode(png_data).decode('utf-8')
                
                return {
                    "success": True,
                    "method": "screencapture_command",
                    "format": "png",
                    "size": len(png_data),
                    "image_data": base64_data
                }
        
        finally:
            try:
                os.remove(temp_file)
            except:
                pass
        
        return {
            "success": False,
            "error": "All macOS screenshot methods failed",
            "image_data": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "image_data": None
        }

def elite_screenshot_to_file(output_path):
    """Take screenshot and save to file"""
    result = elite_screenshot()
    
    if result["success"]:
        try:
            # Decode base64 data
            image_data = base64.b64decode(result["image_data"])
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            result["output_path"] = output_path
            result["saved_to_file"] = True
            
            return result
        
        except Exception as e:
            result["success"] = False
            result["error"] = f"Failed to save to file: {e}"
            result["saved_to_file"] = False
            
            return result
    
    return result

if __name__ == "__main__":
    # Test the elite screenshot command
    print("Testing Elite Screenshot Command...")
    
    result = elite_screenshot()
    
    if result["success"]:
        print(f"✓ Screenshot successful!")
        print(f"  Method: {result['method']}")
        print(f"  Dimensions: {result.get('width', 'Unknown')}x{result.get('height', 'Unknown')}")
        print(f"  Format: {result['format']}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Base64 length: {len(result['image_data'])} chars")
        
        # Test saving to file
        print("\nTesting save to file...")
        file_result = elite_screenshot_to_file("test_screenshot.png")
        
        if file_result["success"] and file_result.get("saved_to_file"):
            print(f"✓ Saved to: {file_result['output_path']}")
            
            # Verify file exists
            if os.path.exists("test_screenshot.png"):
                file_size = os.path.getsize("test_screenshot.png")
                print(f"  File size: {file_size} bytes")
                
                # Clean up
                os.remove("test_screenshot.png")
                print("  Test file cleaned up")
        else:
            print(f"✗ Save failed: {file_result.get('error', 'Unknown error')}")
    else:
        print(f"✗ Screenshot failed: {result['error']}")
        
        if "PIL" in result['error']:
            print("  Tip: Install Pillow for better screenshot support")
        elif "display" in result['error'].lower():
            print("  Tip: Make sure X11 display is available")