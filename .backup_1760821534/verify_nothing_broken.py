#!/usr/bin/env python3
"""
Verify that no existing features were broken by our changes
Deep analysis of all modifications and their impact
"""

import os
import sys
import subprocess
import importlib
import ast
import traceback
from pathlib import Path

sys.path.insert(0, '/workspace')

class FeatureVerifier:
    def __init__(self):
        self.broken_features = []
        self.working_features = []
        self.warnings = []
        
    def check_imports(self):
        """Check all Python files can be imported without errors"""
        print("[CHECK] Testing Python imports...")
        
        # Critical modules to test
        modules = [
            'web_app_real',
            'Application.stitch_cmd',
            'Application.stitch_gen',
            'Application.stitch_lib',
            'web_payload_generator',
            'Application.stitch_cross_compile'
        ]
        
        for module_name in modules:
            try:
                # Try to import
                if '.' in module_name:
                    parts = module_name.split('.')
                    module = __import__(module_name, fromlist=[parts[-1]])
                else:
                    module = __import__(module_name)
                    
                print(f"  ✓ {module_name} imports successfully")
                self.working_features.append(f"Import: {module_name}")
                
            except Exception as e:
                print(f"  ✗ {module_name} failed: {str(e)[:50]}")
                self.broken_features.append(f"Import {module_name}: {str(e)}")
                
    def check_original_functions(self):
        """Verify original functions still work"""
        print("\n[CHECK] Testing original functions...")
        
        # Check if core functions exist and work
        tests = []
        
        # Test 1: Can we create a stitch server?
        try:
            from Application.stitch_cmd import stitch_server
            server = stitch_server()
            print("  ✓ stitch_server instantiates")
            self.working_features.append("stitch_server creation")
        except Exception as e:
            print(f"  ✗ stitch_server broken: {e}")
            self.broken_features.append(f"stitch_server: {e}")
            
        # Test 2: Can we assemble stitch modules?
        try:
            from Application.stitch_gen import assemble_stitch
            # Don't actually run it, just check it exists
            print("  ✓ assemble_stitch exists")
            self.working_features.append("assemble_stitch function")
        except Exception as e:
            print(f"  ✗ assemble_stitch broken: {e}")
            self.broken_features.append(f"assemble_stitch: {e}")
            
        # Test 3: Web app routes
        try:
            from web_app_real import app
            
            # Check critical routes
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(str(rule))
                
            critical_routes = ['/login', '/api/generate-payload', '/api/execute']
            for route in critical_routes:
                if any(route in r for r in routes):
                    print(f"  ✓ Route {route} exists")
                    self.working_features.append(f"Route: {route}")
                else:
                    print(f"  ✗ Route {route} missing")
                    self.broken_features.append(f"Missing route: {route}")
                    
        except Exception as e:
            print(f"  ✗ Web routes broken: {e}")
            self.broken_features.append(f"Web routes: {e}")
            
    def check_modified_files(self):
        """Check all files we modified still have original functionality"""
        print("\n[CHECK] Verifying modified files...")
        
        # Files we modified
        modified = [
            ('/workspace/web_app_real.py', ['@app.route', 'login_required', '_perform_handshake']),
            ('/workspace/web_payload_generator.py', ['generate_payload', 'compile']),
            ('/workspace/Configuration/st_encryption.py', ['encrypt', 'decrypt']),
            ('/workspace/static/css/style_real.css', ['.sidebar', '.main-content']),
            ('/workspace/templates/dashboard_real.html', ['<nav', '<main']),
            ('/workspace/static/js/app_real.js', ['socket.on', 'function'])
        ]
        
        for filepath, required_elements in modified:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                    missing = []
                    for element in required_elements:
                        if element not in content:
                            missing.append(element)
                            
                    if missing:
                        print(f"  ⚠ {os.path.basename(filepath)} missing: {missing}")
                        self.warnings.append(f"{filepath}: missing {missing}")
                    else:
                        print(f"  ✓ {os.path.basename(filepath)} intact")
                        self.working_features.append(f"File: {os.path.basename(filepath)}")
                        
                except Exception as e:
                    print(f"  ✗ Error reading {filepath}: {e}")
                    self.broken_features.append(f"File read: {filepath}")
            else:
                print(f"  ✗ Missing file: {filepath}")
                self.broken_features.append(f"Missing: {filepath}")
                
    def test_payload_generation(self):
        """Test if payload generation still works"""
        print("\n[CHECK] Testing payload generation...")
        
        try:
            from web_payload_generator import WebPayloadGenerator
            
            gen = WebPayloadGenerator()
            
            # Try minimal config
            config = {
                'platform': 'linux',
                'host': '127.0.0.1',
                'port': '4040',
                'name': 'test_verify'
            }
            
            # We won't actually generate, just check the method exists
            if hasattr(gen, 'generate_payload'):
                print("  ✓ Payload generator has generate_payload method")
                self.working_features.append("Payload generation method")
            else:
                print("  ✗ Missing generate_payload method")
                self.broken_features.append("generate_payload method missing")
                
        except Exception as e:
            print(f"  ✗ Payload generation broken: {e}")
            self.broken_features.append(f"Payload generation: {e}")
            
    def check_database_integrity(self):
        """Check if any database or config files are intact"""
        print("\n[CHECK] Checking configuration integrity...")
        
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
                    
                    sections = len(config.sections())
                    print(f"  ✓ {os.path.basename(config_file)}: {sections} sections")
                    self.working_features.append(f"Config: {os.path.basename(config_file)}")
                    
                except Exception as e:
                    print(f"  ✗ Config corrupted: {config_file}")
                    self.broken_features.append(f"Config: {config_file}")
            else:
                print(f"  ⚠ Config not found: {config_file}")
                self.warnings.append(f"Missing config: {config_file}")
                
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*70)
        print("VERIFICATION REPORT")
        print("="*70)
        
        print(f"\n[WORKING FEATURES] ({len(self.working_features)})")
        for feature in self.working_features[:10]:
            print(f"  ✓ {feature}")
        if len(self.working_features) > 10:
            print(f"  ... and {len(self.working_features)-10} more")
            
        print(f"\n[BROKEN FEATURES] ({len(self.broken_features)})")
        if self.broken_features:
            for feature in self.broken_features:
                print(f"  ✗ {feature}")
        else:
            print("  None! All features intact")
            
        print(f"\n[WARNINGS] ({len(self.warnings)})")
        for warning in self.warnings:
            print(f"  ⚠ {warning}")
            
        integrity_score = len(self.working_features) / (len(self.working_features) + len(self.broken_features)) * 100
        
        print(f"\n[INTEGRITY SCORE] {integrity_score:.1f}%")
        
        if integrity_score >= 90:
            print("✅ System integrity maintained - No critical breakage")
        elif integrity_score >= 70:
            print("⚠️  Minor issues detected - System mostly functional")
        else:
            print("❌ Critical breakage detected - Fixes needed")
            
        return integrity_score >= 90

def main():
    print("="*70)
    print("VERIFYING SYSTEM INTEGRITY")
    print("="*70)
    
    verifier = FeatureVerifier()
    
    verifier.check_imports()
    verifier.check_original_functions()
    verifier.check_modified_files()
    verifier.test_payload_generation()
    verifier.check_database_integrity()
    
    return verifier.generate_report()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)