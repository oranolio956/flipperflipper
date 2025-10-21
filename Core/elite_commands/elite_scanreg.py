#!/usr/bin/env python3
"""
Elite Scan Registry Command - Advanced Windows registry scanning and analysis
Comprehensive registry analysis with security focus
"""

import ctypes
from ctypes import wintypes
import winreg
import os
import datetime

class EliteScanReg:
    """Elite registry scanning and analysis"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        
    def execute(self, scan_type='security', root_key='HKLM', subkey=None, search_term=None, **kwargs):
        """Scan Windows registry for various purposes"""
        try:
            if scan_type == 'security':
                return self._security_scan(root_key, subkey)
            elif scan_type == 'malware':
                return self._malware_scan()
            elif scan_type == 'persistence':
                return self._persistence_scan()
            elif scan_type == 'credentials':
                return self._credentials_scan()
            elif scan_type == 'network':
                return self._network_scan()
            elif scan_type == 'software':
                return self._software_scan()
            elif scan_type == 'search':
                return self._search_registry(search_term, root_key, subkey)
            elif scan_type == 'recent_activity':
                return self._recent_activity_scan()
            elif scan_type == 'startup':
                return self._startup_scan()
            else:
                return {
                    'success': False,
                    'error': f'Unknown scan type: {scan_type}',
                    'available_types': ['security', 'malware', 'persistence', 'credentials', 'network', 'software', 'search', 'recent_activity', 'startup']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Registry scan failed: {str(e)}'
            }
    
    def _security_scan(self, root_key, subkey):
        """Scan for security-related registry entries"""
        try:
            security_findings = {
                'security_policies': [],
                'user_rights': [],
                'audit_settings': [],
                'firewall_settings': [],
                'defender_settings': [],
                'security_risks': []
            }
            
            # Map root key string to registry constant
            root_key_map = {
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKCU': winreg.HKEY_CURRENT_USER,
                'HKCR': winreg.HKEY_CLASSES_ROOT,
                'HKU': winreg.HKEY_USERS,
                'HKCC': winreg.HKEY_CURRENT_CONFIG
            }
            
            hkey = root_key_map.get(root_key, winreg.HKEY_LOCAL_MACHINE)
            
            # Security policy locations to check
            security_locations = [
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
                r"SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate",
                r"SOFTWARE\\Policies\\Microsoft\\Windows Defender",
                r"SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy",
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update"
            ]
            
            for location in security_locations:
                try:
                    findings = self._scan_registry_key(hkey, location, 'security')
                    if findings:
                        security_findings['security_policies'].extend(findings)
                except Exception:
                    continue
            
            # Check for specific security risks
            risk_indicators = [
                (r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "EnableLUA", "UAC disabled"),
                (r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "ConsentPromptBehaviorAdmin", "UAC weakened"),
                (r"SOFTWARE\\Policies\\Microsoft\\Windows Defender", "DisableAntiSpyware", "Windows Defender disabled"),
                (r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "*", "Suspicious startup entries")
            ]
            
            for reg_path, value_name, risk_desc in risk_indicators:
                try:
                    key = winreg.OpenKey(hkey, reg_path)
                    if value_name == "*":
                        # Check all values in the key
                        i = 0
                        while True:
                            try:
                                name, value, type = winreg.EnumValue(key, i)
                                if self._is_suspicious_startup_entry(name, value):
                                    security_findings['security_risks'].append({
                                        'type': risk_desc,
                                        'location': f"{root_key}\\{reg_path}",
                                        'name': name,
                                        'value': str(value),
                                        'risk_level': 'medium'
                                    })
                                i += 1
                            except OSError:
                                break
                    else:
                        try:
                            value, _ = winreg.QueryValueEx(key, value_name)
                            if self._is_security_risk(value_name, value):
                                security_findings['security_risks'].append({
                                    'type': risk_desc,
                                    'location': f"{root_key}\\{reg_path}",
                                    'name': value_name,
                                    'value': str(value),
                                    'risk_level': 'high'
                                })
                        except FileNotFoundError:
                            pass
                    
                    winreg.CloseKey(key)
                    
                except Exception:
                    continue
            
            return {
                'success': True,
                'scan_type': 'security',
                'findings': security_findings,
                'total_risks': len(security_findings['security_risks']),
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Security scan failed: {str(e)}'
            }
    
    def _malware_scan(self):
        """Scan for malware-related registry entries"""
        try:
            malware_findings = {
                'suspicious_entries': [],
                'known_malware_keys': [],
                'suspicious_services': [],
                'browser_hijacks': []
            }
            
            # Known malware registry locations
            malware_locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Services"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Classes\\exefile\\shell\\open\\command"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options")
            ]
            
            # Suspicious patterns
            suspicious_patterns = [
                'temp', 'tmp', 'appdata', 'roaming', 'local', 
                'system32', 'syswow64', 'programdata', 'users',
                '.exe', '.scr', '.bat', '.cmd', '.pif', '.com'
            ]
            
            for hkey, reg_path in malware_locations:
                try:
                    key = winreg.OpenKey(hkey, reg_path)
                    i = 0
                    
                    # Check subkeys
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if self._is_suspicious_name(subkey_name):
                                malware_findings['suspicious_entries'].append({
                                    'type': 'suspicious_subkey',
                                    'location': reg_path,
                                    'name': subkey_name,
                                    'reason': 'Suspicious naming pattern'
                                })
                            i += 1
                        except OSError:
                            break
                    
                    # Check values
                    i = 0
                    while True:
                        try:
                            name, value, type = winreg.EnumValue(key, i)
                            if self._is_suspicious_value(name, value):
                                malware_findings['suspicious_entries'].append({
                                    'type': 'suspicious_value',
                                    'location': reg_path,
                                    'name': name,
                                    'value': str(value)[:200],  # Limit value length
                                    'reason': 'Suspicious file path or content'
                                })
                            i += 1
                        except OSError:
                            break
                    
                    winreg.CloseKey(key)
                    
                except Exception:
                    continue
            
            # Check for browser hijacking
            browser_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Internet Explorer\\Main"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Internet Explorer\\Main"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Google\\Chrome\\PreferenceMACs\\Default\\homepage"),
            ]
            
            for hkey, reg_path in browser_locations:
                try:
                    findings = self._check_browser_hijack(hkey, reg_path)
                    if findings:
                        malware_findings['browser_hijacks'].extend(findings)
                except Exception:
                    continue
            
            return {
                'success': True,
                'scan_type': 'malware',
                'findings': malware_findings,
                'total_suspicious': len(malware_findings['suspicious_entries']),
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Malware scan failed: {str(e)}'
            }
    
    def _persistence_scan(self):
        """Scan for persistence mechanisms"""
        try:
            persistence_findings = {
                'startup_entries': [],
                'services': [],
                'scheduled_tasks': [],
                'wmi_subscriptions': [],
                'dll_hijacking': []
            }
            
            # Startup locations
            startup_locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunServices"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunServicesOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run"),
            ]
            
            for hkey, reg_path in startup_locations:
                try:
                    entries = self._enumerate_registry_values(hkey, reg_path)
                    for entry in entries:
                        persistence_findings['startup_entries'].append({
                            'location': reg_path,
                            'name': entry['name'],
                            'value': entry['value'],
                            'type': entry['type'],
                            'persistence_method': 'startup'
                        })
                except Exception:
                    continue
            
            # Service persistence
            try:
                services = self._enumerate_services()
                for service in services:
                    if self._is_suspicious_service(service):
                        persistence_findings['services'].append(service)
            except Exception:
                pass
            
            # Check for DLL hijacking opportunities
            try:
                dll_locations = [
                    r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows",
                    r"SYSTEM\\CurrentControlSet\\Control\\Session Manager"
                ]
                
                for location in dll_locations:
                    try:
                        findings = self._check_dll_hijacking(winreg.HKEY_LOCAL_MACHINE, location)
                        if findings:
                            persistence_findings['dll_hijacking'].extend(findings)
                    except Exception:
                        continue
            except Exception:
                pass
            
            return {
                'success': True,
                'scan_type': 'persistence',
                'findings': persistence_findings,
                'total_mechanisms': sum(len(v) for v in persistence_findings.values()),
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Persistence scan failed: {str(e)}'
            }
    
    def _credentials_scan(self):
        """Scan for stored credentials and sensitive data"""
        try:
            credential_findings = {
                'stored_passwords': [],
                'cached_credentials': [],
                'browser_data': [],
                'wifi_profiles': [],
                'sensitive_keys': []
            }
            
            # Credential storage locations
            credential_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Protected Storage System Provider"),
                (winreg.HKEY_LOCAL_MACHINE, r"SECURITY\\Policy\\Secrets"),
                (winreg.HKEY_LOCAL_MACHINE, r"SAM\\Domains\\Account\\Users"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Internet Explorer\\IntelliForms\\Storage2"),
            ]
            
            for hkey, reg_path in credential_locations:
                try:
                    # Note: Many of these keys require special privileges to access
                    findings = self._scan_credential_location(hkey, reg_path)
                    if findings:
                        credential_findings['sensitive_keys'].extend(findings)
                except Exception:
                    # Expected for protected keys
                    continue
            
            # Check for browser credential storage indicators
            browser_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Google\\Chrome\\PreferenceMACs"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Mozilla\\Firefox\\Profiles"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Internet Explorer\\IntelliForms"),
            ]
            
            for hkey, reg_path in browser_locations:
                try:
                    findings = self._check_browser_credentials(hkey, reg_path)
                    if findings:
                        credential_findings['browser_data'].extend(findings)
                except Exception:
                    continue
            
            return {
                'success': True,
                'scan_type': 'credentials',
                'findings': credential_findings,
                'total_findings': sum(len(v) for v in credential_findings.values()),
                'scan_time': datetime.datetime.now().isoformat(),
                'note': 'Many credential locations require elevated privileges to access'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Credentials scan failed: {str(e)}'
            }
    
    def _network_scan(self):
        """Scan for network-related registry entries"""
        try:
            network_findings = {
                'network_shares': [],
                'proxy_settings': [],
                'network_adapters': [],
                'firewall_rules': [],
                'dns_settings': []
            }
            
            # Network configuration locations
            network_locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Services\\lanmanserver\\Shares"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\Class\\{4D36E972-E325-11CE-BFC1-08002BE10318}"),
            ]
            
            for hkey, reg_path in network_locations:
                try:
                    findings = self._scan_network_location(hkey, reg_path)
                    if 'Tcpip' in reg_path:
                        network_findings['dns_settings'].extend(findings)
                    elif 'Internet Settings' in reg_path:
                        network_findings['proxy_settings'].extend(findings)
                    elif 'Shares' in reg_path:
                        network_findings['network_shares'].extend(findings)
                    elif '4D36E972' in reg_path:
                        network_findings['network_adapters'].extend(findings)
                except Exception:
                    continue
            
            return {
                'success': True,
                'scan_type': 'network',
                'findings': network_findings,
                'total_findings': sum(len(v) for v in network_findings.values()),
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Network scan failed: {str(e)}'
            }
    
    def _software_scan(self):
        """Scan for installed software and applications"""
        try:
            software_findings = {
                'installed_programs': [],
                'uninstall_entries': [],
                'suspicious_software': [],
                'software_count': 0
            }
            
            # Software installation locations
            software_locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
            ]
            
            for hkey, reg_path in software_locations:
                try:
                    key = winreg.OpenKey(hkey, reg_path)
                    i = 0
                    
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            
                            # Get software details
                            try:
                                subkey = winreg.OpenKey(key, subkey_name)
                                software_info = self._get_software_info(subkey, subkey_name)
                                
                                if software_info:
                                    software_findings['installed_programs'].append(software_info)
                                    
                                    # Check if software is suspicious
                                    if self._is_suspicious_software(software_info):
                                        software_findings['suspicious_software'].append(software_info)
                                
                                winreg.CloseKey(subkey)
                                
                            except Exception:
                                pass
                            
                            i += 1
                        except OSError:
                            break
                    
                    winreg.CloseKey(key)
                    
                except Exception:
                    continue
            
            software_findings['software_count'] = len(software_findings['installed_programs'])
            
            return {
                'success': True,
                'scan_type': 'software',
                'findings': software_findings,
                'total_software': software_findings['software_count'],
                'suspicious_count': len(software_findings['suspicious_software']),
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Software scan failed: {str(e)}'
            }
    
    def _search_registry(self, search_term, root_key, subkey):
        """Search registry for specific terms"""
        try:
            if not search_term:
                return {
                    'success': False,
                    'error': 'Search term is required'
                }
            
            search_results = {
                'key_matches': [],
                'value_name_matches': [],
                'value_data_matches': [],
                'total_matches': 0
            }
            
            # Map root key
            root_key_map = {
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKCU': winreg.HKEY_CURRENT_USER,
                'HKCR': winreg.HKEY_CLASSES_ROOT,
                'HKU': winreg.HKEY_USERS,
                'HKCC': winreg.HKEY_CURRENT_CONFIG
            }
            
            hkey = root_key_map.get(root_key, winreg.HKEY_LOCAL_MACHINE)
            search_path = subkey if subkey else ""
            
            # Perform recursive search
            matches = self._recursive_search(hkey, search_path, search_term.lower())
            
            search_results['key_matches'] = matches.get('keys', [])
            search_results['value_name_matches'] = matches.get('value_names', [])
            search_results['value_data_matches'] = matches.get('value_data', [])
            search_results['total_matches'] = sum(len(v) for v in matches.values())
            
            return {
                'success': True,
                'scan_type': 'search',
                'search_term': search_term,
                'root_key': root_key,
                'subkey': subkey,
                'results': search_results,
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Registry search failed: {str(e)}'
            }
    
    def _recent_activity_scan(self):
        """Scan for recent user activity in registry"""
        try:
            activity_findings = {
                'recent_docs': [],
                'mru_lists': [],
                'recent_apps': [],
                'user_activity': []
            }
            
            # Recent activity locations
            activity_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\LastVisitedPidlMRU"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths"),
            ]
            
            for hkey, reg_path in activity_locations:
                try:
                    findings = self._scan_activity_location(hkey, reg_path)
                    if 'RecentDocs' in reg_path:
                        activity_findings['recent_docs'].extend(findings)
                    elif 'MRU' in reg_path:
                        activity_findings['mru_lists'].extend(findings)
                    elif 'TypedPaths' in reg_path:
                        activity_findings['user_activity'].extend(findings)
                except Exception:
                    continue
            
            return {
                'success': True,
                'scan_type': 'recent_activity',
                'findings': activity_findings,
                'total_findings': sum(len(v) for v in activity_findings.values()),
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Recent activity scan failed: {str(e)}'
            }
    
    def _startup_scan(self):
        """Comprehensive startup programs scan"""
        try:
            startup_findings = {
                'run_keys': [],
                'services': [],
                'scheduled_tasks': [],
                'startup_folders': [],
                'total_startup_items': 0
            }
            
            # All startup locations
            startup_locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run"),
            ]
            
            for hkey, reg_path in startup_locations:
                try:
                    entries = self._enumerate_registry_values(hkey, reg_path)
                    for entry in entries:
                        startup_findings['run_keys'].append({
                            'location': reg_path,
                            'name': entry['name'],
                            'command': entry['value'],
                            'type': 'registry_run_key'
                        })
                except Exception:
                    continue
            
            startup_findings['total_startup_items'] = len(startup_findings['run_keys'])
            
            return {
                'success': True,
                'scan_type': 'startup',
                'findings': startup_findings,
                'total_items': startup_findings['total_startup_items'],
                'scan_time': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Startup scan failed: {str(e)}'
            }
    
    # Helper methods
    def _scan_registry_key(self, hkey, reg_path, scan_context):
        """Generic registry key scanner"""
        try:
            findings = []
            key = winreg.OpenKey(hkey, reg_path)
            
            # Enumerate values
            i = 0
            while True:
                try:
                    name, value, type = winreg.EnumValue(key, i)
                    findings.append({
                        'name': name,
                        'value': str(value),
                        'type': type,
                        'location': reg_path
                    })
                    i += 1
                except OSError:
                    break
            
            winreg.CloseKey(key)
            return findings
            
        except Exception:
            return []
    
    def _enumerate_registry_values(self, hkey, reg_path):
        """Enumerate all values in a registry key"""
        try:
            values = []
            key = winreg.OpenKey(hkey, reg_path)
            
            i = 0
            while True:
                try:
                    name, value, type = winreg.EnumValue(key, i)
                    values.append({
                        'name': name,
                        'value': str(value),
                        'type': type
                    })
                    i += 1
                except OSError:
                    break
            
            winreg.CloseKey(key)
            return values
            
        except Exception:
            return []
    
    def _is_suspicious_name(self, name):
        """Check if a registry key/value name is suspicious"""
        suspicious_patterns = [
            'temp', 'tmp', 'cache', 'svchost', 'winlogon', 'explorer',
            'system', 'microsoft', 'windows', 'update', 'security'
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in suspicious_patterns)
    
    def _is_suspicious_value(self, name, value):
        """Check if a registry value is suspicious"""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        suspicious_paths = [
            'temp', 'tmp', 'appdata', 'programdata', 'system32',
            'syswow64', 'users', 'documents'
        ]
        
        return any(path in value_lower for path in suspicious_paths)
    
    def _is_security_risk(self, name, value):
        """Check if a registry value represents a security risk"""
        security_risks = {
            'EnableLUA': lambda v: v == 0,  # UAC disabled
            'ConsentPromptBehaviorAdmin': lambda v: v == 0,  # UAC weakened
            'DisableAntiSpyware': lambda v: v == 1,  # Defender disabled
        }
        
        risk_check = security_risks.get(name)
        return risk_check(value) if risk_check else False
    
    def _recursive_search(self, hkey, path, search_term, max_depth=3, current_depth=0):
        """Recursively search registry"""
        matches = {'keys': [], 'value_names': [], 'value_data': []}
        
        if current_depth >= max_depth:
            return matches
        
        try:
            key = winreg.OpenKey(hkey, path) if path else hkey
            
            # Search subkeys
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    if search_term in subkey_name.lower():
                        matches['keys'].append(f"{path}\\{subkey_name}" if path else subkey_name)
                    
                    # Recurse into subkey (limited depth)
                    if current_depth < max_depth - 1:
                        subpath = f"{path}\\{subkey_name}" if path else subkey_name
                        sub_matches = self._recursive_search(hkey, subpath, search_term, max_depth, current_depth + 1)
                        for match_type in matches:
                            matches[match_type].extend(sub_matches[match_type])
                    
                    i += 1
                except OSError:
                    break
            
            # Search values
            i = 0
            while True:
                try:
                    name, value, type = winreg.EnumValue(key, i)
                    if search_term in name.lower():
                        matches['value_names'].append(f"{path}\\{name}" if path else name)
                    if search_term in str(value).lower():
                        matches['value_data'].append(f"{path}\\{name}" if path else name)
                    i += 1
                except OSError:
                    break
            
            if path:  # Only close if we opened a subkey
                winreg.CloseKey(key)
                
        except Exception:
            pass
        
        return matches

def elite_scanreg(scan_type='security', root_key='HKLM', subkey=None, search_term=None, **kwargs):
    """Elite scanreg command entry point"""
    scanreg_cmd = EliteScanReg()
    return scanreg_cmd.execute(scan_type, root_key, subkey, search_term, **kwargs)