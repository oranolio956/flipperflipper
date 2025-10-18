#!/usr/bin/env python3
"""
COMPREHENSIVE FIX PLAN - Address All 748 Issues
Strategic, research-based approach with testing at each phase
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from collections import defaultdict
import time

class ComprehensiveFixPlan:
    def __init__(self):
        # Load the audit report
        self.load_audit_results()
        
        # Categorize fixes by priority and risk
        self.fix_phases = {
            'phase1_critical': [],      # Syntax errors, breaking bugs
            'phase2_security': [],      # Security vulnerabilities  
            'phase3_error_handling': [], # Bare excepts, error handling
            'phase4_code_quality': [],  # TODOs, imports, globals
            'phase5_optimization': []   # Performance, redundancy
        }
        
        self.test_suite = []
        self.fixes_applied = []
        self.rollback_points = []
        
    def load_audit_results(self):
        """Load the deep audit report"""
        try:
            with open('/workspace/deep_audit_report.json', 'r') as f:
                self.audit_data = json.load(f)
                
            self.total_issues = self.audit_data['statistics']['issues']
            self.findings = self.audit_data['findings']
            
            print(f"[LOADED] {self.total_issues} issues from audit report")
            
        except FileNotFoundError:
            print("[ERROR] Audit report not found, generating new audit...")
            self.audit_data = {'findings': {}, 'statistics': {}}
            self.findings = {}
            
    def categorize_issues(self):
        """Categorize all issues by type and priority"""
        print("\n[CATEGORIZING] Organizing issues by fix strategy...")
        
        issue_categories = defaultdict(list)
        
        for filepath, issues in self.findings.items():
            for issue in issues:
                severity = issue.get('severity', 'LOW')
                issue_type = issue.get('type', 'Unknown')
                
                # Categorize by severity and type
                if severity == 'CRITICAL':
                    self.fix_phases['phase1_critical'].append({
                        'file': filepath,
                        'issue': issue,
                        'fix_strategy': self.get_fix_strategy(issue_type)
                    })
                elif severity == 'HIGH' or 'security' in issue_type.lower():
                    self.fix_phases['phase2_security'].append({
                        'file': filepath,
                        'issue': issue,
                        'fix_strategy': self.get_fix_strategy(issue_type)
                    })
                elif 'except' in issue_type.lower() or 'error' in issue_type.lower():
                    self.fix_phases['phase3_error_handling'].append({
                        'file': filepath,
                        'issue': issue,
                        'fix_strategy': self.get_fix_strategy(issue_type)
                    })
                elif severity == 'MEDIUM':
                    self.fix_phases['phase4_code_quality'].append({
                        'file': filepath,
                        'issue': issue,
                        'fix_strategy': self.get_fix_strategy(issue_type)
                    })
                else:
                    self.fix_phases['phase5_optimization'].append({
                        'file': filepath,
                        'issue': issue,
                        'fix_strategy': self.get_fix_strategy(issue_type)
                    })
                    
                issue_categories[issue_type].append(filepath)
                
        # Print summary
        print(f"\n[CATEGORIZATION COMPLETE]")
        for phase, items in self.fix_phases.items():
            print(f"  {phase}: {len(items)} issues")
            
        print(f"\n[ISSUE TYPES]")
        for issue_type, files in sorted(issue_categories.items())[:10]:
            print(f"  {issue_type}: {len(files)} occurrences")
            
    def get_fix_strategy(self, issue_type):
        """Determine the fix strategy for each issue type"""
        strategies = {
            'Syntax Error': 'parse_and_fix_syntax',
            'Hardcoded password': 'move_to_env_var',
            'Hardcoded secret': 'move_to_env_var',
            'Shell injection risk': 'replace_with_subprocess',
            # SECURITY: Review eval() usage
    # SECURITY: Review eval() usage
            'Dangerous eval() usage': 'review_and_sandbox',
            'Dangerous exec() usage': 'review_and_sandbox',
            'Bare except clause': 'specify_exception_type',
            'Too broad exception': 'narrow_exception_scope',
            'Unfinished code marker': 'implement_or_document',
            'Wildcard import': 'specify_imports',
            'Global variable usage': 'refactor_to_class_or_param',
            'Infinite loop without clear exit': 'add_exit_condition',
            'Redundant boolean comparison': 'simplify_boolean',
            'Explicit return None': 'remove_redundant_return',
            'Circular import': 'refactor_imports',
            'Duplicate route': 'remove_duplicate',
            'Missing method': 'implement_method',
            'Weak hashing': 'upgrade_hash_algorithm',
            'Insecure encryption': 'upgrade_encryption'
        }
        
        return strategies.get(issue_type, 'manual_review')
        
    def create_test_suite(self):
        """Create comprehensive test suite for validation"""
        print("\n[TESTING] Creating test suite...")
        
        self.test_suite = [
            {
                'name': 'Syntax Check',
                'command': 'python3 -m py_compile',
                'files': ['web_app_real.py', 'web_payload_generator.py'],
                'critical': True
            },
            {
                'name': 'Import Test',
                'command': 'python3 -c "import {module}"',
                'modules': ['web_app_real', 'Application.stitch_cmd'],
                'critical': True
            },
            {
                'name': 'Web Server Start',
                'command': 'timeout 5 python3 -c "from web_app_real import app; print(\'OK\')"',
                'critical': True
            },
            {
                'name': 'Payload Generation',
                'command': 'python3 -c "from web_payload_generator import WebPayloadGenerator; print(\'OK\')"',
                'critical': True
            },
            {
                'name': 'Security Check',
                'command': 'grep -r "password.*=" --include="*.py" | grep -v "#" | wc -l',
                'threshold': 10,  # Should be less than 10 hardcoded passwords
                'critical': False
            }
        ]
        
        print(f"  Created {len(self.test_suite)} tests")
        
    def run_tests(self, phase_name=""):
        """Run test suite to ensure nothing is broken"""
        print(f"\n[TESTING] Running test suite {phase_name}...")
        
        all_passed = True
        results = []
        
        for test in self.test_suite:
            if test.get('files'):
                # Test specific files
                for file in test['files']:
                    filepath = os.path.join('/workspace', file)
                    if os.path.exists(filepath):
                        result = subprocess.run(
                            f"{test['command']} {filepath}",
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        
                        passed = result.returncode == 0
                        results.append({
                            'test': f"{test['name']} - {file}",
                            'passed': passed,
                            'critical': test.get('critical', False)
                        })
                        
                        if not passed and test.get('critical'):
                            all_passed = False
                            
            elif test.get('modules'):
                # Test module imports
                for module in test['modules']:
                    cmd = test['command'].format(module=module)
                    result = subprocess.run(cmd, shell=True, capture_output=True)
                    
                    passed = result.returncode == 0
                    results.append({
                        'test': f"{test['name']} - {module}",
                        'passed': passed,
                        'critical': test.get('critical', False)
                    })
                    
                    if not passed and test.get('critical'):
                        all_passed = False
                        
            else:
                # Run general command
                result = subprocess.run(test['command'], shell=True, capture_output=True, text=True)
                
                if 'threshold' in test:
                    try:
                        value = int(result.stdout.strip())
                        passed = value < test['threshold']
                    except Exception:
                        passed = False
                else:
                    passed = result.returncode == 0 or 'OK' in result.stdout
                    
                results.append({
                    'test': test['name'],
                    'passed': passed,
                    'critical': test.get('critical', False)
                })
                
                if not passed and test.get('critical'):
                    all_passed = False
                    
        # Print results
        print(f"\n  Test Results:")
        for result in results:
            status = "✓" if result['passed'] else "✗"
            critical = " [CRITICAL]" if result['critical'] and not result['passed'] else ""
            print(f"    {status} {result['test']}{critical}")
            
        return all_passed, results
        
    def create_rollback_point(self, phase_name):
        """Create a rollback point before applying fixes"""
        print(f"\n[ROLLBACK] Creating rollback point for {phase_name}...")
        
        rollback_dir = f"/workspace/.rollback/{phase_name}_{int(time.time())}"
        os.makedirs(rollback_dir, exist_ok=True)
        
        # Backup critical files
        critical_files = [
            'web_app_real.py',
            'web_payload_generator.py',
            'Application/stitch_cmd.py',
            'Application/stitch_gen.py'
        ]
        
        for file in critical_files:
            filepath = os.path.join('/workspace', file)
            if os.path.exists(filepath):
                backup_path = os.path.join(rollback_dir, file)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(filepath, backup_path)
                
        self.rollback_points.append(rollback_dir)
        print(f"  Rollback point created: {rollback_dir}")
        
        return rollback_dir
        
    def rollback(self, rollback_dir):
        """Rollback to a previous state"""
        print(f"\n[ROLLBACK] Rolling back to {rollback_dir}...")
        
        for root, dirs, files in os.walk(rollback_dir):
            for file in files:
                backup_path = os.path.join(root, file)
                relative_path = os.path.relpath(backup_path, rollback_dir)
                restore_path = os.path.join('/workspace', relative_path)
                
                print(f"  Restoring {relative_path}")
                shutil.copy2(backup_path, restore_path)
                
        print("  Rollback complete")
        
    def generate_implementation_plan(self):
        """Generate the complete implementation plan"""
        print("\n" + "="*70)
        print("COMPREHENSIVE FIX IMPLEMENTATION PLAN")
        print("="*70)
        
        total_fixes = sum(len(phase) for phase in self.fix_phases.values())
        
        print(f"\n[OVERVIEW]")
        print(f"  Total Issues to Fix: {total_fixes}")
        print(f"  Estimated Time: {total_fixes * 2} minutes")
        print(f"  Risk Level: Managed (rollback points at each phase)")
        
        print(f"\n[EXECUTION PHASES]")
        
        print(f"\n  PHASE 1: Critical Fixes ({len(self.fix_phases['phase1_critical'])} issues)")
        print(f"    • Fix syntax errors")
        print(f"    • Fix import failures")
        print(f"    • Fix breaking bugs")
        print(f"    • Test: Core functionality")
        
        print(f"\n  PHASE 2: Security ({len(self.fix_phases['phase2_security'])} issues)")
        print(f"    • Replace hardcoded credentials")
        print(f"    • Fix shell injection risks")
        print(f"    • Upgrade weak crypto")
        print(f"    • Test: Security scan")
        
        print(f"\n  PHASE 3: Error Handling ({len(self.fix_phases['phase3_error_handling'])} issues)")
        print(f"    • Fix bare except clauses")
        print(f"    • Improve error messages")
        print(f"    • Add logging")
        print(f"    • Test: Error scenarios")
        
        print(f"\n  PHASE 4: Code Quality ({len(self.fix_phases['phase4_code_quality'])} issues)")
        print(f"    • Fix imports")
        print(f"    • Refactor globals")
        print(f"    • Clean up TODOs")
        print(f"    • Test: Code analysis")
        
        print(f"\n  PHASE 5: Optimization ({len(self.fix_phases['phase5_optimization'])} issues)")
        print(f"    • Remove redundancy")
        print(f"    • Improve performance")
        print(f"    • Polish code")
        print(f"    • Test: Performance")
        
        print(f"\n[TESTING STRATEGY]")
        print(f"  • Run tests before each phase")
        print(f"  • Run tests after each file modification")
        print(f"  • Run comprehensive test after each phase")
        print(f"  • Rollback if critical tests fail")
        
        print(f"\n[ROLLBACK STRATEGY]")
        print(f"  • Create snapshot before each phase")
        print(f"  • Test after each fix")
        print(f"  • Automatic rollback on critical failure")
        print(f"  • Manual rollback option available")
        
        # Save plan
        plan = {
            'total_issues': total_fixes,
            'phases': {name: len(items) for name, items in self.fix_phases.items()},
            'test_suite': len(self.test_suite),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open('/workspace/fix_implementation_plan.json', 'w') as f:
            json.dump(plan, f, indent=2)
            
        print(f"\n[+] Plan saved to fix_implementation_plan.json")
        
        return plan

def main():
    print("="*70)
    print("COMPREHENSIVE FIX PLANNING")
    print("="*70)
    
    planner = ComprehensiveFixPlan()
    
    # Step 1: Categorize all issues
    planner.categorize_issues()
    
    # Step 2: Create test suite
    planner.create_test_suite()
    
    # Step 3: Run baseline tests
    print("\n[BASELINE] Running baseline tests...")
    baseline_passed, baseline_results = planner.run_tests("baseline")
    
    if not baseline_passed:
        print("\n⚠️  Some baseline tests failed - will address in fixes")
        
    # Step 4: Generate implementation plan
    plan = planner.generate_implementation_plan()
    
    print(f"\n[READY] Plan complete. Execute with 'python3 execute_fixes.py'")
    
    return plan

if __name__ == "__main__":
    main()