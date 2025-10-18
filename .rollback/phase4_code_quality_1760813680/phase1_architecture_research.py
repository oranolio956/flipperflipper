#!/usr/bin/env python3
"""
Phase 1.2: Architecture Research
Understanding the complete system architecture and data flow
"""

import os
import sys
import ast
import json
import subprocess
import importlib.util

sys.path.insert(0, '/workspace')

class ArchitectureAnalyzer:
    def __init__(self):
        self.architecture = {
            'components': {},
            'data_flow': [],
            'dependencies': {},
            'issues': []
        }
    
    def analyze_component_structure(self):
        """Map out all system components"""
        print("[RESEARCH] Mapping system components...")
        
        components = {
            'Server Core': {
                'path': '/workspace/Application/stitch_cmd.py',
                'class': 'stitch_server',
                'purpose': 'Main C2 server'
            },
            'Protocol Handler': {
                'path': '/workspace/Application/stitch_lib.py',
                'class': 'stitch_commands_library',
                'purpose': 'Command execution and protocol'
            },
            'Web Interface': {
                'path': '/workspace/web_app_real.py',
                'purpose': 'Web API and UI'
            },
            'Payload Generator': {
                'path': '/workspace/Application/stitch_gen.py',
                'purpose': 'Payload creation and compilation'
            },
            'Cross Compiler': {
                'path': '/workspace/Application/stitch_cross_compile.py',
                'purpose': 'Cross-platform compilation'
            }
        }
        
        for name, info in components.items():
            if os.path.exists(info['path']):
                # Get file size and line count
                with open(info['path'], 'r') as f:
                    lines = len(f.readlines())
                
                size = os.path.getsize(info['path'])
                
                print(f"  {name}:")
                print(f"    Lines: {lines}")
                print(f"    Size: {size} bytes")
                
                self.architecture['components'][name] = {
                    'lines': lines,
                    'size': size,
                    'purpose': info['purpose']
                }
        
    def trace_data_flow(self):
        """Trace data flow through the system"""
        print("\n[RESEARCH] Tracing data flow...")
        
        # Trace payload generation flow
        print("  Payload Generation Flow:")
        flow = [
            "1. Web API receives request",
            "2. web_payload_generator.generate_payload() called",
            "3. stitch_gen.assemble_stitch() creates modules",
            "4. stitch_cross_compile compiles (or falls back)",
            "5. Binary/script returned to user"
        ]
        
        for step in flow:
            print(f"    {step}")
        self.architecture['data_flow'].append(('payload_gen', flow))
        
        # Trace command execution flow
        print("\n  Command Execution Flow:")
        flow = [
            "1. Web API receives command request",
            "2. execute_real_command() called",
            "3. _perform_handshake() establishes AES",
            "4. execute_on_target() sends command",
            "5. stitch_lib processes on target",
            "6. Response encrypted and returned"
        ]
        
        for step in flow:
            print(f"    {step}")
        self.architecture['data_flow'].append(('command_exec', flow))
        
    def analyze_dependency_chain(self):
        """Analyze module dependencies"""
        print("\n[RESEARCH] Analyzing dependencies...")
        
        # Check Python package dependencies
        import pkg_resources
        
        required_packages = [
            'flask',
            'flask-socketio',
            'pyinstaller',
            'pycryptodome',
            'requests',
            'colorama',
            'mss',
            'pexpect'
        ]
        
        installed = []
        missing = []
        
        for package in required_packages:
            try:
                version = pkg_resources.get_distribution(package).version
                installed.append(f"{package}=={version}")
                print(f"  ✓ {package}: {version}")
            except:
                missing.append(package)
                print(f"  ✗ {package}: MISSING")
        
        self.architecture['dependencies']['installed'] = installed
        self.architecture['dependencies']['missing'] = missing
        
    def identify_architectural_issues(self):
        """Identify architectural problems"""
        print("\n[RESEARCH] Identifying architectural issues...")
        
        issues = []
        
        # Issue 1: Handshake complexity
        print("  Checking handshake implementation...")
        handshake_file = '/workspace/web_app_real.py'
        with open(handshake_file, 'r') as f:
            content = f.read()
            
        if '_perform_handshake' in content:
            # Count lines in handshake function
            lines = content.split('def _perform_handshake')[1].split('def ')[0]
            line_count = len(lines.split('\n'))
            
            if line_count > 50:
                issues.append(f"Complex handshake: {line_count} lines")
                print(f"    Issue: Complex handshake ({line_count} lines)")
        
        # Issue 2: Payload bundling
        print("  Checking payload bundling...")
        if not os.path.exists('/workspace/Configuration/requirements.py'):
            issues.append("Missing requirements.py in Configuration")
            print("    Issue: Missing requirements module")
        
        # Issue 3: Cross-compilation
        print("  Checking cross-compilation...")
        cross_compile = '/workspace/Application/stitch_cross_compile.py'
        if os.path.exists(cross_compile):
            with open(cross_compile, 'r') as f:
                content = f.read()
                
            if 'wine' in content.lower():
                # Check if Wine is installed
                result = subprocess.run(['which', 'wine'], capture_output=True)
                if result.returncode != 0:
                    issues.append("Wine not installed for Windows compilation")
                    print("    Issue: Wine not installed")
        
        self.architecture['issues'] = issues
        
    def analyze_protocol_implementation(self):
        """Deep dive into protocol implementation"""
        print("\n[RESEARCH] Analyzing protocol implementation...")
        
        # Read stitch_lib.py
        stitch_lib = '/workspace/Application/stitch_lib.py'
        
        if os.path.exists(stitch_lib):
            with open(stitch_lib, 'r') as f:
                content = f.read()
            
            # Find st_send and st_receive functions
            send_impl = 'def st_send' in content
            receive_impl = 'def st_receive' in content
            
            print(f"  st_send implemented: {send_impl}")
            print(f"  st_receive implemented: {receive_impl}")
            
            # Check for encryption
            if 'AES' in content:
                print("  AES encryption found")
                
                # Look for AES usage
                aes_lines = [line for line in content.split('\n') if 'AES' in line]
                print(f"  AES references: {len(aes_lines)}")
    
    def research_working_payload(self):
        """Analyze what makes a working payload"""
        print("\n[RESEARCH] Analyzing working payload structure...")
        
        # Check our working test payload
        test_payload = '/tmp/stitch_payload.py'
        
        if os.path.exists(test_payload):
            with open(test_payload, 'r') as f:
                content = f.read()
            
            # Analyze structure
            has_socket = 'import socket' in content
            has_connect = 'connect(' in content
            has_loop = 'while' in content
            
            print(f"  Socket import: {has_socket}")
            print(f"  Connection code: {has_connect}")
            print(f"  Event loop: {has_loop}")
            
            # Count functions
            functions = content.count('def ')
            print(f"  Functions defined: {functions}")
    
    def generate_architecture_report(self):
        """Generate comprehensive architecture report"""
        print("\n" + "="*70)
        print("ARCHITECTURE ANALYSIS REPORT")
        print("="*70)
        
        print("\n[COMPONENTS]")
        for name, info in self.architecture['components'].items():
            print(f"  {name}: {info['lines']} lines, {info['purpose']}")
        
        print("\n[DATA FLOWS]")
        for flow_name, steps in self.architecture['data_flow']:
            print(f"  {flow_name}:")
            for step in steps[:3]:
                print(f"    {step}")
        
        print("\n[DEPENDENCIES]")
        print(f"  Installed: {len(self.architecture['dependencies'].get('installed', []))}")
        print(f"  Missing: {len(self.architecture['dependencies'].get('missing', []))}")
        
        print("\n[ISSUES IDENTIFIED]")
        for issue in self.architecture['issues']:
            print(f"  - {issue}")
        
        return self.architecture

def main():
    print("="*70)
    print("PHASE 1.2: ARCHITECTURE RESEARCH")
    print("="*70)
    
    analyzer = ArchitectureAnalyzer()
    
    # Run analysis
    analyzer.analyze_component_structure()
    analyzer.trace_data_flow()
    analyzer.analyze_dependency_chain()
    analyzer.identify_architectural_issues()
    analyzer.analyze_protocol_implementation()
    analyzer.research_working_payload()
    
    # Generate report
    architecture = analyzer.generate_architecture_report()
    
    # Save findings
    with open('/workspace/phase1_architecture.json', 'w') as f:
        json.dump(architecture, f, indent=2)
    
    print("\n[+] Architecture analysis complete. Saved to phase1_architecture.json")

if __name__ == "__main__":
    main()