#!/usr/bin/env python3
"""
Advanced Web Interface Testing
Tests real-time features, WebSocket functionality, and UI components
"""

import os
import sys
import json
import time
import threading
import requests
from datetime import datetime

# Set up environment
os.environ['STITCH_ADMIN_USER'] = 'admin'
os.environ['STITCH_ADMIN_PASSWORD'] = 'test123456789'

def test_web_interface_advanced():
    """Advanced web interface testing"""
    print("🌐 Advanced Web Interface Testing")
    print("=" * 50)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'api_endpoints': {},
        'authentication': {},
        'command_system': {},
        'file_operations': {},
        'ui_functionality': {},
        'issues': []
    }
    
    try:
        from web_app_real import app, socketio, get_stitch_server, execute_real_command
        
        print("✓ Web app imports successful")
        
        # Test Flask app with test client
        with app.test_client() as client:
            print("\n🔍 Testing API Endpoints...")
            
            # Test health endpoint
            response = client.get('/health')
            results['api_endpoints']['health'] = {
                'status_code': response.status_code,
                'response': response.get_json() if response.status_code == 200 else None
            }
            print(f"  Health endpoint: {response.status_code}")
            
            # Test login page
            response = client.get('/login')
            results['api_endpoints']['login_page'] = response.status_code
            print(f"  Login page: {response.status_code}")
            
            # Test dashboard redirect (should redirect to login)
            response = client.get('/')
            results['api_endpoints']['dashboard_redirect'] = response.status_code
            print(f"  Dashboard redirect: {response.status_code}")
            
            # Test authentication
            print("\n🔐 Testing Authentication...")
            
            # Test invalid login
            response = client.post('/login', data={
                'username': 'invalid',
                'password': 'invalid'
            })
            results['authentication']['invalid_login'] = response.status_code
            print(f"  Invalid login: {response.status_code}")
            
            # Test valid login
            response = client.post('/login', data={
                'username': 'admin',
                'password': 'test123456789'
            }, follow_redirects=True)
            results['authentication']['valid_login'] = response.status_code
            print(f"  Valid login: {response.status_code}")
            
            # Test authenticated endpoints
            print("\n⚡ Testing Command System...")
            
            # Test connections API
            response = client.get('/api/connections')
            results['api_endpoints']['connections'] = {
                'status_code': response.status_code,
                'data': response.get_json() if response.status_code == 200 else None
            }
            print(f"  Connections API: {response.status_code}")
            
            # Test server status API
            response = client.get('/api/server/status')
            results['api_endpoints']['server_status'] = {
                'status_code': response.status_code,
                'data': response.get_json() if response.status_code == 200 else None
            }
            print(f"  Server status API: {response.status_code}")
            
            # Test command execution API
            response = client.post('/api/execute', 
                json={'command': 'sessions'},
                headers={'Content-Type': 'application/json'}
            )
            results['command_system']['sessions_command'] = {
                'status_code': response.status_code,
                'success': response.get_json().get('success') if response.status_code == 200 else False
            }
            print(f"  Sessions command: {response.status_code}")
            
            # Test command definitions API
            response = client.get('/api/command_definitions')
            results['command_system']['command_definitions'] = {
                'status_code': response.status_code,
                'count': len(response.get_json().get('definitions', {})) if response.status_code == 200 else 0
            }
            print(f"  Command definitions: {response.status_code}")
            
            # Test file operations
            print("\n📁 Testing File Operations...")
            
            # Test downloads list
            response = client.get('/api/files/downloads')
            results['file_operations']['downloads_list'] = {
                'status_code': response.status_code,
                'count': len(response.get_json()) if response.status_code == 200 else 0
            }
            print(f"  Downloads list: {response.status_code}")
            
            # Test export functionality
            response = client.get('/api/export/logs?format=json')
            results['file_operations']['export_logs'] = response.status_code
            print(f"  Export logs: {response.status_code}")
            
            response = client.get('/api/export/commands?format=csv')
            results['file_operations']['export_commands'] = response.status_code
            print(f"  Export commands: {response.status_code}")
        
        # Test command execution system directly
        print("\n⚡ Testing Command Execution System...")
        
        # Test server-only commands
        commands_to_test = ['sessions', 'history', 'showkey', 'home', 'cls']
        for cmd in commands_to_test:
            try:
                result = execute_real_command(cmd)
                results['command_system'][f'{cmd}_command'] = {
                    'success': True,
                    'output_length': len(result) if result else 0
                }
                print(f"  ✓ {cmd}: {len(result) if result else 0} chars")
            except Exception as e:
                results['command_system'][f'{cmd}_command'] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"  ✗ {cmd}: {e}")
        
        # Test server instance
        print("\n🔌 Testing Server Instance...")
        server = get_stitch_server()
        results['server_instance'] = {
            'listening_port': server.listen_port,
            'active_connections': len(server.inf_sock),
            'has_config': server.Config is not None,
            'has_aes_lib': server.aes_lib is not None
        }
        print(f"  Listening port: {server.listen_port}")
        print(f"  Active connections: {len(server.inf_sock)}")
        
    except Exception as e:
        results['issues'].append(f"Critical error: {str(e)}")
        print(f"❌ Critical error: {e}")
    
    return results

