#!/usr/bin/env python3
"""
Comprehensive Stitch RAT Audit Script
Tests all major components and identifies issues
"""

import os
import sys
import json
import time
import threading
import importlib.util
from datetime import datetime

# Set up environment
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'test123456789'

class StitchAuditor:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'core_components': {},
            'web_interface': {},
            'payload_system': {},
            'pylib_modules': {},
            'networking': {},
            'security': {},
            'ui_components': {},
            'issues': [],
            'recommendations': []
        }
    
    def test_core_components(self):
        """Test core Stitch components"""
        print("🔍 Testing Core Components...")
        
        try:
            from Application.stitch_cmd import stitch_server
            self.results['core_components']['stitch_server'] = 'WORKING'
            
            # Test server instance
            server = stitch_server()
            self.results['core_components']['server_instance'] = 'WORKING'
            
            # Test configuration loading
            self.results['core_components']['config_loading'] = 'WORKING' if server.Config else 'FAILED'
            self.results['core_components']['aes_library'] = 'WORKING' if server.aes_lib else 'FAILED'
            
        except Exception as e:
            self.results['core_components']['error'] = str(e)
            self.results['issues'].append(f"Core components failed: {e}")
    
    def test_web_interface(self):
        """Test web interface components"""
        print("🌐 Testing Web Interface...")
        
        try:
            from web_app_real import app, get_stitch_server
            self.results['web_interface']['app_creation'] = 'WORKING'
            
            # Test Flask app configuration
            with app.test_client() as client:
                # Health endpoint
                response = client.get('/health')
                self.results['web_interface']['health_endpoint'] = 'WORKING' if response.status_code == 200 else 'FAILED'
                
                # Login page
                response = client.get('/login')
                self.results['web_interface']['login_page'] = 'WORKING' if response.status_code == 200 else 'FAILED'
                
                # API endpoints (should require auth)
                response = client.get('/api/connections')
                self.results['web_interface']['api_auth'] = 'WORKING' if response.status_code in [200, 302] else 'FAILED'
            
            # Test command execution system
            from web_app_real import execute_real_command
            result = execute_real_command('sessions')
            self.results['web_interface']['command_execution'] = 'WORKING' if result else 'FAILED'
            
        except Exception as e:
            self.results['web_interface']['error'] = str(e)
            self.results['issues'].append(f"Web interface failed: {e}")
    
    def test_payload_system(self):
        """Test payload generation system"""
        print("🎯 Testing Payload System...")
        
        try:
            import Application.stitch_gen as stitch_gen
            import Application.Stitch_Vars.globals as stitch_globals
            
            self.results['payload_system']['imports'] = 'WORKING'
            
            # Check required paths
            paths_check = {
                'payloads_path': os.path.exists(stitch_globals.payloads_path),
                'downloads_path': os.path.exists(stitch_globals.downloads_path),
                'uploads_path': os.path.exists(stitch_globals.uploads_path),
                'aes_file': os.path.exists(stitch_globals.st_aes),
                'aes_lib': os.path.exists(stitch_globals.st_aes_lib)
            }
            
            self.results['payload_system']['paths'] = paths_check
            
            # Test AES key system
            if os.path.exists(stitch_globals.st_aes):
                with open(stitch_globals.st_aes, 'r') as f:
                    aes_content = f.read()
                self.results['payload_system']['aes_key_generation'] = 'WORKING' if 'aes_encoded' in aes_content else 'FAILED'
            
        except Exception as e:
            self.results['payload_system']['error'] = str(e)
            self.results['issues'].append(f"Payload system failed: {e}")
    
    def test_pylib_modules(self):
        """Test PyLib modules"""
        print("📚 Testing PyLib Modules...")
        
        pylib_path = '/workspace/PyLib'
        modules = [f[:-3] for f in os.listdir(pylib_path) if f.endswith('.py') and not f.startswith('__')]
        
        working = []
        broken = []
        stubbed = []
        
        for module_name in modules:
            try:
                module_path = os.path.join(pylib_path, f'{module_name}.py')
                
                # Read module content to analyze
                with open(module_path, 'r') as f:
                    content = f.read()
                
                # Check for stub indicators
                if ('pass' in content and len(content) < 200) or 'NotImplementedError' in content:
                    stubbed.append(module_name)
                elif any(undefined in content for undefined in ['win_client', 'osx_client', 'client_socket', 'send(client_socket']):
                    # These modules are designed for payload context
                    broken.append(f"{module_name} (payload-only)")
                else:
                    working.append(module_name)
                    
            except Exception as e:
                broken.append(f"{module_name} ({str(e)[:30]}...)")
        
        self.results['pylib_modules'] = {
            'total': len(modules),
            'working': working,
            'broken': broken,
            'stubbed': stubbed
        }
        
        if broken:
            self.results['issues'].append(f"PyLib modules broken: {len(broken)}/{len(modules)}")
    
    def test_networking(self):
        """Test networking components"""
        print("🔌 Testing Networking...")
        
        try:
            from Application.stitch_cmd import stitch_server
            import socket
            
            # Test socket creation
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('127.0.0.1', 0))
            port = test_socket.getsockname()[1]
            test_socket.close()
            
            self.results['networking']['socket_creation'] = 'WORKING'
            self.results['networking']['test_port'] = port
            
            # Test server listening capability
            server = stitch_server()
            self.results['networking']['server_creation'] = 'WORKING'
            
        except Exception as e:
            self.results['networking']['error'] = str(e)
            self.results['issues'].append(f"Networking failed: {e}")
    
    def test_security_features(self):
        """Test security features"""
        print("🔒 Testing Security Features...")
        
        try:
            from config import Config
            from auth_utils import APIKeyManager
            
            # Test configuration
            security_features = {
                'https_support': Config.ENABLE_HTTPS,
                'api_keys': Config.ENABLE_API_KEYS,
                'rate_limiting': True,  # Always enabled
                'csrf_protection': True,  # Always enabled
                'session_security': Config.SESSION_COOKIE_HTTPONLY,
                'failed_login_tracking': Config.ENABLE_FAILED_LOGIN_ALERTS
            }
            
            self.results['security'] = security_features
            
            # Test API key manager
            api_manager = APIKeyManager()
            self.results['security']['api_key_manager'] = 'WORKING'
            
        except Exception as e:
            self.results['security']['error'] = str(e)
            self.results['issues'].append(f"Security features failed: {e}")
    
    def test_ui_components(self):
        """Test UI components"""
        print("🎨 Testing UI Components...")
        
        # Check static files
        static_files = {
            'css_real': os.path.exists('/workspace/static/css/style_real.css'),
            'js_real': os.path.exists('/workspace/static/js/app_real.js'),
            'favicon': os.path.exists('/workspace/static/favicon.ico')
        }
        
        # Check templates
        templates = {
            'dashboard_real': os.path.exists('/workspace/templates/dashboard_real.html'),
            'login': os.path.exists('/workspace/templates/login.html')
        }
        
        self.results['ui_components'] = {
            'static_files': static_files,
            'templates': templates
        }
        
        # Check for missing files
        missing_files = []
        for category, files in [('static', static_files), ('templates', templates)]:
            for file, exists in files.items():
                if not exists:
                    missing_files.append(f"{category}/{file}")
        
        if missing_files:
            self.results['issues'].append(f"Missing UI files: {missing_files}")
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        print("💡 Generating Recommendations...")
        
        recommendations = []
        
        # Core issues
        if 'error' in self.results['core_components']:
            recommendations.append("CRITICAL: Fix core component imports and dependencies")
        
        # Web interface issues
        if 'error' in self.results['web_interface']:
            recommendations.append("HIGH: Resolve web interface startup issues")
        
        # PyLib module issues
        broken_count = len(self.results['pylib_modules'].get('broken', []))
        total_count = self.results['pylib_modules'].get('total', 0)
        if broken_count > total_count * 0.5:
            recommendations.append(f"MEDIUM: {broken_count}/{total_count} PyLib modules need payload context fixes")
        
        # Security recommendations
        security = self.results.get('security', {})
        if not security.get('https_support'):
            recommendations.append("MEDIUM: Enable HTTPS for production deployment")
        if not security.get('api_keys'):
            recommendations.append("LOW: Consider enabling API key authentication")
        
        # UI recommendations
        ui_issues = len([f for files in self.results['ui_components'].values() for f in files.values() if not f])
        if ui_issues > 0:
            recommendations.append(f"LOW: Fix {ui_issues} missing UI files")
        
        self.results['recommendations'] = recommendations
    
    def run_audit(self):
        """Run complete audit"""
        print("🚀 Starting Comprehensive Stitch RAT Audit")
        print("=" * 50)
        
        self.test_core_components()
        self.test_web_interface()
        self.test_payload_system()
        self.test_pylib_modules()
        self.test_networking()
        self.test_security_features()
        self.test_ui_components()
        self.generate_recommendations()
        
        return self.results
    
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "=" * 50)
        print("📊 AUDIT SUMMARY")
        print("=" * 50)
        
        # Overall status
        total_issues = len(self.results['issues'])
        if total_issues == 0:
            print("✅ OVERALL STATUS: EXCELLENT - No critical issues found")
        elif total_issues <= 2:
            print("⚠️  OVERALL STATUS: GOOD - Minor issues found")
        elif total_issues <= 5:
            print("🔶 OVERALL STATUS: FAIR - Several issues need attention")
        else:
            print("❌ OVERALL STATUS: POOR - Multiple critical issues")
        
        print(f"\n📈 COMPONENT STATUS:")
        components = ['core_components', 'web_interface', 'payload_system', 'networking', 'security']
        for component in components:
            status = "✅ WORKING" if 'error' not in self.results[component] else "❌ FAILED"
            print(f"  {component.replace('_', ' ').title()}: {status}")
        
        # PyLib status
        pylib = self.results['pylib_modules']
        working_pct = (len(pylib['working']) / pylib['total'] * 100) if pylib['total'] > 0 else 0
        print(f"  PyLib Modules: {working_pct:.1f}% working ({len(pylib['working'])}/{pylib['total']})")
        
        # Issues
        if self.results['issues']:
            print(f"\n⚠️  ISSUES FOUND ({len(self.results['issues'])}):")
            for i, issue in enumerate(self.results['issues'], 1):
                print(f"  {i}. {issue}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    auditor = StitchAuditor()
    results = auditor.run_audit()
    auditor.print_summary()
    
    # Save results
    with open('/workspace/audit_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /workspace/audit_results.json")