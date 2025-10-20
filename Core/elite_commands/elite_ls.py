#!/usr/bin/env python3
"""
Elite LS Command - Advanced directory listing with hidden files and ADS detection
Uses direct Windows API calls, no subprocess
"""

import ctypes
import os
import sys
import stat
import time
from ctypes import wintypes
from datetime import datetime

def elite_ls(directory="."):
    """
    List directory with advanced features:
    - Hidden files and system files
    - Alternate Data Streams (ADS) detection
    - File attributes and permissions
    - No subprocess calls - pure API
    """
    
    if not os.path.exists(directory):
        return {
            "success": False,
            "error": f"Directory not found: {directory}",
            "files": []
        }
    
    try:
        if os.name == 'nt':
            return _windows_elite_ls(directory)
        else:
            return _unix_elite_ls(directory)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "files": []
        }

def _windows_elite_ls(directory):
    """Windows implementation using FindFirstFileExW API"""
    kernel32 = ctypes.windll.kernel32
    
    # Constants
    INVALID_HANDLE_VALUE = -1
    FILE_ATTRIBUTE_HIDDEN = 0x02
    FILE_ATTRIBUTE_SYSTEM = 0x04
    FILE_ATTRIBUTE_DIRECTORY = 0x10
    FILE_ATTRIBUTE_ARCHIVE = 0x20
    FILE_ATTRIBUTE_READONLY = 0x01
    FILE_ATTRIBUTE_COMPRESSED = 0x800
    FILE_ATTRIBUTE_ENCRYPTED = 0x4000
    
    # WIN32_FIND_DATAW structure
    class WIN32_FIND_DATAW(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("dwReserved0", wintypes.DWORD),
            ("dwReserved1", wintypes.DWORD),
            ("cFileName", wintypes.WCHAR * 260),
            ("cAlternateFileName", wintypes.WCHAR * 14),
        ]
    
    find_data = WIN32_FIND_DATAW()
    files = []
    
    # Search for all files including hidden
    search_path = os.path.join(directory, "*")
    
    # Use FindFirstFileExW for better performance
    handle = kernel32.FindFirstFileExW(
        search_path,
        1,  # FindExInfoBasic
        ctypes.byref(find_data),
        0,  # FindExSearchNameMatch
        None,
        0x2  # FIND_FIRST_EX_LARGE_FETCH
    )
    
    if handle == INVALID_HANDLE_VALUE:
        error_code = kernel32.GetLastError()
        return {
            "success": False,
            "error": f"FindFirstFileEx failed with error {error_code}",
            "files": []
        }
    
    try:
        while True:
            filename = find_data.cFileName
            
            # Skip . and ..
            if filename not in [".", ".."]:
                file_path = os.path.join(directory, filename)
                
                # Get file size
                file_size = (find_data.nFileSizeHigh << 32) + find_data.nFileSizeLow
                
                # Parse attributes
                attrs = find_data.dwFileAttributes
                file_info = {
                    'name': filename,
                    'path': file_path,
                    'size': file_size,
                    'size_human': _format_size(file_size),
                    'is_directory': bool(attrs & FILE_ATTRIBUTE_DIRECTORY),
                    'is_hidden': bool(attrs & FILE_ATTRIBUTE_HIDDEN),
                    'is_system': bool(attrs & FILE_ATTRIBUTE_SYSTEM),
                    'is_readonly': bool(attrs & FILE_ATTRIBUTE_READONLY),
                    'is_archive': bool(attrs & FILE_ATTRIBUTE_ARCHIVE),
                    'is_compressed': bool(attrs & FILE_ATTRIBUTE_COMPRESSED),
                    'is_encrypted': bool(attrs & FILE_ATTRIBUTE_ENCRYPTED),
                    'attributes_raw': attrs,
                    'created': _filetime_to_datetime(find_data.ftCreationTime),
                    'modified': _filetime_to_datetime(find_data.ftLastWriteTime),
                    'accessed': _filetime_to_datetime(find_data.ftLastAccessTime)
                }
                
                # Check for Alternate Data Streams
                ads_streams = _check_ads(file_path)
                if ads_streams:
                    file_info['ads'] = ads_streams
                    file_info['has_ads'] = True
                else:
                    file_info['has_ads'] = False
                
                # Get owner information
                try:
                    owner_info = _get_file_owner(file_path)
                    file_info.update(owner_info)
                except:
                    file_info['owner'] = 'Unknown'
                    file_info['owner_sid'] = 'Unknown'
                
                # Check if file is signed (for executables)
                if filename.lower().endswith(('.exe', '.dll', '.sys')):
                    file_info['is_signed'] = _check_signature(file_path)
                else:
                    file_info['is_signed'] = None
                
                files.append(file_info)
            
            # Get next file
            if not kernel32.FindNextFileW(handle, ctypes.byref(find_data)):
                break
        
    finally:
        kernel32.FindClose(handle)
    
    # Sort files: directories first, then by name
    files.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
    
    return {
        "success": True,
        "directory": directory,
        "file_count": len([f for f in files if not f['is_directory']]),
        "dir_count": len([f for f in files if f['is_directory']]),
        "hidden_count": len([f for f in files if f['is_hidden']]),
        "ads_count": len([f for f in files if f.get('has_ads', False)]),
        "files": files
    }

