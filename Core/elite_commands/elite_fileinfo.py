#!/usr/bin/env python3
"""
Elite File Info Command - Comprehensive file metadata analysis
Advanced file information gathering with forensic details
"""

import ctypes
from ctypes import wintypes
import os
import hashlib
import datetime
import struct

class EliteFileInfo:
    """Elite file information gathering with advanced analysis"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32
        
    def execute(self, filepath):
        """Get comprehensive file information"""
        try:
            if not os.path.exists(filepath):
                return {
                    'success': False,
                    'error': f'File not found: {filepath}'
                }
            
            info = {
                'filepath': filepath,
                'basic_info': self._get_basic_info(filepath),
                'attributes': self._get_file_attributes(filepath),
                'timestamps': self._get_timestamps(filepath),
                'security': self._get_security_info(filepath),
                'hashes': self._get_file_hashes(filepath),
                'metadata': self._get_metadata(filepath),
                'alternate_streams': self._get_alternate_streams(filepath),
                'pe_info': self._get_pe_info(filepath) if filepath.lower().endswith(('.exe', '.dll', '.sys')) else None
            }
            
            return {
                'success': True,
                'data': info,
                'message': f'File information gathered for: {filepath}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get file info: {str(e)}',
                'filepath': filepath
            }
    
    def _get_basic_info(self, filepath):
        """Get basic file information"""
        try:
            stat = os.stat(filepath)
            return {
                'size': stat.st_size,
                'size_human': self._format_size(stat.st_size),
                'is_file': os.path.isfile(filepath),
                'is_directory': os.path.isdir(filepath),
                'is_link': os.path.islink(filepath),
                'extension': os.path.splitext(filepath)[1].lower()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_file_attributes(self, filepath):
        """Get Windows file attributes"""
        try:
            attrs = self.kernel32.GetFileAttributesW(filepath)
            if attrs == -1:
                return {'error': 'Failed to get attributes'}
            
            return {
                'hidden': bool(attrs & 0x02),
                'system': bool(attrs & 0x04),
                'directory': bool(attrs & 0x10),
                'archive': bool(attrs & 0x20),
                'device': bool(attrs & 0x40),
                'normal': bool(attrs & 0x80),
                'temporary': bool(attrs & 0x100),
                'sparse': bool(attrs & 0x200),
                'reparse_point': bool(attrs & 0x400),
                'compressed': bool(attrs & 0x800),
                'offline': bool(attrs & 0x1000),
                'not_indexed': bool(attrs & 0x2000),
                'encrypted': bool(attrs & 0x4000),
                'raw_value': hex(attrs)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_timestamps(self, filepath):
        """Get file timestamps"""
        try:
            # Get handle to file
            handle = self.kernel32.CreateFileW(
                filepath,
                0x80000000,  # GENERIC_READ
                3,           # FILE_SHARE_READ | FILE_SHARE_WRITE
                None,
                3,           # OPEN_EXISTING
                0x02000000,  # FILE_FLAG_BACKUP_SEMANTICS
                None
            )
            
            if handle == -1:
                stat = os.stat(filepath)
                return {
                    'created': datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'accessed': datetime.datetime.fromtimestamp(stat.st_atime).isoformat(),
                    'source': 'os.stat (fallback)'
                }
            
            # Get file times
            creation_time = wintypes.FILETIME()
            access_time = wintypes.FILETIME()
            write_time = wintypes.FILETIME()
            
            success = self.kernel32.GetFileTime(
                handle,
                ctypes.byref(creation_time),
                ctypes.byref(access_time),
                ctypes.byref(write_time)
            )
            
            self.kernel32.CloseHandle(handle)
            
            if success:
                return {
                    'created': self._filetime_to_datetime(creation_time).isoformat(),
                    'accessed': self._filetime_to_datetime(access_time).isoformat(),
                    'modified': self._filetime_to_datetime(write_time).isoformat(),
                    'source': 'Windows API'
                }
            else:
                return {'error': 'Failed to get file times'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_security_info(self, filepath):
        """Get file security information"""
        try:
            # Get file owner
            security_info = {}
            
            # This is a simplified version - full implementation would use GetFileSecurity
            try:
                import win32security
                import win32api
                
                sd = win32security.GetFileSecurity(filepath, win32security.OWNER_SECURITY_INFORMATION)
                owner_sid = sd.GetSecurityDescriptorOwner()
                name, domain, type = win32security.LookupAccountSid(None, owner_sid)
                
                security_info['owner'] = f"{domain}\\{name}"
                security_info['owner_sid'] = str(owner_sid)
                
            except ImportError:
                security_info['owner'] = 'Unknown (win32security not available)'
            except Exception as e:
                security_info['owner'] = f'Error: {str(e)}'
            
            return security_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_file_hashes(self, filepath):
        """Calculate file hashes"""
        try:
            hashes = {}
            
            # Only calculate hashes for files smaller than 100MB to avoid performance issues
            if os.path.getsize(filepath) > 100 * 1024 * 1024:
                return {'note': 'File too large for hash calculation (>100MB)'}
            
            with open(filepath, 'rb') as f:
                content = f.read()
                
                hashes['md5'] = hashlib.md5(content).hexdigest()
                hashes['sha1'] = hashlib.sha1(content).hexdigest()
                hashes['sha256'] = hashlib.sha256(content).hexdigest()
            
            return hashes
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_metadata(self, filepath):
        """Get file metadata"""
        try:
            metadata = {}
            
            # Get version info for executables
            if filepath.lower().endswith(('.exe', '.dll')):
                try:
                    import win32api
                    info = win32api.GetFileVersionInfo(filepath, "\\")
                    ms = info['FileVersionMS']
                    ls = info['FileVersionLS']
                    version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                    metadata['version'] = version
                except:
                    metadata['version'] = 'Unknown'
            
            return metadata
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_alternate_streams(self, filepath):
        """Get alternate data streams"""
        try:
            streams = []
            
            # Use FindFirstStreamW to enumerate streams
            # This is a simplified version - full implementation would use proper structures
            try:
                import subprocess
                result = subprocess.run(['dir', '/r', filepath], 
                                      capture_output=True, text=True, shell=True)
                if ':' in result.stdout:
                    streams.append('Alternate streams detected (use streams.exe for details)')
            except:
                pass
            
            return streams if streams else ['No alternate streams']
            
        except Exception as e:
            return ['Error checking streams']
    
    def _get_pe_info(self, filepath):
        """Get PE file information"""
        try:
            pe_info = {}
            
            with open(filepath, 'rb') as f:
                # Read DOS header
                dos_header = f.read(64)
                if len(dos_header) < 64 or dos_header[:2] != b'MZ':
                    return {'error': 'Not a valid PE file'}
                
                # Get PE header offset
                pe_offset = struct.unpack('<I', dos_header[60:64])[0]
                f.seek(pe_offset)
                
                # Read PE signature
                pe_sig = f.read(4)
                if pe_sig != b'PE\\x00\\x00':
                    return {'error': 'Invalid PE signature'}
                
                # Read COFF header
                coff_header = f.read(20)
                machine, sections, timestamp = struct.unpack('<HHI', coff_header[:8])
                
                pe_info['machine'] = hex(machine)
                pe_info['sections'] = sections
                pe_info['timestamp'] = datetime.datetime.fromtimestamp(timestamp).isoformat()
                pe_info['compile_date'] = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            return pe_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _filetime_to_datetime(self, filetime):
        """Convert Windows FILETIME to datetime"""
        # FILETIME is 100-nanosecond intervals since January 1, 1601
        timestamp = (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime
        # Convert to seconds since Unix epoch
        unix_timestamp = (timestamp / 10000000.0) - 11644473600
        return datetime.datetime.fromtimestamp(unix_timestamp)
    
    def _format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

def elite_fileinfo(filepath):
    """Elite fileinfo command entry point"""
    fileinfo_cmd = EliteFileInfo()
    return fileinfo_cmd.execute(filepath)