def test_ui_components():
    """Test UI components and static files"""
    print("\n🎨 Testing UI Components...")
    
    ui_results = {
        'static_files': {},
        'templates': {},
        'css_analysis': {},
        'js_analysis': {}
    }
    
    # Check static files
    static_files = {
        'style_real.css': '/workspace/static/css/style_real.css',
        'app_real.js': '/workspace/static/js/app_real.js',
        'favicon.ico': '/workspace/static/favicon.ico',
        'favicon.svg': '/workspace/static/favicon.svg'
    }
    
    for name, path in static_files.items():
        exists = os.path.exists(path)
        ui_results['static_files'][name] = {
            'exists': exists,
            'size': os.path.getsize(path) if exists else 0
        }
        print(f"  {name}: {'✓' if exists else '✗'} ({ui_results['static_files'][name]['size']} bytes)")
    
    # Analyze CSS file
    css_path = '/workspace/static/css/style_real.css'
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        ui_results['css_analysis'] = {
            'lines': len(css_content.splitlines()),
            'has_responsive': '@media' in css_content,
            'has_animations': 'animation' in css_content or 'transition' in css_content,
            'has_grid': 'grid' in css_content,
            'has_flexbox': 'flex' in css_content
        }
        print(f"  CSS analysis: {ui_results['css_analysis']['lines']} lines, responsive: {ui_results['css_analysis']['has_responsive']}")
    
    # Analyze JavaScript file
    js_path = '/workspace/static/js/app_real.js'
    if os.path.exists(js_path):
        with open(js_path, 'r') as f:
            js_content = f.read()
        
        ui_results['js_analysis'] = {
            'lines': len(js_content.splitlines()),
            'has_websocket': 'socket.io' in js_content or 'WebSocket' in js_content,
            'has_ajax': 'fetch(' in js_content or 'XMLHttpRequest' in js_content,
            'has_event_listeners': 'addEventListener' in js_content,
            'has_error_handling': 'try {' in js_content or 'catch(' in js_content
        }
        print(f"  JS analysis: {ui_results['js_analysis']['lines']} lines, WebSocket: {ui_results['js_analysis']['has_websocket']}")
    
    # Check templates
    templates = {
        'dashboard_real.html': '/workspace/templates/dashboard_real.html',
        'login.html': '/workspace/templates/login.html'
    }
    
    for name, path in templates.items():
        exists = os.path.exists(path)
        ui_results['templates'][name] = {
            'exists': exists,
            'size': os.path.getsize(path) if exists else 0
        }
        print(f"  {name}: {'✓' if exists else '✗'} ({ui_results['templates'][name]['size']} bytes)")
    
    return ui_results

