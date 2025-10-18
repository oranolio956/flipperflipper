#!/usr/bin/env python3
"""
Simple test to verify payload generation actually works
"""

import os
import sys
import shutil
from pathlib import Path

# Add to path
sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'

from web_payload_generator import web_payload_gen

def test_simple_generation():
    """Test basic payload generation"""
    
    print("="*60)
    print("TESTING PAYLOAD GENERATION")
    print("="*60)
    
    # Test Python script generation first (simplest case)
    config = {
        'bind_host': '0.0.0.0',
        'bind_port': '4433',
        'listen_host': '',
        'listen_port': '',
        'enable_bind': True,
        'enable_listen': False,
        'platform': 'python',
        'payload_name': 'test_payload'
    }
    
    print("\n[1] Testing Python script generation...")
    result = web_payload_gen.generate_payload(config)
    
    if result['success']:
        print(f"✓ Success: {result['message']}")
        print(f"  Path: {result['payload_path']}")
        print(f"  Size: {result['size']} bytes")
        
        # Check file exists
        if os.path.exists(result['payload_path']):
            print(f"  ✓ File exists")
            
            # Check it's a Python file
            with open(result['payload_path'], 'r') as f:
                content = f.read(100)
                if 'python' in content.lower() or 'from' in content:
                    print(f"  ✓ Looks like Python code")
                else:
                    print(f"  ✗ Doesn't look like Python")
        else:
            print(f"  ✗ File doesn't exist!")
            return False
    else:
        print(f"✗ Failed: {result['message']}")
        return False
    
    # Now test Linux binary generation
    print("\n[2] Testing Linux binary generation...")
    config['platform'] = 'linux'
    config['payload_name'] = 'test_linux'
    
    result = web_payload_gen.generate_payload(config)
    
    if result['success']:
        print(f"✓ Success: {result['message']}")
        print(f"  Path: {result['payload_path']}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Type: {result['payload_type']}")
        
        if os.path.exists(result['payload_path']):
            print(f"  ✓ File exists")
            
            # Check if it's executable
            if result['payload_type'] == 'executable':
                print(f"  ✓ Marked as executable type")
            elif result['payload_type'] == 'script':
                print(f"  ⚠ Fell back to script (PyInstaller might have failed)")
        else:
            print(f"  ✗ File doesn't exist!")
    else:
        print(f"✗ Failed: {result['message']}")
    
    return True

if __name__ == "__main__":
    success = test_simple_generation()
    print("\n" + "="*60)
    if success:
        print("BASIC TEST PASSED")
    else:
        print("TEST FAILED")
    print("="*60)