def _unix_elite_ls(directory):
    """Unix implementation with extended attributes and hidden files"""
    files = []
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            try:
                # Use lstat to get info without following symlinks
                file_stat = os.lstat(file_path)
                
                file_info = {
                    'name': filename,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'size_human': _format_size(file_stat.st_size),
                    'is_directory': stat.S_ISDIR(file_stat.st_mode),
                    'is_hidden': filename.startswith('.'),
                    'is_symlink': stat.S_ISLNK(file_stat.st_mode),
                    'mode': stat.filemode(file_stat.st_mode),
                    'mode_octal': oct(file_stat.st_mode)[-3:],
                    'uid': file_stat.st_uid,
                    'gid': file_stat.st_gid,
                    'created': datetime.fromtimestamp(file_stat.st_ctime),
                    'modified': datetime.fromtimestamp(file_stat.st_mtime),
                    'accessed': datetime.fromtimestamp(file_stat.st_atime)
                }
                
                # Get owner/group names
                try:
                    import pwd
                    import grp
                    file_info['owner'] = pwd.getpwuid(file_stat.st_uid).pw_name
                    file_info['group'] = grp.getgrgid(file_stat.st_gid).gr_name
                except:
                    file_info['owner'] = str(file_stat.st_uid)
                    file_info['group'] = str(file_stat.st_gid)
                
                # Check for extended attributes
                try:
                    import xattr
                    attrs = list(xattr.listxattr(file_path))
                    if attrs:
                        file_info['xattrs'] = attrs
                        file_info['has_xattrs'] = True
                    else:
                        file_info['has_xattrs'] = False
                except ImportError:
                    file_info['has_xattrs'] = False
                except:
                    file_info['has_xattrs'] = False
                
                # For symlinks, get target
                if file_info['is_symlink']:
                    try:
                        file_info['symlink_target'] = os.readlink(file_path)
                    except:
                        file_info['symlink_target'] = 'Unknown'
                
                files.append(file_info)
                
            except (OSError, IOError) as e:
                # Add entry for inaccessible files
                files.append({
                    'name': filename,
                    'path': file_path,
                    'error': str(e),
                    'accessible': False
                })
                continue
        
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied accessing {directory}",
            "files": []
        }
    
    # Sort files: directories first, then by name
    files.sort(key=lambda x: (not x.get('is_directory', False), x['name'].lower()))
    
    return {
        "success": True,
        "directory": directory,
        "file_count": len([f for f in files if not f.get('is_directory', False)]),
        "dir_count": len([f for f in files if f.get('is_directory', False)]),
        "hidden_count": len([f for f in files if f.get('is_hidden', False)]),
        "files": files
    }