def test_payload_generation():
    """Test payload generation capabilities"""
    print("\n🎯 Testing Payload Generation...")
    
    payload_results = {
        'aes_system': {},
        'payload_paths': {},
        'generation_capability': {}
    }
    
    try:
        import Application.Stitch_Vars.globals as stitch_globals
        import Application.Stitch_Vars.st_aes as st_aes
        
        # Test AES system
        payload_results['aes_system'] = {
            'aes_file_exists': os.path.exists(stitch_globals.st_aes),
            'aes_lib_exists': os.path.exists(stitch_globals.st_aes_lib),
            'secret_available': hasattr(st_aes, 'secret')
        }
        print(f"  AES file: {'✓' if payload_results['aes_system']['aes_file_exists'] else '✗'}")
        print(f"  AES library: {'✓' if payload_results['aes_system']['aes_lib_exists'] else '✗'}")
        
        # Test payload paths
        paths_to_check = {
            'payloads': stitch_globals.payloads_path,
            'downloads': stitch_globals.downloads_path,
            'uploads': stitch_globals.uploads_path,
            'tools': stitch_globals.tools_path
        }
        
        for name, path in paths_to_check.items():
            exists = os.path.exists(path)
            payload_results['payload_paths'][name] = {
                'exists': exists,
                'writable': os.access(path, os.W_OK) if exists else False
            }
            print(f"  {name} path: {'✓' if exists else '✗'} ({'writable' if payload_results['payload_paths'][name]['writable'] else 'read-only'})")
        
        # Test generation imports
        try:
            import Application.stitch_gen as stitch_gen
            payload_results['generation_capability']['imports'] = True
            print("  ✓ Payload generation imports successful")
        except Exception as e:
            payload_results['generation_capability']['imports'] = False
            payload_results['generation_capability']['import_error'] = str(e)
            print(f"  ✗ Payload generation imports failed: {e}")
        
    except Exception as e:
        payload_results['error'] = str(e)
        print(f"  ❌ Payload testing error: {e}")
    
    return payload_results

def run_advanced_tests():
    """Run all advanced tests"""
    print("🚀 Starting Advanced Stitch RAT Testing")
    print("=" * 60)
    
    # Run tests
    web_results = test_web_interface_advanced()
    ui_results = test_ui_components()
    payload_results = test_payload_generation()
    
    # Combine results
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'web_interface': web_results,
        'ui_components': ui_results,
        'payload_system': payload_results,
        'summary': {}
    }
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 ADVANCED TEST SUMMARY")
    print("=" * 60)
    
    # Web interface summary
    api_working = sum(1 for endpoint in web_results['api_endpoints'].values() 
                     if isinstance(endpoint, dict) and endpoint.get('status_code') == 200 
                     or isinstance(endpoint, int) and endpoint == 200)
    api_total = len(web_results['api_endpoints'])
    
    print(f"🌐 Web Interface: {api_working}/{api_total} API endpoints working")
    
    # UI components summary
    static_working = sum(1 for file_info in ui_results['static_files'].values() if file_info['exists'])
    static_total = len(ui_results['static_files'])
    
    template_working = sum(1 for template_info in ui_results['templates'].values() if template_info['exists'])
    template_total = len(ui_results['templates'])
    
    print(f"🎨 UI Components: {static_working}/{static_total} static files, {template_working}/{template_total} templates")
    
    # Command system summary
    cmd_working = sum(1 for cmd_result in web_results['command_system'].values() 
                     if isinstance(cmd_result, dict) and cmd_result.get('success'))
    cmd_total = len([k for k in web_results['command_system'].keys() if k.endswith('_command')])
    
    print(f"⚡ Command System: {cmd_working}/{cmd_total} commands working")
    
    # Overall assessment
    total_issues = len(web_results.get('issues', []))
    if total_issues == 0 and api_working >= api_total * 0.8:
        print("\n✅ OVERALL: EXCELLENT - Web interface fully functional")
    elif total_issues <= 2:
        print("\n⚠️  OVERALL: GOOD - Minor issues detected")
    else:
        print("\n🔶 OVERALL: NEEDS ATTENTION - Multiple issues found")
    
    # Save detailed results
    with open('/workspace/advanced_test_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /workspace/advanced_test_results.json")
    
    return final_results

if __name__ == "__main__":
    results = run_advanced_tests()