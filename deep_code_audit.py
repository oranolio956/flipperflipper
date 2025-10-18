#!/usr/bin/env python3
"""
DEEP CODE AUDIT - File by File Analysis
Examines every file for issues without running imports
"""

import os
import re
import json
import ast
from pathlib import Path
from collections import defaultdict

class DeepCodeAuditor:
    def __init__(self):
        self.findings = defaultdict(list)
        self.file_count = 0
        self.issue_count = 0
        
    def audit_file_content(self, filepath):
        """Audit a file's content for issues"""
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            filename = os.path.basename(filepath)
            
            # 1. Check for syntax issues
            if filepath.endswith('.py'):
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    issues.append({
                        'severity': 'CRITICAL',
                        'type': 'Syntax Error',
                        'detail': f'Line {e.lineno}: {e.msg}',
                        'file': filename
                    })
                    
            # 2. Security issues
            security_patterns = [
                (r'password\s*=\s*["\'][\w]+["\']', 'Hardcoded password'),
                (r'secret\s*=\s*["\'][\w]+["\']', 'Hardcoded secret'),
                # SECURITY: Review eval() usage
    # SECURITY: Review eval() usage
                (r'eval\s*\(', 'Dangerous eval() usage'),
                (r'exec\s*\(', 'Dangerous exec() usage'),
                (r'pickle\.loads', 'Unsafe pickle deserialization'),
                (r'os\.system\s*\(', 'Shell injection risk with os.system'),
                (r'subprocess\.call\s*\([^,]+,\s*shell=True', 'Shell injection risk'),
            ]
            
            for pattern, issue_type in security_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'severity': 'HIGH',
                        'type': issue_type,
                        'detail': f'Line {line_num}: {match.group()[:50]}',
                        'file': filename
                    })
                    
            # 3. Code quality issues
            quality_patterns = [
                (r'except\s*:\s*$', 'Bare except clause'),
                (r'except\s+Exception\s*:\s*$', 'Too broad exception'),
                (r'TODO|FIXME|XXX|HACK', 'Unfinished code marker'),
                (r'import\s+\*', 'Wildcard import'),
                (r'global\s+\w+', 'Global variable usage'),
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, issue_type in quality_patterns:
                    if re.search(pattern, line):
                        issues.append({
                            'severity': 'MEDIUM',
                            'type': issue_type,
                            'detail': f'Line {i}: {line.strip()[:50]}',
                            'file': filename
                        })
                        
            # 4. Logic issues
            logic_patterns = [
                (r'while\s+True\s*:', 'Infinite loop without clear exit'),
                (r'if\s+.*==\s*True', 'Redundant boolean comparison'),
                (r'if\s+.*==\s*False', 'Redundant boolean comparison'),
                (r'return\s+None\s*$', 'Explicit return None'),
            ]
            
            for pattern, issue_type in logic_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'severity': 'LOW',
                        'type': issue_type,
                        'detail': f'Line {line_num}',
                        'file': filename
                    })
                    
            # 5. Import issues
            import_lines = [l for l in lines if l.strip().startswith(('import ', 'from '))]
            
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    # Check for missing modules
                    if 'from requirements import' in line:
                        issues.append({
                            'severity': 'HIGH',
                            'type': 'Circular import',
                            'detail': f'Line {i+1}: requirements importing from requirements',
                            'file': filename
                        })
                        
            # 6. Specific file checks
            if filename == 'web_app_real.py':
                # Check for route issues
                if '@app.route' in content:
                    routes = re.findall(r"@app\.route\('([^']+)'", content)
                    
                    # Check for duplicate routes
                    seen = set()
                    for route in routes:
                        if route in seen:
                            issues.append({
                                'severity': 'HIGH',
                                'type': 'Duplicate route',
                                'detail': f'Route {route} defined multiple times',
                                'file': filename
                            })
                        seen.add(route)
                        
            if filename == 'web_payload_generator.py':
                # Check payload generation logic
                if 'generate_payload' in content:
                    if 'try:' in content and 'except:' in content:
                        if content.count('except:') > content.count('except '):
                            issues.append({
                                'severity': 'MEDIUM',
                                'type': 'Error handling',
                                'detail': 'Multiple bare except clauses hiding errors',
                                'file': filename
                            })
                            
            if 'st_encryption' in filename:
                # Check encryption implementation
                if 'AES.MODE_ECB' in content:
                    issues.append({
                        'severity': 'CRITICAL',
                        'type': 'Insecure encryption',
                        'detail': 'ECB mode is insecure, use CBC or GCM',
                        'file': filename
                    })
                    
                if 'md5' in content.lower():
                    issues.append({
                        'severity': 'HIGH',
                        'type': 'Weak hashing',
                        'detail': 'MD5 is broken, use SHA256 or better',
                        'file': filename
                    })
                    
        except Exception as e:
            issues.append({
                'severity': 'ERROR',
                'type': 'File read error',
                'detail': str(e),
                'file': filepath
            })
            
        return issues
        
    def audit_directory(self, directory):
        """Audit all files in a directory"""
        print(f"\n[AUDITING] {directory}")
        
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'build', 'dist']]
            
            for file in files:
                if file.endswith(('.py', '.yml', '.yaml', '.ini', '.json')):
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, '/workspace')
                    
                    self.file_count += 1
                    issues = self.audit_file_content(filepath)
                    
                    if issues:
                        self.findings[relative_path] = issues
                        self.issue_count += len(issues)
                        
                        # Print critical issues immediately
                        for issue in issues:
                            if issue['severity'] == 'CRITICAL':
                                print(f"  ❌ CRITICAL in {relative_path}: {issue['type']}")
                                
    def audit_integration(self):
        """Check integration between components"""
        print("\n[AUDITING] Component Integration")
        
        integration_issues = []
        
        # Check if web_app imports work with payload generator
        web_app = '/workspace/web_app_real.py'
        payload_gen = '/workspace/web_payload_generator.py'
        
        if os.path.exists(web_app) and os.path.exists(payload_gen):
            with open(web_app, 'r') as f:
                web_content = f.read()
                
            with open(payload_gen, 'r') as f:
                gen_content = f.read()
                
            # Check if web app properly imports generator
            if 'web_payload_generator' in web_content:
                if 'WebPayloadGenerator' not in web_content:
                    integration_issues.append({
                        'severity': 'HIGH',
                        'type': 'Integration issue',
                        'detail': 'web_app imports generator but doesn\'t use class',
                        'component': 'Web->PayloadGen'
                    })
                    
            # Check if generator has required methods
            if 'def generate_payload' not in gen_content:
                integration_issues.append({
                    'severity': 'CRITICAL',
                    'type': 'Missing method',
                    'detail': 'PayloadGenerator missing generate_payload method',
                    'component': 'PayloadGen'
                })
                
        # Check C2 server integration
        stitch_cmd = '/workspace/Application/stitch_cmd.py'
        if os.path.exists(stitch_cmd):
            with open(stitch_cmd, 'r') as f:
                cmd_content = f.read()
                
            # Check for required classes/methods
            required = ['class stitch_server', 'def do_listen', 'def do_shell']
            for req in required:
                if req not in cmd_content:
                    integration_issues.append({
                        'severity': 'CRITICAL',
                        'type': 'Missing component',
                        'detail': f'stitch_cmd missing: {req}',
                        'component': 'C2Server'
                    })
                    
        return integration_issues
        
    def generate_detailed_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*70)
        print("DEEP CODE AUDIT REPORT")
        print("="*70)
        
        # Categorize by severity
        critical = []
        high = []
        medium = []
        low = []
        
        for filepath, issues in self.findings.items():
            for issue in issues:
                if issue['severity'] == 'CRITICAL':
                    critical.append((filepath, issue))
                elif issue['severity'] == 'HIGH':
                    high.append((filepath, issue))
                elif issue['severity'] == 'MEDIUM':
                    medium.append((filepath, issue))
                else:
                    low.append((filepath, issue))
                    
        print(f"\n[STATISTICS]")
        print(f"  Files Analyzed: {self.file_count}")
        print(f"  Total Issues: {self.issue_count}")
        print(f"  Critical: {len(critical)}")
        print(f"  High: {len(high)}")
        print(f"  Medium: {len(medium)}")
        print(f"  Low: {len(low)}")
        
        # Report critical issues
        if critical:
            print(f"\n[CRITICAL ISSUES - IMMEDIATE ACTION REQUIRED]")
            for filepath, issue in critical[:10]:
                print(f"  ❌ {filepath}")
                print(f"     Issue: {issue['type']}")
                print(f"     Detail: {issue['detail']}")
                
        # Report high priority
        if high:
            print(f"\n[HIGH PRIORITY ISSUES]")
            for filepath, issue in high[:10]:
                print(f"  ⚠️  {filepath}")
                print(f"     Issue: {issue['type']}")
                print(f"     Detail: {issue['detail']}")
                
        # Check specific functionality
        print(f"\n[FUNCTIONALITY CHECK]")
        
        # Check if key files exist
        key_files = {
            'web_app_real.py': 'Web Interface',
            'web_payload_generator.py': 'Payload Generation',
            'Application/stitch_cmd.py': 'C2 Server',
            'Application/stitch_gen.py': 'Module Assembly',
            'Configuration/st_encryption.py': 'Encryption'
        }
        
        for file, component in key_files.items():
            full_path = os.path.join('/workspace', file)
            if os.path.exists(full_path):
                issues = self.findings.get(file, [])
                critical_count = sum(1 for i in issues if i['severity'] == 'CRITICAL')
                
                if critical_count > 0:
                    print(f"  ❌ {component}: {critical_count} critical issues")
                elif issues:
                    print(f"  ⚠️  {component}: {len(issues)} issues")
                else:
                    print(f"  ✓ {component}: No issues found")
            else:
                print(f"  ❌ {component}: FILE MISSING")
                
        # Save full report
        report = {
            'statistics': {
                'files': self.file_count,
                'issues': self.issue_count,
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium),
                'low': len(low)
            },
            'findings': dict(self.findings)
        }
        
        with open('/workspace/deep_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n[+] Full report saved to deep_audit_report.json")
        
        # Overall assessment
        print(f"\n[OVERALL ASSESSMENT]")
        
        if len(critical) == 0 and len(high) < 5:
            print("✅ GOOD - Codebase is in good shape with minor issues")
        elif len(critical) < 3 and len(high) < 10:
            print("⚠️  FAIR - Some issues need attention but functional")
        elif len(critical) < 10:
            print("⚠️  POOR - Multiple critical issues affecting functionality")
        else:
            print("❌ CRITICAL - Major issues throughout, needs significant work")

def main():
    print("="*70)
    print("DEEP CODE AUDIT - COMPLETE ANALYSIS")
    print("="*70)
    
    auditor = DeepCodeAuditor()
    
    # Audit main directories
    directories = [
        '/workspace',
        '/workspace/Application',
        '/workspace/Configuration',
        '/workspace/static',
        '/workspace/templates'
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            auditor.audit_directory(directory)
            
    # Check integration
    integration_issues = auditor.audit_integration()
    if integration_issues:
        auditor.findings['_integration'] = integration_issues
        auditor.issue_count += len(integration_issues)
        
    # Generate report
    auditor.generate_detailed_report()

if __name__ == "__main__":
    main()