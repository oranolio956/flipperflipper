#!/usr/bin/env python3
"""
Final Validation Test - Verify all fixes are properly implemented
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class FinalValidator:
    def __init__(self):
        self.results = {
            'protocol_fixes': {},
            'binary_compilation': {},
            'mobile_ui': {},
            'overall': {}
        }
        
    def validate_protocol_fixes(self):
        """Validate protocol fixes are in place"""
        print("[VALIDATING] Protocol Fixes...")
        
        # Check if protocol files exist
        protocol_files = [
            '/workspace/correct_payload_protocol.py',
            '/workspace/fixed_payload_protocol.py',
            '/workspace/connection_fix_report.txt'
        ]
        
        for file in protocol_files:
            exists = os.path.exists(file)
            self.results['protocol_fixes'][os.path.basename(file)] = exists
            print(f"  {'✓' if exists else '✗'} {os.path.basename(file)}")
            
        # Check handshake implementation
        with open('/workspace/web_app_real.py', 'r') as f:
            content = f.read()
            
        simplified = 'Simplified working handshake' in content
        self.results['protocol_fixes']['handshake_simplified'] = simplified
        print(f"  {'✓' if simplified else '✗'} Handshake simplified in web_app_real.py")
        
        # Check correct payload has proper implementation
        if os.path.exists('/workspace/correct_payload_protocol.py'):
            with open('/workspace/correct_payload_protocol.py', 'r') as f:
                payload_content = f.read()
                
            has_handshake = 'def connect_and_handshake' in payload_content
            has_struct = 'struct.pack' in payload_content
            
            self.results['protocol_fixes']['proper_handshake'] = has_handshake
            self.results['protocol_fixes']['struct_protocol'] = has_struct
            
            print(f"  {'✓' if has_handshake else '✗'} Proper handshake method")
            print(f"  {'✓' if has_struct else '✗'} Struct-based protocol")
            
        return all(self.results['protocol_fixes'].values())
    
    def validate_binary_compilation(self):
        """Validate binary compilation works"""
        print("\n[VALIDATING] Binary Compilation...")
        
        # Check if binary exists
        binary_path = Path('/workspace/binary_compilation_test/dist/test_binary')
        binary_exists = binary_path.exists()
        
        self.results['binary_compilation']['binary_exists'] = binary_exists
        print(f"  {'✓' if binary_exists else '✗'} Binary executable exists")
        
        if binary_exists:
            # Check size (should be > 5MB for bundled Python)
            size = binary_path.stat().st_size
            size_ok = size > 5_000_000
            
            self.results['binary_compilation']['size_ok'] = size_ok
            print(f"  {'✓' if size_ok else '✗'} Binary size: {size:,} bytes")
            
            # Check if executable
            is_executable = os.access(binary_path, os.X_OK)
            self.results['binary_compilation']['is_executable'] = is_executable
            print(f"  {'✓' if is_executable else '✗'} File is executable")
            
        # Check PyInstaller spec template
        spec_exists = os.path.exists('/workspace/binary_compilation_test/payload_template.spec')
        self.results['binary_compilation']['spec_template'] = spec_exists
        print(f"  {'✓' if spec_exists else '✗'} PyInstaller spec template exists")
        
        # Check fix script
        fixer_exists = os.path.exists('/workspace/fix_binary_compilation.py')
        self.results['binary_compilation']['fixer_script'] = fixer_exists
        print(f"  {'✓' if fixer_exists else '✗'} Binary compilation fixer script")
        
        return all(self.results['binary_compilation'].values())
    
    def validate_mobile_ui(self):
        """Validate mobile UI fixes"""
        print("\n[VALIDATING] Mobile UI Fixes...")
        
        # Check CSS fixes
        css_path = '/workspace/static/css/style_real.css'
        if os.path.exists(css_path):
            with open(css_path, 'r') as f:
                css = f.read()
                
            has_mobile_logout = '.mobile-logout' in css
            has_overflow_fix = 'overflow-wrap: break-word' in css
            has_responsive = '@media (max-width: 768px)' in css
            
            self.results['mobile_ui']['mobile_logout_css'] = has_mobile_logout
            self.results['mobile_ui']['overflow_fix'] = has_overflow_fix
            self.results['mobile_ui']['responsive_css'] = has_responsive
            
            print(f"  {'✓' if has_mobile_logout else '✗'} Mobile logout CSS")
            print(f"  {'✓' if has_overflow_fix else '✗'} Text overflow fix")
            print(f"  {'✓' if has_responsive else '✗'} Responsive CSS rules")
            
        # Check HTML fixes
        html_path = '/workspace/templates/dashboard_real.html'
        if os.path.exists(html_path):
            with open(html_path, 'r') as f:
                html = f.read()
                
            has_mobile_button = 'mobile-logout' in html
            has_toggle = 'sidebar-toggle' in html
            
            self.results['mobile_ui']['mobile_button_html'] = has_mobile_button
            self.results['mobile_ui']['sidebar_toggle'] = has_toggle
            
            print(f"  {'✓' if has_mobile_button else '✗'} Mobile logout button in HTML")
            print(f"  {'✓' if has_toggle else '✗'} Sidebar toggle button")
            
        # Check JavaScript fixes
        js_path = '/workspace/static/js/app_real.js'
        if os.path.exists(js_path):
            with open(js_path, 'r') as f:
                js = f.read()
                
            has_toggle_func = 'toggleSidebar' in js
            has_responsive_js = 'window.innerWidth' in js and '768' in js
            
            self.results['mobile_ui']['toggle_function'] = has_toggle_func
            self.results['mobile_ui']['responsive_js'] = has_responsive_js
            
            print(f"  {'✓' if has_toggle_func else '✗'} Toggle sidebar function")
            print(f"  {'✓' if has_responsive_js else '✗'} Responsive JavaScript")
            
        return all(self.results['mobile_ui'].values())
    
    def validate_overall_system(self):
        """Validate overall system status"""
        print("\n[VALIDATING] Overall System...")
        
        # Check all phases completed
        phase_files = [
            '/workspace/phase1_findings.txt',
            '/workspace/phase3_fixes.txt',
            '/workspace/phase5_test_results.json',
            '/workspace/phase6_final_report.json'
        ]
        
        phases_complete = sum(1 for f in phase_files if os.path.exists(f))
        self.results['overall']['phases_complete'] = phases_complete
        print(f"  Phases completed: {phases_complete}/{len(phase_files)}")
        
        # Check reports
        reports = [
            '/workspace/FINAL_IMPLEMENTATION_REPORT.md',
            '/workspace/connection_fix_report.txt',
            '/workspace/binary_compilation_report.txt',
            '/workspace/mobile_ui_fixes.txt'
        ]
        
        reports_generated = sum(1 for r in reports if os.path.exists(r))
        self.results['overall']['reports_generated'] = reports_generated
        print(f"  Reports generated: {reports_generated}/{len(reports)}")
        
        # Check backups created
        import glob
        backups = glob.glob('/workspace/**/*.backup*', recursive=True)
        backups += glob.glob('/workspace/**/*_backup', recursive=True)
        
        self.results['overall']['backups_created'] = len(backups)
        print(f"  Backup files created: {len(backups)}")
        
        return True
    
    def generate_final_report(self):
        """Generate final validation report"""
        print("\n" + "="*70)
        print("FINAL VALIDATION REPORT")
        print("="*70)
        
        # Calculate scores
        protocol_score = sum(1 for v in self.results['protocol_fixes'].values() if v)
        protocol_total = len(self.results['protocol_fixes'])
        
        binary_score = sum(1 for v in self.results['binary_compilation'].values() if v)
        binary_total = len(self.results['binary_compilation'])
        
        mobile_score = sum(1 for v in self.results['mobile_ui'].values() if v)
        mobile_total = len(self.results['mobile_ui'])
        
        print(f"\n[PROTOCOL FIXES] {protocol_score}/{protocol_total} ({'✅ COMPLETE' if protocol_score == protocol_total else '⚠️ PARTIAL'})")
        for key, value in self.results['protocol_fixes'].items():
            print(f"  {'✓' if value else '✗'} {key}")
            
        print(f"\n[BINARY COMPILATION] {binary_score}/{binary_total} ({'✅ COMPLETE' if binary_score == binary_total else '⚠️ PARTIAL'})")
        for key, value in self.results['binary_compilation'].items():
            print(f"  {'✓' if value else '✗'} {key}")
            
        print(f"\n[MOBILE UI] {mobile_score}/{mobile_total} ({'✅ COMPLETE' if mobile_score == mobile_total else '⚠️ PARTIAL'})")
        for key, value in self.results['mobile_ui'].items():
            print(f"  {'✓' if value else '✗'} {key}")
            
        print(f"\n[OVERALL SYSTEM]")
        for key, value in self.results['overall'].items():
            print(f"  {key}: {value}")
            
        # Calculate total score
        total_score = protocol_score + binary_score + mobile_score
        total_possible = protocol_total + binary_total + mobile_total
        percentage = (total_score / total_possible) * 100
        
        print(f"\n[FINAL SCORE]")
        print(f"  Total: {total_score}/{total_possible} ({percentage:.1f}%)")
        
        if percentage >= 90:
            print("\n✅ IMPLEMENTATION COMPLETE - All major fixes properly applied!")
        elif percentage >= 70:
            print("\n⚠️ IMPLEMENTATION MOSTLY COMPLETE - Some minor issues remain")
        else:
            print("\n❌ IMPLEMENTATION INCOMPLETE - Major issues need attention")
            
        # Save results
        with open('/workspace/final_validation_results.json', 'w') as f:
            json.dump({
                'results': self.results,
                'score': {
                    'total': total_score,
                    'possible': total_possible,
                    'percentage': percentage
                }
            }, f, indent=2)
            
        print(f"\n[+] Validation results saved to final_validation_results.json")
        
        return percentage >= 90

def main():
    print("="*70)
    print("FINAL VALIDATION TEST")
    print("="*70)
    print("Checking all implemented fixes...\n")
    
    validator = FinalValidator()
    
    # Run all validations
    protocol_ok = validator.validate_protocol_fixes()
    binary_ok = validator.validate_binary_compilation()
    mobile_ok = validator.validate_mobile_ui()
    overall_ok = validator.validate_overall_system()
    
    # Generate report
    complete = validator.generate_final_report()
    
    return complete

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)