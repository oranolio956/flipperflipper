#!/usr/bin/env python3
"""
Elite Environment Command - Comprehensive environment variable analysis
Advanced environment information gathering with security context
"""

import ctypes
from ctypes import wintypes
import os
import subprocess

class EliteEnvironment:
    """Elite environment variable analysis"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32
        
    def execute(self, variable_name=None):
        """Get comprehensive environment information"""
        try:
            if variable_name:
                # Get specific environment variable
                return self._get_specific_variable(variable_name)
            else:
                # Get all environment variables with analysis
                return self._get_all_variables()
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Environment analysis failed: {str(e)}'
            }
    
    def _get_specific_variable(self, variable_name):
        """Get specific environment variable with details"""
        try:
            # Get from current process environment
            current_value = os.environ.get(variable_name)
            
            # Get from system environment
            system_value = self._get_system_variable(variable_name)
            
            # Get from user environment  
            user_value = self._get_user_variable(variable_name)
            
            result = {
                'success': True,
                'variable': variable_name,
                'current_process': current_value,
                'system_level': system_value,
                'user_level': user_value,
                'analysis': self._analyze_variable(variable_name, current_value)
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get variable {variable_name}: {str(e)}'
            }
    
    def _get_all_variables(self):
        """Get all environment variables with comprehensive analysis"""
        try:
            all_vars = {}
            sensitive_vars = []
            path_vars = []
            security_relevant = []
            
            # Get all current environment variables
            for key, value in os.environ.items():
                all_vars[key] = {
                    'value': value,
                    'length': len(value),
                    'type': self._classify_variable(key, value)
                }
                
                # Classify variables
                if self._is_sensitive_variable(key):
                    sensitive_vars.append(key)
                
                if 'PATH' in key.upper():
                    path_vars.append(key)
                
                if self._is_security_relevant(key):
                    security_relevant.append(key)
            
            # Get system PATH analysis
            path_analysis = self._analyze_path_variable()
            
            # Get process environment block info
            peb_info = self._get_peb_environment_info()
            
            result = {
                'success': True,
                'total_variables': len(all_vars),
                'variables': all_vars,
                'classification': {
                    'sensitive': sensitive_vars,
                    'path_related': path_vars,
                    'security_relevant': security_relevant
                },
                'path_analysis': path_analysis,
                'peb_info': peb_info,
                'security_assessment': self._assess_environment_security()
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to analyze environment: {str(e)}'
            }
    
    def _get_system_variable(self, variable_name):
        """Get system-level environment variable"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment") as key:
                try:
                    value, _ = winreg.QueryValueEx(key, variable_name)
                    return value
                except FileNotFoundError:
                    return None
        except Exception:
            return None
    
    def _get_user_variable(self, variable_name):
        """Get user-level environment variable"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                try:
                    value, _ = winreg.QueryValueEx(key, variable_name)
                    return value
                except FileNotFoundError:
                    return None
        except Exception:
            return None
    
    def _classify_variable(self, key, value):
        """Classify environment variable type"""
        key_upper = key.upper()
        
        if 'PATH' in key_upper:
            return 'PATH'
        elif key_upper in ['USERNAME', 'USER', 'LOGNAME']:
            return 'USER_IDENTITY'
        elif key_upper in ['COMPUTERNAME', 'HOSTNAME']:
            return 'SYSTEM_IDENTITY'
        elif key_upper in ['TEMP', 'TMP', 'TMPDIR']:
            return 'TEMPORARY'
        elif key_upper.startswith('PROCESSOR_'):
            return 'HARDWARE'
        elif key_upper in ['OS', 'OSTYPE', 'WINDIR', 'SYSTEMROOT']:
            return 'SYSTEM'
        elif '\\\\' in value or '/' in value:
            return 'PATH_LIKE'
        else:
            return 'GENERAL'
    
    def _is_sensitive_variable(self, key):
        """Check if variable contains sensitive information"""
        sensitive_patterns = [
            'PASSWORD', 'PASS', 'SECRET', 'KEY', 'TOKEN', 'AUTH',
            'CREDENTIAL', 'API_KEY', 'ACCESS_TOKEN', 'SESSION'
        ]
        key_upper = key.upper()
        return any(pattern in key_upper for pattern in sensitive_patterns)
    
    def _is_security_relevant(self, key):
        """Check if variable is security relevant"""
        security_patterns = [
            'PROCESSOR_', 'OS', 'WINDIR', 'SYSTEMROOT', 'PROGRAMFILES',
            'COMMONPROGRAMFILES', 'ALLUSERSPROFILE', 'APPDATA'
        ]
        key_upper = key.upper()
        return any(key_upper.startswith(pattern) for pattern in security_patterns)
    
    def _analyze_variable(self, key, value):
        """Analyze specific variable for security implications"""
        analysis = {
            'classification': self._classify_variable(key, value),
            'sensitive': self._is_sensitive_variable(key),
            'security_relevant': self._is_security_relevant(key),
            'potential_issues': []
        }
        
        if value:
            # Check for potential security issues
            if '\\\\' in value and 'admin$' in value.lower():
                analysis['potential_issues'].append('Contains admin share reference')
            
            if len(value) > 1000:
                analysis['potential_issues'].append('Unusually long value')
            
            if any(char in value for char in ['<', '>', '|', '&']):
                analysis['potential_issues'].append('Contains shell metacharacters')
        
        return analysis
    
    def _analyze_path_variable(self):
        """Analyze PATH variable for security issues"""
        try:
            path_value = os.environ.get('PATH', '')
            paths = path_value.split(os.pathsep)
            
            analysis = {
                'total_paths': len(paths),
                'paths': paths,
                'issues': [],
                'writable_paths': [],
                'non_existent_paths': []
            }
            
            for path in paths:
                if not path.strip():
                    continue
                    
                # Check if path exists
                if not os.path.exists(path):
                    analysis['non_existent_paths'].append(path)
                
                # Check if path is writable (security risk)
                try:
                    if os.access(path, os.W_OK):
                        analysis['writable_paths'].append(path)
                except:
                    pass
                
                # Check for relative paths (security risk)
                if not os.path.isabs(path):
                    analysis['issues'].append(f'Relative path in PATH: {path}')
                
                # Check for current directory in PATH
                if path in ['.', '']:
                    analysis['issues'].append('Current directory (.) in PATH - security risk')
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_peb_environment_info(self):
        """Get Process Environment Block information"""
        try:
            # This is a simplified version - full implementation would access PEB directly
            peb_info = {
                'environment_size': len(str(dict(os.environ))),
                'variable_count': len(os.environ),
                'note': 'PEB direct access requires advanced techniques'
            }
            
            return peb_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _assess_environment_security(self):
        """Assess overall environment security"""
        assessment = {
            'risk_level': 'LOW',
            'issues': [],
            'recommendations': []
        }
        
        # Check for common security issues
        path_value = os.environ.get('PATH', '')
        if '.' in path_value.split(os.pathsep):
            assessment['issues'].append('Current directory in PATH')
            assessment['risk_level'] = 'MEDIUM'
        
        # Check for sensitive variables
        sensitive_count = sum(1 for key in os.environ.keys() if self._is_sensitive_variable(key))
        if sensitive_count > 0:
            assessment['issues'].append(f'{sensitive_count} potentially sensitive variables found')
            if sensitive_count > 3:
                assessment['risk_level'] = 'HIGH'
        
        # Add recommendations
        if assessment['issues']:
            assessment['recommendations'].extend([
                'Review PATH variable for security risks',
                'Audit sensitive environment variables',
                'Remove unnecessary variables'
            ])
        
        return assessment

def elite_environment(variable_name=None):
    """Elite environment command entry point"""
    env_cmd = EliteEnvironment()
    return env_cmd.execute(variable_name)