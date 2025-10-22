#!/usr/bin/env python3
"""
Phase 1 Testing Suite for Stitch Payload Validation
Comprehensive testing of payload generation, connection, and dashboard display
"""

import os
import sys
import time
import json
import hashlib
import subprocess
import threading
import requests
import websocket
import psutil
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add workspace to path
sys.path.insert(0, '/workspace')

class Phase1Tester:
    def __init__(self):
        self.base_path = Path('/workspace')
        self.test_results = []
        self.server_process = None
        self.server_url = 'http://localhost:5000'
        self.server_port = 4040
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_payload_generation(self) -> Dict[str, Any]:
        """Test payload generation for all platforms and types"""
        self.log("Starting payload generation testing...")
        
        try:
            from unified_payload_generator import generate_payload, unified_generator
            
            platforms = ['linux', 'windows', 'macos']
            payload_types = ['python']  # Start with python only for now
            
            results = {
                'success': True,
                'generated_payloads': [],
                'errors': []
            }
            
            for platform in platforms:
                for payload_type in payload_types:
                    config = {
                        'type': payload_type,
                        'platform': platform,
                        'bind_host': 'localhost',
                        'bind_port': '4040',
                        'listen_host': 'localhost', 
                        'listen_port': '4040',
                        'payload_name': f'test_{platform}_{payload_type}',
                        'obfuscate': True
                    }
                    
                    self.log(f"Generating {platform} {payload_type} payload...")
                    result = generate_payload(config)
                    
                    if result['success']:
                        # Analyze the generated payload
                        payload_path = Path(result['payload_path'])
                        file_size = payload_path.stat().st_size
                        file_hash = hashlib.sha256(payload_path.read_bytes()).hexdigest()
                        
                        payload_info = {
                            'platform': platform,
                            'type': payload_type,
                            'filename': result['filename'],
                            'path': str(payload_path),
                            'size': file_size,
                            'hash': file_hash,
                            'generated_at': datetime.now().isoformat()
                        }
                        
                        results['generated_payloads'].append(payload_info)
                        self.log(f"✓ Generated {result['filename']} ({file_size} bytes)")
                    else:
                        error_msg = f"Failed to generate {platform} {payload_type}: {result['error']}"
                        results['errors'].append(error_msg)
                        self.log(f"✗ {error_msg}", "ERROR")
                        results['success'] = False
            
            return results
            
        except Exception as e:
            self.log(f"Payload generation test failed: {str(e)}", "ERROR")
            return {
                'success': False,
                'generated_payloads': [],
                'errors': [str(e)]
            }
    
    def start_stitch_server(self) -> bool:
        """Start the Stitch server for testing"""
        self.log("Starting Stitch server...")
        
        try:
            # Start server in background
            self.server_process = subprocess.Popen([
                'python3', 'web_app_real.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='/workspace')
            
            # Wait for server to be ready
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get(f"{self.server_url}/", timeout=2)
                    if response.status_code == 200:
                        self.log("✓ Stitch server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(1)
                self.log(f"Waiting for server... (attempt {attempt + 1}/{max_attempts})")
            
            self.log("✗ Server failed to start within timeout", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"Failed to start server: {str(e)}", "ERROR")
            return False
    
    def test_server_connection(self) -> Dict[str, Any]:
        """Test server connectivity and basic functionality"""
        self.log("Testing server connection...")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.server_url}/", timeout=10)
            if response.status_code != 200:
                return {'success': False, 'error': f'Server returned status {response.status_code}'}
            
            # Test targets endpoint
            targets_response = requests.get(f"{self.server_url}/api/targets", timeout=10)
            if targets_response.status_code != 200:
                return {'success': False, 'error': f'Targets endpoint failed with status {targets_response.status_code}'}
            
            targets_data = targets_response.json()
            
            return {
                'success': True,
                'server_status': {'status': 'running', 'message': 'Server is accessible'},
                'targets_count': len(targets_data.get('targets', [])),
                'targets_data': targets_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_network_monitoring(self) -> Dict[str, Any]:
        """Test network monitoring capabilities"""
        self.log("Testing network monitoring...")
        
        try:
            # Check if port 4040 is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.server_port))
            sock.close()
            
            if result == 0:
                self.log("✓ Server port 4040 is accessible")
                return {'success': True, 'port_accessible': True}
            else:
                self.log("✗ Server port 4040 is not accessible", "ERROR")
                return {'success': False, 'port_accessible': False}
                
        except Exception as e:
            self.log(f"Network monitoring test failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}
    
    def test_system_resources(self) -> Dict[str, Any]:
        """Test system resource usage"""
        self.log("Testing system resources...")
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            resources = {
                'cpu_percent': cpu_percent,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_free': disk.free,
                'disk_percent': disk.percent
            }
            
            self.log(f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
            
            return {'success': True, 'resources': resources}
            
        except Exception as e:
            self.log(f"Resource monitoring failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all Phase 1 tests"""
        self.log("=" * 60)
        self.log("STARTING PHASE 1 COMPREHENSIVE TESTING")
        self.log("=" * 60)
        
        test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'overall_success': True
        }
        
        # Test 1: Payload Generation
        self.log("\n--- TEST 1: PAYLOAD GENERATION ---")
        payload_results = self.test_payload_generation()
        test_results['tests']['payload_generation'] = payload_results
        if not payload_results['success']:
            test_results['overall_success'] = False
        
        # Test 2: Server Startup
        self.log("\n--- TEST 2: SERVER STARTUP ---")
        server_started = self.start_stitch_server()
        test_results['tests']['server_startup'] = {
            'success': server_started,
            'server_process_running': self.server_process is not None
        }
        if not server_started:
            test_results['overall_success'] = False
            return test_results
        
        # Test 3: Server Connection
        self.log("\n--- TEST 3: SERVER CONNECTION ---")
        connection_results = self.test_server_connection()
        test_results['tests']['server_connection'] = connection_results
        if not connection_results['success']:
            test_results['overall_success'] = False
        
        # Test 4: Network Monitoring
        self.log("\n--- TEST 4: NETWORK MONITORING ---")
        network_results = self.test_network_monitoring()
        test_results['tests']['network_monitoring'] = network_results
        if not network_results['success']:
            test_results['overall_success'] = False
        
        # Test 5: System Resources
        self.log("\n--- TEST 5: SYSTEM RESOURCES ---")
        resource_results = self.test_system_resources()
        test_results['tests']['system_resources'] = resource_results
        if not resource_results['success']:
            test_results['overall_success'] = False
        
        test_results['end_time'] = datetime.now().isoformat()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("PHASE 1 TESTING COMPLETE")
        self.log("=" * 60)
        
        if test_results['overall_success']:
            self.log("✓ ALL TESTS PASSED - Phase 1 Complete!")
        else:
            self.log("✗ SOME TESTS FAILED - Check results above", "ERROR")
        
        return test_results
    
    def cleanup(self):
        """Clean up test resources"""
        if self.server_process:
            self.log("Stopping server...")
            self.server_process.terminate()
            self.server_process.wait(timeout=10)

def main():
    """Main testing function"""
    tester = Phase1Tester()
    
    try:
        results = tester.run_comprehensive_test()
        
        # Save results
        results_file = '/workspace/phase1_test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nTest results saved to: {results_file}")
        
        return results['overall_success']
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        return False
    except Exception as e:
        print(f"Testing failed with error: {str(e)}")
        return False
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)