#!/usr/bin/env python3
"""
Elite Lsmod Command - List loaded kernel modules and drivers
Advanced module enumeration with security analysis
"""

import ctypes
from ctypes import wintypes
import subprocess
import os

class EliteLsmod:
    """Elite loaded module enumeration"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.psapi = ctypes.windll.psapi
        
    def execute(self, process_id=None):
        """Get comprehensive loaded module information"""
        try:
            if process_id:
                # Get modules for specific process
                modules_info = self._get_process_modules(process_id)
            else:
                # Get system-wide module information
                modules_info = {
                    'kernel_modules': self._get_kernel_modules(),
                    'system_drivers': self._get_system_drivers(),
                    'loaded_dlls': self._get_loaded_dlls(),
                    'module_analysis': self._analyze_modules()
                }
            
            return {
                'success': True,
                'data': modules_info,
                'message': 'Module enumeration completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Module enumeration failed: {str(e)}'
            }
    
    def _get_kernel_modules(self):
        """Get kernel modules and drivers"""
        try:
            modules = []
            
            # Use driverquery to get driver information
            try:
                result = subprocess.run(['driverquery', '/v', '/fo', 'csv'], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\\n')
                    if len(lines) > 1:
                        headers = [h.strip('"') for h in lines[0].split(',')]
                        
                        for line in lines[1:]:
                            if line.strip():
                                values = [v.strip('"') for v in line.split(',')]
                                if len(values) >= len(headers):
                                    module_info = dict(zip(headers, values))
                                    modules.append({
                                        'name': module_info.get('Module Name', ''),
                                        'display_name': module_info.get('Display Name', ''),
                                        'type': module_info.get('Driver Type', ''),
                                        'start_mode': module_info.get('Start Mode', ''),
                                        'state': module_info.get('State', ''),
                                        'status': module_info.get('Status', ''),
                                        'accept_stop': module_info.get('Accept Stop', ''),
                                        'accept_pause': module_info.get('Accept Pause', ''),
                                        'memory_usage': module_info.get('Paged Pool(bytes)', ''),
                                        'path': module_info.get('Path', '')
                                    })
            except Exception as e:
                modules.append({'error': f'driverquery failed: {str(e)}'})
            
            return modules
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_system_drivers(self):
        """Get system drivers using alternative methods"""
        try:
            drivers = []
            
            # Use PowerShell to get driver information
            try:
                ps_command = """
                Get-WmiObject -Class Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, DriverDate, IsSigned, Signer | ConvertTo-Json
                """
                
                result = subprocess.run(['powershell', '-Command', ps_command], 
                                      capture_output=True, text=True, timeout=20)
                
                if result.returncode == 0:
                    import json
                    try:
                        driver_data = json.loads(result.stdout)
                        if isinstance(driver_data, list):
                            drivers = driver_data
                        else:
                            drivers = [driver_data]
                    except json.JSONDecodeError:
                        drivers.append({'note': 'PowerShell output parsing failed'})
            except Exception as e:
                drivers.append({'error': f'PowerShell query failed: {str(e)}'})
            
            return drivers
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_loaded_dlls(self):
        """Get loaded DLLs from current process"""
        try:
            dlls = []
            
            # Get current process handle
            current_process = self.kernel32.GetCurrentProcess()
            
            # Enumerate modules in current process
            module_handles = (wintypes.HMODULE * 1024)()
            bytes_needed = wintypes.DWORD()
            
            success = self.psapi.EnumProcessModules(
                current_process,
                module_handles,
                ctypes.sizeof(module_handles),
                ctypes.byref(bytes_needed)
            )
            
            if success:
                module_count = bytes_needed.value // ctypes.sizeof(wintypes.HMODULE)
                
                for i in range(min(module_count, 1024)):
                    module_handle = module_handles[i]
                    if module_handle:
                        # Get module information
                        module_info = self._get_module_info(current_process, module_handle)
                        if module_info:
                            dlls.append(module_info)
            
            return dlls
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_process_modules(self, process_id):
        """Get modules for specific process"""
        try:
            modules = []
            
            # Open process
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            
            process_handle = self.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                False,
                process_id
            )
            
            if process_handle:
                try:
                    # Enumerate modules
                    module_handles = (wintypes.HMODULE * 1024)()
                    bytes_needed = wintypes.DWORD()
                    
                    success = self.psapi.EnumProcessModules(
                        process_handle,
                        module_handles,
                        ctypes.sizeof(module_handles),
                        ctypes.byref(bytes_needed)
                    )
                    
                    if success:
                        module_count = bytes_needed.value // ctypes.sizeof(wintypes.HMODULE)
                        
                        for i in range(min(module_count, 1024)):
                            module_handle = module_handles[i]
                            if module_handle:
                                module_info = self._get_module_info(process_handle, module_handle)
                                if module_info:
                                    modules.append(module_info)
                
                finally:
                    self.kernel32.CloseHandle(process_handle)
            
            return {
                'process_id': process_id,
                'modules': modules,
                'module_count': len(modules)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_module_info(self, process_handle, module_handle):
        """Get detailed information about a module"""
        try:
            module_info = {}
            
            # Get module file name
            filename_buffer = ctypes.create_unicode_buffer(260)
            filename_length = self.psapi.GetModuleFileNameExW(
                process_handle,
                module_handle,
                filename_buffer,
                260
            )
            
            if filename_length > 0:
                module_info['filename'] = filename_buffer.value
                module_info['basename'] = os.path.basename(filename_buffer.value)
            
            # Get module information
            class MODULEINFO(ctypes.Structure):
                _fields_ = [
                    ("lpBaseOfDll", ctypes.c_void_p),
                    ("SizeOfImage", wintypes.DWORD),
                    ("EntryPoint", ctypes.c_void_p)
                ]
            
            mod_info = MODULEINFO()
            success = self.psapi.GetModuleInformation(
                process_handle,
                module_handle,
                ctypes.byref(mod_info),
                ctypes.sizeof(mod_info)
            )
            
            if success:
                module_info['base_address'] = hex(mod_info.lpBaseOfDll)
                module_info['size'] = mod_info.SizeOfImage
                module_info['entry_point'] = hex(mod_info.EntryPoint)
                module_info['size_human'] = self._format_bytes(mod_info.SizeOfImage)
            
            # Get version information if available
            if 'filename' in module_info:
                try:
                    import win32api
                    version_info = win32api.GetFileVersionInfo(module_info['filename'], "\\\\")
                    ms = version_info['FileVersionMS']
                    ls = version_info['FileVersionLS']
                    version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                    module_info['version'] = version
                except:
                    module_info['version'] = 'Unknown'
            
            return module_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_modules(self):
        """Analyze loaded modules for security implications"""
        try:
            analysis = {
                'total_drivers': 0,
                'unsigned_drivers': [],
                'suspicious_modules': [],
                'security_notes': [],
                'driver_types': {}
            }
            
            # Analyze kernel modules
            kernel_modules = self._get_kernel_modules()
            analysis['total_drivers'] = len([m for m in kernel_modules if 'error' not in m])
            
            for module in kernel_modules:
                if 'error' not in module:
                    # Count driver types
                    driver_type = module.get('type', 'Unknown')
                    analysis['driver_types'][driver_type] = analysis['driver_types'].get(driver_type, 0) + 1
                    
                    # Check for suspicious characteristics
                    if module.get('state', '').lower() == 'stopped':
                        analysis['suspicious_modules'].append(f"{module.get('name', 'Unknown')} - Stopped state")
                    
                    # Check path for suspicious locations
                    path = module.get('path', '').lower()
                    if path and ('temp' in path or 'users' in path):
                        analysis['suspicious_modules'].append(f"{module.get('name', 'Unknown')} - Suspicious path: {path}")
            
            # Add security notes
            if analysis['suspicious_modules']:
                analysis['security_notes'].append(f"Found {len(analysis['suspicious_modules'])} potentially suspicious modules")
            
            analysis['security_notes'].extend([
                'Review unsigned drivers for legitimacy',
                'Monitor drivers in unusual locations',
                'Check stopped drivers for malware'
            ])
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _format_bytes(self, bytes_value):
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

def elite_lsmod(process_id=None):
    """Elite lsmod command entry point"""
    lsmod_cmd = EliteLsmod()
    return lsmod_cmd.execute(process_id)