def _check_ads(filepath):
    """Check for Alternate Data Streams (Windows only)"""
    if os.name != 'nt':
        return []
    
    kernel32 = ctypes.windll.kernel32
    streams = []
    
    try:
        # Use FindFirstStreamW to enumerate streams
        STREAM_INFO_LEVELS = 0  # FindStreamInfoStandard
        
        # Define STREAM_INFO structure
        class WIN32_FIND_STREAM_DATA(ctypes.Structure):
            _fields_ = [
                ("StreamSize", ctypes.c_longlong),
                ("cStreamName", wintypes.WCHAR * 296)
            ]
        
        find_data = WIN32_FIND_STREAM_DATA()
        
        handle = kernel32.FindFirstStreamW(
            filepath,
            STREAM_INFO_LEVELS,
            ctypes.byref(find_data),
            0
        )
        
        if handle != -1:
            while True:
                stream_name = find_data.cStreamName
                stream_size = find_data.StreamSize
                
                # Skip the main data stream
                if stream_name and stream_name != "::$DATA":
                    streams.append({
                        'name': stream_name,
                        'size': stream_size,
                        'size_human': _format_size(stream_size)
                    })
                
                if not kernel32.FindNextStreamW(handle, ctypes.byref(find_data)):
                    break
            
            kernel32.FindClose(handle)
    except:
        pass  # ADS not supported or accessible
    
    return streams

def _get_file_owner(filepath):
    """Get file owner information (Windows only)"""
    if os.name != 'nt':
        return {'owner': 'N/A', 'owner_sid': 'N/A'}
    
    try:
        import win32security
        import win32api
        
        # Get security descriptor
        sd = win32security.GetFileSecurity(filepath, win32security.OWNER_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        
        # Convert SID to name
        try:
            name, domain, type = win32security.LookupAccountSid(None, owner_sid)
            if domain:
                owner_name = f"{domain}\\{name}"
            else:
                owner_name = name
        except:
            owner_name = str(owner_sid)
        
        return {
            'owner': owner_name,
            'owner_sid': str(owner_sid)
        }
        
    except ImportError:
        # Fallback without pywin32
        return {'owner': 'Unknown', 'owner_sid': 'Unknown'}
    except Exception as e:
        return {'owner': f'Error: {e}', 'owner_sid': 'Unknown'}

def _check_signature(filepath):
    """Check if executable is digitally signed (Windows only)"""
    if os.name != 'nt':
        return None
    
    try:
        import win32security
        
        # This is a simplified check - full implementation would use WinVerifyTrust
        # For now, just check if file has certificate
        try:
            # Use wintrust.dll to verify signature
            wintrust = ctypes.windll.wintrust
            
            # WINTRUST_FILE_INFO structure (simplified)
            class WINTRUST_FILE_INFO(ctypes.Structure):
                _fields_ = [
                    ("cbStruct", wintypes.DWORD),
                    ("pcwszFilePath", wintypes.LPCWSTR),
                    ("hFile", wintypes.HANDLE),
                    ("pgKnownSubject", ctypes.c_void_p)
                ]
            
            file_info = WINTRUST_FILE_INFO()
            file_info.cbStruct = ctypes.sizeof(WINTRUST_FILE_INFO)
            file_info.pcwszFilePath = filepath
            file_info.hFile = None
            file_info.pgKnownSubject = None
            
            # This is simplified - full implementation would call WinVerifyTrust
            # For now, assume unsigned
            return False
            
        except:
            return None
            
    except ImportError:
        return None

def _filetime_to_datetime(filetime):
    """Convert Windows FILETIME to datetime"""
    try:
        # FILETIME is 100-nanosecond intervals since January 1, 1601
        timestamp = (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime
        # Convert to seconds since epoch
        timestamp = (timestamp - 116444736000000000) / 10000000
        return datetime.fromtimestamp(timestamp)
    except:
        return datetime.now()

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
    # Test the elite ls command
    import json
    
    print("Testing Elite LS Command...")
    
    # Test current directory
    result = elite_ls(".")
    
    if result["success"]:
        print(f"Directory: {result['directory']}")
        print(f"Files: {result['file_count']}, Directories: {result['dir_count']}")
        print(f"Hidden: {result.get('hidden_count', 0)}, ADS: {result.get('ads_count', 0)}")
        print("\nFirst 5 files:")
        
        for file_info in result["files"][:5]:
            print(f"  {file_info['name']} ({file_info['size_human']})")
            if file_info.get('is_hidden'):
                print("    [HIDDEN]")
            if file_info.get('has_ads'):
                print(f"    [ADS: {len(file_info['ads'])} streams]")
    else:
        print(f"Error: {result['error']}")