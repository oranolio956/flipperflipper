#!/usr/bin/env python3
"""
Elite PWD Command - Get working directory without syscall logging
Uses direct Windows API calls
"""

import ctypes
import os
import sys
from ctypes import wintypes

def elite_pwd():
    """
    Get current working directory using direct API calls
    Avoids subprocess and reduces logging footprint
    """
    
    try:
        if os.name == 'nt':
            return _windows_elite_pwd()
        else:
            return _unix_elite_pwd()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "directory": None
        }

def _windows_elite_pwd():
    """Windows implementation using GetCurrentDirectoryW"""
    kernel32 = ctypes.windll.kernel32
    
    # Get required buffer size
    buffer_size = kernel32.GetCurrentDirectoryW(0, None)
    
    if buffer_size == 0:
        error_code = kernel32.GetLastError()
        return {
            "success": False,
            "error": f"GetCurrentDirectory failed with error {error_code}",
            "directory": None
        }
    
    # Create buffer and get directory
    buffer = ctypes.create_unicode_buffer(buffer_size)
    result = kernel32.GetCurrentDirectoryW(buffer_size, buffer)
    
    if result == 0:
        error_code = kernel32.GetLastError()
        return {
            "success": False,
            "error": f"GetCurrentDirectory failed with error {error_code}",
            "directory": None
        }
    
    current_dir = buffer.value
    
    # Get additional information about the directory
    try:
        dir_info = _get_directory_info(current_dir)
    except:
        dir_info = {}
    
    return {
        "success": True,
        "directory": current_dir,
        "directory_info": dir_info
    }

def _unix_elite_pwd():
    """Unix implementation using getcwd"""
    try:
        current_dir = os.getcwd()
        
        # Get additional information
        try:
            dir_info = _get_unix_directory_info(current_dir)
        except:
            dir_info = {}
        
        return {
            "success": True,
            "directory": current_dir,
            "directory_info": dir_info
        }
        
    except OSError as e:
        return {
            "success": False,
            "error": str(e),
            "directory": None
        }

def _get_directory_info(directory):
    """Get additional information about directory (Windows)"""
    kernel32 = ctypes.windll.kernel32
    
    info = {}
    
    try:
        # Get file attributes
        attrs = kernel32.GetFileAttributesW(directory)
        if attrs != -1:  # INVALID_FILE_ATTRIBUTES
            info['is_hidden'] = bool(attrs & 0x02)  # FILE_ATTRIBUTE_HIDDEN
            info['is_system'] = bool(attrs & 0x04)  # FILE_ATTRIBUTE_SYSTEM
            info['is_compressed'] = bool(attrs & 0x800)  # FILE_ATTRIBUTE_COMPRESSED
            info['is_encrypted'] = bool(attrs & 0x4000)  # FILE_ATTRIBUTE_ENCRYPTED
        
        # Get drive information
        drive_letter = directory[:3] if len(directory) >= 3 else directory
        if drive_letter.endswith('\\'):
            drive_type = kernel32.GetDriveTypeW(drive_letter)
            drive_types = {
                0: "Unknown",
                1: "Invalid",
                2: "Removable",
                3: "Fixed",
                4: "Network",
                5: "CD-ROM",
                6: "RAM Disk"
            }
            info['drive_type'] = drive_types.get(drive_type, "Unknown")
            
            # Get disk space
            free_bytes = ctypes.c_ulonglong()
            total_bytes = ctypes.c_ulonglong()
            
            if kernel32.GetDiskFreeSpaceExW(
                drive_letter,
                ctypes.byref(free_bytes),
                ctypes.byref(total_bytes),
                None
            ):
                info['free_space'] = free_bytes.value
                info['total_space'] = total_bytes.value
                info['free_space_human'] = _format_size(free_bytes.value)
                info['total_space_human'] = _format_size(total_bytes.value)
                info['used_percent'] = ((total_bytes.value - free_bytes.value) / total_bytes.value * 100) if total_bytes.value > 0 else 0
        
    except Exception as e:
        info['error'] = str(e)
    
    return info

def _get_unix_directory_info(directory):
    """Get additional information about directory (Unix)"""
    import stat
    import os
    
    info = {}
    
    try:
        # Get directory stats
        dir_stat = os.stat(directory)
        info['mode'] = stat.filemode(dir_stat.st_mode)
        info['mode_octal'] = oct(dir_stat.st_mode)[-3:]
        info['uid'] = dir_stat.st_uid
        info['gid'] = dir_stat.st_gid
        
        # Get owner/group names
        try:
            import pwd
            import grp
            info['owner'] = pwd.getpwuid(dir_stat.st_uid).pw_name
            info['group'] = grp.getgrgid(dir_stat.st_gid).gr_name
        except:
            info['owner'] = str(dir_stat.st_uid)
            info['group'] = str(dir_stat.st_gid)
        
        # Get filesystem information
        try:
            statvfs = os.statvfs(directory)
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_available
            
            info['total_space'] = total_space
            info['free_space'] = free_space
            info['total_space_human'] = _format_size(total_space)
            info['free_space_human'] = _format_size(free_space)
            info['used_percent'] = ((total_space - free_space) / total_space * 100) if total_space > 0 else 0
            
        except:
            pass
        
    except Exception as e:
        info['error'] = str(e)
    
    return info

def _format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

if __name__ == "__main__":
    # Test the elite pwd command
    import json
    
    print("Testing Elite PWD Command...")
    
    result = elite_pwd()
    
    if result["success"]:
        print(f"Current Directory: {result['directory']}")
        
        if result.get('directory_info'):
            info = result['directory_info']
            print("\nDirectory Information:")
            
            if 'drive_type' in info:
                print(f"  Drive Type: {info['drive_type']}")
            
            if 'free_space_human' in info:
                print(f"  Free Space: {info['free_space_human']} / {info['total_space_human']}")
                print(f"  Used: {info['used_percent']:.1f}%")
            
            if 'owner' in info:
                print(f"  Owner: {info['owner']} ({info['mode']})")
                
    else:
        print(f"Error: {result['error']}")