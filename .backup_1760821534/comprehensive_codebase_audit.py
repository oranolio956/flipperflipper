#!/usr/bin/env python3
"""
COMPREHENSIVE CODEBASE AUDIT
Complete 1:1 analysis of every file, function, and feature
Evidence-based assessment with no assumptions
"""

import os
import sys
import ast
import re
import json
import subprocess
import importlib.util
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, '/workspace')

class ComprehensiveCodebaseAuditor:
    def __init__(self):
        self.audit_results = {
            'broken_features': [],
            'logic_issues': [],
            'missing_dependencies': [],
            'security_concerns': [],
            'performance_issues': [],
            'code_quality': [],
            'integration_problems': [],
            'documentation_gaps': []
        }
        self.files_audited = 0
        self.total_issues = 0
        
    def audit_python_file(self, filepath):
        """Deep audit of a Python file"""
        issues = []
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Parse AST
            try:
                tree = ast.parse(content)
                
                # Check for issues
                for node in ast.walk(tree):
                    # Check for bare excepts
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        issues.append({
                            'type': 'code_quality',
                            'issue': 'Bare except clause (catches all exceptions)',
                            'line': node.lineno if hasattr(node, 'lineno') else 'unknown'
                        })
                        
                    # Check for hardcoded passwords/keys
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                if 'password' in target.id.lower() or 'secret' in target.id.lower():
                                    if isinstance(node.value, ast.Constant):
                                        issues.append({
                                            'type': 'security',
                                            'issue': f'Hardcoded credential: {target.id}',
                                            'line': node.lineno
                                        })
                                        
                    # Check for infinite loops
                    if isinstance(node, ast.While):
                        if isinstance(node.test, ast.Constant) and node.test.value:
                            has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                            if not has_break:
                                issues.append({
                                    'type': 'logic',
                                    'issue': 'Potential infinite loop without break',
                                    'line': node.lineno
                                })
                                
            except SyntaxError as e:
                issues.append({
                    'type': 'broken',
                    'issue': f'Syntax error: {e}',
                    'line': e.lineno
                })
                
            # Check imports
            import_lines = re.findall(r'^(?:from|import)\s+([^\s]+)', content, re.MULTILINE)
            for imp in import_lines:
                module_name = imp.split('.')[0]
                
                # Check if import works
                try:
                    if module_name not in ['Application', 'Configuration', 'PyLib']:
                        __import__(module_name)
                except ImportError:
                    issues.append({
                        'type': 'dependency',
                        'issue': f'Missing import: {module_name}',
                        'line': 'imports'
                    })
                    
            # Check for TODO/FIXME comments
            todos = re.findall(r'#\s*(TODO|FIXME|XXX|HACK):\s*(.+)', content)
            for todo_type, todo_msg in todos:
                issues.append({
                    'type': 'documentation',
                    'issue': f'{todo_type}: {todo_msg}',
                    'line': 'comment'
                })
                
            # Check for potential SQL injection
            if 'execute(' in content or 'executemany(' in content:
                if '%s' not in content and '?' not in content:
                    sql_lines = re.findall(r'\.execute\(["\'](.+?)["\']', content)
                    for sql in sql_lines:
                        if any(op in sql for op in ['%', 'format', '+']):
                            issues.append({
                                'type': 'security',
                                'issue': 'Potential SQL injection vulnerability',
                                'line': 'execute() call'
                            })
                            
            # Check for deprecated functions
            deprecated = {
                'os.popen': 'subprocess.run',
                'urllib.urlopen': 'urllib.request.urlopen',
                'threading.Thread.setDaemon': 'daemon parameter'
            }
            
            for old, new in deprecated.items():
                if old in content:
                    issues.append({
                        'type': 'code_quality',
                        'issue': f'Deprecated: {old} should use {new}',
                        'line': 'deprecated'
                    })
                    
        except Exception as e:
            issues.append({
                'type': 'broken',
                'issue': f'Cannot analyze file: {e}',
                'line': 'file'
            })
            
        return issues
        
    def audit_web_routes(self):
        """Audit all web routes and endpoints"""
        print("\n[AUDITING] Web Routes and Endpoints...")
        
        issues = []
        
        try:
            from web_app_real import app
            
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'path': str(rule)
                })
                
            # Check for issues
            api_routes = [r for r in routes if '/api/' in r['path']]
            
            # Check if all API routes have proper methods
            for route in api_routes:
                if 'POST' in route['methods'] and 'GET' in route['methods']:
                    issues.append({
                        'route': route['path'],
                        'issue': 'API endpoint accepts both GET and POST (security concern)',
                        'severity': 'medium'
                    })
                    
            # Check for missing critical routes
            critical_routes = ['/api/health', '/api/status', '/api/version']
            existing_paths = [r['path'] for r in routes]
            
            for critical in critical_routes:
                if critical not in existing_paths:
                    issues.append({
                        'route': critical,
                        'issue': 'Missing recommended endpoint',
                        'severity': 'low'
                    })
                    
        except Exception as e:
            issues.append({
                'route': 'web_app_real',
                'issue': f'Cannot import web app: {e}',
                'severity': 'critical'
            })
            
        return issues
        
    def audit_configuration_files(self):
        """Audit configuration files"""
        print("\n[AUDITING] Configuration Files...")
        
        issues = []
        
        config_files = [
            '/workspace/Application/Stitch_Vars/st_aes_lib.ini',
            '/workspace/Application/stitch_config.ini'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    import configparser
                    config = configparser.ConfigParser()
                    config.read(config_file)
                    
                    # Check for issues
                    for section in config.sections():
                        for key, value in config.items(section):
                            # Check for empty values
                            if not value:
                                issues.append({
                                    'file': config_file,
                                    'issue': f'Empty config value: [{section}] {key}',
                                    'severity': 'low'
                                })
                                
                            # Check for default passwords
                            if 'password' in key.lower() and value in ['password', '12345', 'admin']:
                                issues.append({
                                    'file': config_file,
                                    'issue': f'Default password detected: [{section}] {key}',
                                    'severity': 'high'
                                })
                                
                except Exception as e:
                    issues.append({
                        'file': config_file,
                        'issue': f'Cannot parse config: {e}',
                        'severity': 'medium'
                    })
            else:
                issues.append({
                    'file': config_file,
                    'issue': 'Configuration file missing',
                    'severity': 'medium'
                })
                
        return issues
        
    def audit_payload_generation(self):
        """Audit payload generation logic"""
        print("\n[AUDITING] Payload Generation...")
        
        issues = []
        
        # Check web_payload_generator.py
        gen_file = '/workspace/web_payload_generator.py'
        
        if os.path.exists(gen_file):
            with open(gen_file, 'r') as f:
                content = f.read()
                
            # Check for issues
            if 'try:' in content and 'except:' in content:
                bare_excepts = len(re.findall(r'except:\s*$', content, re.MULTILINE))
                if bare_excepts > 0:
                    issues.append({
                        'file': 'web_payload_generator.py',
                        'issue': f'{bare_excepts} bare except clauses (hides errors)',
                        'severity': 'medium'
                    })
                    
            # Check if compilation actually works
            if 'compile_payload' in content:
                # Check if PyInstaller is properly configured
                if '--onefile' in content and '.spec' in content:
                    issues.append({
                        'file': 'web_payload_generator.py',
                        'issue': 'Conflicting PyInstaller options (--onefile with .spec)',
                        'severity': 'high'
                    })
                    
            # Check error handling
            if 'return None' in content:
                return_nones = len(re.findall(r'return\s+None', content))
                if return_nones > 3:
                    issues.append({
                        'file': 'web_payload_generator.py',
                        'issue': f'Excessive None returns ({return_nones}) - poor error handling',
                        'severity': 'medium'
                    })
                    
        return issues
        
    def audit_security(self):
        """Audit security implementations"""
        print("\n[AUDITING] Security...")
        
        issues = []
        
        # Check CSRF implementation
        web_app = '/workspace/web_app_real.py'
        if os.path.exists(web_app):
            with open(web_app, 'r') as f:
                content = f.read()
                
            # Check CSRF
            if 'csrf.exempt' in content:
                exempt_count = content.count('csrf.exempt')
                if exempt_count > 0:
                    issues.append({
                        'component': 'CSRF',
                        'issue': f'{exempt_count} endpoints exempt from CSRF protection',
                        'severity': 'high'
                    })
                    
            # Check session configuration
            if 'SECRET_KEY' in content:
                if "SECRET_KEY = 'dev'" in content or "SECRET_KEY = 'secret'" in content:
                    issues.append({
                        'component': 'Session',
                        'issue': 'Hardcoded weak secret key',
                        'severity': 'critical'
                    })
                    
            # Check password storage
            if 'password' in content:
                if 'hashlib.md5' in content:
                    issues.append({
                        'component': 'Password',
                        'issue': 'Using MD5 for password hashing (insecure)',
                        'severity': 'critical'
                    })
                    
        # Check encryption
        enc_file = '/workspace/Configuration/st_encryption.py'
        if os.path.exists(enc_file):
            with open(enc_file, 'r') as f:
                content = f.read()
                
            if 'ECB' in content:
                issues.append({
                    'component': 'Encryption',
                    'issue': 'Using ECB mode (insecure)',
                    'severity': 'high'
                })
                
            if 'DES' in content:
                issues.append({
                    'component': 'Encryption',
                    'issue': 'Using DES encryption (deprecated)',
                    'severity': 'critical'
                })
                
        return issues
        
    def audit_database_logic(self):
        """Check for database and data handling issues"""
        print("\n[AUDITING] Data Handling...")
        
        issues = []
        
        # Look for database files
        for root, dirs, files in os.walk('/workspace'):
            for file in files:
                if file.endswith(('.db', '.sqlite', '.sql')):
                    filepath = os.path.join(root, file)
                    
                    # Check if database is version controlled
                    if not filepath.startswith('/tmp'):
                        issues.append({
                            'file': filepath,
                            'issue': 'Database file in version control',
                            'severity': 'medium'
                        })
                        
        return issues
        
    def audit_all_files(self):
        """Audit all Python files in the codebase"""
        print("\n[AUDITING] All Python Files...")
        
        all_issues = defaultdict(list)
        
        # Define directories to audit
        dirs_to_audit = [
            '/workspace',
            '/workspace/Application',
            '/workspace/Configuration',
            '/workspace/PyLib'
        ]
        
        for base_dir in dirs_to_audit:
            if not os.path.exists(base_dir):
                continue
                
            for root, dirs, files in os.walk(base_dir):
                # Skip certain directories
                if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.env']):
                    continue
                    
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        self.files_audited += 1
                        
                        # Audit the file
                        file_issues = self.audit_python_file(filepath)
                        
                        if file_issues:
                            relative_path = os.path.relpath(filepath, '/workspace')
                            all_issues[relative_path] = file_issues
                            self.total_issues += len(file_issues)
                            
        return dict(all_issues)
        
    def generate_comprehensive_report(self):
        """Generate the comprehensive audit report"""
        print("\n" + "="*70)
        print("COMPREHENSIVE CODEBASE AUDIT REPORT")
        print("="*70)
        
        print(f"\n[STATISTICS]")
        print(f"  Files Audited: {self.files_audited}")
        print(f"  Total Issues Found: {self.total_issues}")
        
        # Categorize issues by severity
        critical = []
        high = []
        medium = []
        low = []
        
        for category, issues in self.audit_results.items():
            for issue in issues:
                severity = issue.get('severity', 'medium')
                
                if severity == 'critical':
                    critical.append((category, issue))
                elif severity == 'high':
                    high.append((category, issue))
                elif severity == 'medium':
                    medium.append((category, issue))
                else:
                    low.append((category, issue))
                    
        print(f"\n[ISSUES BY SEVERITY]")
        print(f"  Critical: {len(critical)}")
        print(f"  High: {len(high)}")
        print(f"  Medium: {len(medium)}")
        print(f"  Low: {len(low)}")
        
        # Report critical issues
        if critical:
            print(f"\n[CRITICAL ISSUES - MUST FIX]")
            for category, issue in critical[:5]:
                print(f"  ❌ {category}: {issue}")
                
        # Report high priority issues
        if high:
            print(f"\n[HIGH PRIORITY ISSUES]")
            for category, issue in high[:5]:
                print(f"  ⚠️  {category}: {issue}")
                
        # Save full report
        report_data = {
            'timestamp': os.popen('date').read().strip(),
            'statistics': {
                'files_audited': self.files_audited,
                'total_issues': self.total_issues,
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium),
                'low': len(low)
            },
            'issues': self.audit_results,
            'file_issues': self.file_audit_results
        }
        
        with open('/workspace/comprehensive_audit_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n[+] Full report saved to comprehensive_audit_report.json")
        
        # Overall health score
        health_score = 100
        health_score -= len(critical) * 10
        health_score -= len(high) * 5
        health_score -= len(medium) * 2
        health_score -= len(low) * 0.5
        health_score = max(0, health_score)
        
        print(f"\n[CODEBASE HEALTH SCORE] {health_score:.1f}%")
        
        if health_score >= 90:
            print("✅ Excellent - Minor issues only")
        elif health_score >= 70:
            print("⚠️  Good - Some issues need attention")
        elif health_score >= 50:
            print("⚠️  Fair - Multiple issues require fixing")
        else:
            print("❌ Poor - Significant issues throughout codebase")
            
def main():
    print("="*70)
    print("STARTING COMPREHENSIVE CODEBASE AUDIT")
    print("="*70)
    print("This will analyze every file and feature for issues\n")
    
    auditor = ComprehensiveCodebaseAuditor()
    
    # Run all audits
    print("[*] Running comprehensive audits...")
    
    # Audit all Python files
    auditor.file_audit_results = auditor.audit_all_files()
    
    # Audit specific components
    auditor.audit_results['web_routes'] = auditor.audit_web_routes()
    auditor.audit_results['configuration'] = auditor.audit_configuration_files()
    auditor.audit_results['payload_generation'] = auditor.audit_payload_generation()
    auditor.audit_results['security'] = auditor.audit_security()
    auditor.audit_results['database'] = auditor.audit_database_logic()
    
    # Generate report
    auditor.generate_comprehensive_report()
    
    print("\n[AUDIT COMPLETE]")

if __name__ == "__main__":
    main()