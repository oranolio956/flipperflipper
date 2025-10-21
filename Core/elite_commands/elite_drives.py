#!/usr/bin/env python3
"""
Elite Drives Command - Comprehensive drive and storage analysis
Advanced drive enumeration with forensic details
"""

import ctypes
from ctypes import wintypes
import os
import subprocess

class EliteDrives:
    """Elite drive enumeration and analysis"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        
    def execute(self):
        """Get comprehensive drive information"""
        try:
            drives_info = {
                'logical_drives': self._get_logical_drives(),
                'physical_drives': self._get_physical_drives(),
                'network_drives': self._get_network_drives(),
                'removable_drives': self._get_removable_drives(),
                'drive_analysis': self._analyze_drives(),
                'security_assessment': self._assess_drive_security()
            }
            
            return {
                'success': True,
                'data': drives_info,
                'message': f'Found {len(drives_info["logical_drives"])} logical drives'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Drive enumeration failed: {str(e)}'
            }
    
    def _get_logical_drives(self):
        """Get logical drive information"""
        drives = []
        
        try:
            # Get drive bitmask
            drive_mask = self.kernel32.GetLogicalDrives()
            
            for i in range(26):  # A-Z
                if drive_mask & (1 << i):
                    drive_letter = chr(ord('A') + i)
                    drive_path = f"{drive_letter}:\\\\"
                    
                    drive_info = {
                        'letter': drive_letter,
                        'path': drive_path,
                        'type': self._get_drive_type(drive_path),
                        'file_system': self._get_file_system(drive_path),
                        'space_info': self._get_space_info(drive_path),
                        'volume_info': self._get_volume_info(drive_path),
                        'attributes': self._get_drive_attributes(drive_path)
                    }
                    
                    drives.append(drive_info)
            
            return drives
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_drive_type(self, drive_path):
        """Get drive type"""
        try:
            drive_type = self.kernel32.GetDriveTypeW(drive_path)
            
            type_map = {
                0: 'UNKNOWN',
                1: 'NO_ROOT_DIR',
                2: 'REMOVABLE',
                3: 'FIXED',
                4: 'REMOTE',
                5: 'CDROM',
                6: 'RAMDISK'
            }
            
            return {
                'code': drive_type,
                'name': type_map.get(drive_type, 'UNKNOWN'),
                'description': self._get_drive_type_description(drive_type)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_file_system(self, drive_path):
        """Get file system information"""
        try:
            volume_name = ctypes.create_unicode_buffer(261)
            file_system = ctypes.create_unicode_buffer(261)
            serial_number = wintypes.DWORD()
            max_component_length = wintypes.DWORD()
            file_system_flags = wintypes.DWORD()
            
            success = self.kernel32.GetVolumeInformationW(
                drive_path,
                volume_name, 261,
                ctypes.byref(serial_number),
                ctypes.byref(max_component_length),
                ctypes.byref(file_system_flags),
                file_system, 261
            )
            
            if success:
                return {
                    'type': file_system.value,
                    'volume_name': volume_name.value,
                    'serial_number': hex(serial_number.value),
                    'max_component_length': max_component_length.value,
                    'flags': self._parse_file_system_flags(file_system_flags.value)
                }
            else:
                return {'error': 'Failed to get file system info'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_space_info(self, drive_path):
        """Get drive space information"""
        try:
            free_bytes = wintypes.ULARGE_INTEGER()
            total_bytes = wintypes.ULARGE_INTEGER()
            total_free_bytes = wintypes.ULARGE_INTEGER()
            
            success = self.kernel32.GetDiskFreeSpaceExW(
                drive_path,
                ctypes.byref(free_bytes),
                ctypes.byref(total_bytes),
                ctypes.byref(total_free_bytes)
            )
            
            if success:
                total = total_bytes.value
                free = free_bytes.value
                used = total - free
                
                return {
                    'total_bytes': total,
                    'free_bytes': free,
                    'used_bytes': used,
                    'total_human': self._format_bytes(total),
                    'free_human': self._format_bytes(free),
                    'used_human': self._format_bytes(used),
                    'usage_percent': round((used / total * 100), 2) if total > 0 else 0
                }
            else:
                return {'error': 'Failed to get space info'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_volume_info(self, drive_path):
        """Get volume information"""
        try:
            # Get volume GUID
            volume_guid = ctypes.create_unicode_buffer(50)
            success = self.kernel32.GetVolumeNameForVolumeMountPointW(
                drive_path, volume_guid, 50
            )
            
            volume_info = {}
            if success:
                volume_info['guid'] = volume_guid.value
            
            # Get volume paths
            try:
                paths_buffer = ctypes.create_unicode_buffer(1024)
                paths_length = wintypes.DWORD()
                
                if volume_info.get('guid'):
                    success = self.kernel32.GetVolumePathNamesForVolumeNameW(
                        volume_info['guid'],
                        paths_buffer, 1024,
                        ctypes.byref(paths_length)
                    )
                    
                    if success:
                        paths = paths_buffer.value.split('\\x00')
                        volume_info['mount_points'] = [p for p in paths if p]
            except:
                pass
            
            return volume_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_drive_attributes(self, drive_path):
        """Get drive attributes and properties"""
        try:
            attributes = {}
            
            # Check if drive is ready
            try:
                os.listdir(drive_path)
                attributes['ready'] = True
            except:
                attributes['ready'] = False
            
            # Check if drive is compressed
            try:
                attrs = self.kernel32.GetFileAttributesW(drive_path)
                attributes['compressed'] = bool(attrs & 0x800)
            except:
                attributes['compressed'] = False
            
            return attributes
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_physical_drives(self):
        """Get physical drive information"""
        try:
            physical_drives = []
            
            # Use WMI to get physical drive info
            try:
                import subprocess
                result = subprocess.run([
                    'wmic', 'diskdrive', 'get', 
                    'DeviceID,Model,Size,MediaType,InterfaceType',
                    '/format:csv'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\\n')[1:]  # Skip header
                    for line in lines:
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) >= 6:
                                physical_drives.append({
                                    'device_id': parts[1],
                                    'interface_type': parts[2],
                                    'media_type': parts[3],
                                    'model': parts[4],
                                    'size': parts[5]
                                })
            except:
                physical_drives.append({'note': 'WMI query failed, using fallback method'})
            
            return physical_drives
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_network_drives(self):
        """Get network drive mappings"""
        try:
            network_drives = []
            
            # Use net use command to get network drives
            try:
                result = subprocess.run(['net', 'use'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\\n')
                    for line in lines:
                        if ':' in line and '\\\\\\\\' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                network_drives.append({
                                    'local_drive': parts[1] if len(parts) > 1 else '',
                                    'remote_path': parts[2] if len(parts) > 2 else '',
                                    'status': parts[0] if len(parts) > 0 else ''
                                })
            except:
                pass
            
            return network_drives
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_removable_drives(self):
        """Get removable drive information"""
        try:
            removable_drives = []
            
            # Check each logical drive for removable type
            drive_mask = self.kernel32.GetLogicalDrives()
            
            for i in range(26):  # A-Z
                if drive_mask & (1 << i):
                    drive_letter = chr(ord('A') + i)
                    drive_path = f"{drive_letter}:\\\\"
                    
                    drive_type = self.kernel32.GetDriveTypeW(drive_path)
                    if drive_type == 2:  # REMOVABLE
                        removable_drives.append({
                            'letter': drive_letter,
                            'path': drive_path,
                            'ready': self._is_drive_ready(drive_path)
                        })
            
            return removable_drives
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _analyze_drives(self):
        """Analyze drives for interesting characteristics"""
        analysis = {
            'total_drives': 0,
            'drive_types': {},
            'file_systems': {},
            'total_space': 0,
            'total_free': 0,
            'security_notes': []
        }
        
        try:
            logical_drives = self._get_logical_drives()
            analysis['total_drives'] = len(logical_drives)
            
            for drive in logical_drives:
                # Count drive types
                if 'type' in drive and 'name' in drive['type']:
                    drive_type = drive['type']['name']
                    analysis['drive_types'][drive_type] = analysis['drive_types'].get(drive_type, 0) + 1
                
                # Count file systems
                if 'file_system' in drive and 'type' in drive['file_system']:
                    fs_type = drive['file_system']['type']
                    analysis['file_systems'][fs_type] = analysis['file_systems'].get(fs_type, 0) + 1
                
                # Sum space
                if 'space_info' in drive:
                    space = drive['space_info']
                    if 'total_bytes' in space:
                        analysis['total_space'] += space['total_bytes']
                    if 'free_bytes' in space:
                        analysis['total_free'] += space['free_bytes']
            
            # Add security notes
            if 'REMOVABLE' in analysis['drive_types']:
                analysis['security_notes'].append('Removable drives detected - potential data exfiltration risk')
            
            if 'REMOTE' in analysis['drive_types']:
                analysis['security_notes'].append('Network drives detected - check access controls')
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _assess_drive_security(self):
        """Assess drive security configuration"""
        assessment = {
            'risk_level': 'LOW',
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check for unencrypted drives
            logical_drives = self._get_logical_drives()
            
            for drive in logical_drives:
                if drive.get('type', {}).get('name') == 'FIXED':
                    # Check if BitLocker is enabled (simplified check)
                    drive_letter = drive.get('letter', '')
                    if drive_letter:
                        # This is a basic check - full implementation would use proper BitLocker APIs
                        assessment['issues'].append(f'Drive {drive_letter}: BitLocker status unknown')
            
            # Check for removable drives
            removable_drives = self._get_removable_drives()
            if removable_drives:
                assessment['issues'].append(f'{len(removable_drives)} removable drives detected')
                assessment['risk_level'] = 'MEDIUM'
                assessment['recommendations'].append('Implement removable media controls')
            
            return assessment
            
        except Exception as e:
            return {'error': str(e)}
    
    def _parse_file_system_flags(self, flags):
        """Parse file system flags"""
        flag_map = {
            0x00000001: 'FILE_CASE_SENSITIVE_SEARCH',
            0x00000002: 'FILE_CASE_PRESERVED_NAMES',
            0x00000004: 'FILE_UNICODE_ON_DISK',
            0x00000008: 'FILE_PERSISTENT_ACLS',
            0x00000010: 'FILE_FILE_COMPRESSION',
            0x00000020: 'FILE_VOLUME_QUOTAS',
            0x00000040: 'FILE_SUPPORTS_SPARSE_FILES',
            0x00000080: 'FILE_SUPPORTS_REPARSE_POINTS',
            0x00000100: 'FILE_SUPPORTS_REMOTE_STORAGE',
            0x00008000: 'FILE_VOLUME_IS_COMPRESSED',
            0x00010000: 'FILE_SUPPORTS_OBJECT_IDS',
            0x00020000: 'FILE_SUPPORTS_ENCRYPTION',
            0x00040000: 'FILE_NAMED_STREAMS',
            0x00080000: 'FILE_READ_ONLY_VOLUME'
        }
        
        active_flags = []
        for flag_value, flag_name in flag_map.items():
            if flags & flag_value:
                active_flags.append(flag_name)
        
        return active_flags
    
    def _get_drive_type_description(self, drive_type):
        """Get human readable drive type description"""
        descriptions = {
            0: 'The drive type cannot be determined',
            1: 'The root path is invalid',
            2: 'Removable drive (floppy, USB, etc.)',
            3: 'Fixed drive (hard disk, SSD)',
            4: 'Network drive',
            5: 'CD-ROM/DVD drive',
            6: 'RAM disk'
        }
        return descriptions.get(drive_type, 'Unknown drive type')
    
    def _is_drive_ready(self, drive_path):
        """Check if drive is ready for access"""
        try:
            os.listdir(drive_path)
            return True
        except:
            return False
    
    def _format_bytes(self, bytes_value):
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} EB"

def elite_drives():
    """Elite drives command entry point"""
    drives_cmd = EliteDrives()
    return drives_cmd.execute()