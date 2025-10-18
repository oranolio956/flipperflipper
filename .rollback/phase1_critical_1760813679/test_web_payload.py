#!/usr/bin/env python3
"""
Test script to verify web payload generation works correctly
"""

import os
import sys
import json
import time
from pathlib import Path

# Add workspace to path
sys.path.insert(0, '/workspace')

def test_payload_generation():
    """Test the payload generation functionality"""
    
    print("="*70)
    print("TESTING WEB PAYLOAD GENERATION")
    print("="*70)
    
    # Import the web payload generator
    try:
        from web_payload_generator import web_payload_gen
        print("✓ Successfully imported web_payload_generator")
    except ImportError as e:
        print(f"✗ Failed to import web_payload_generator: {e}")
        return False
    
    # Test configurations
    test_cases = [
        {
            'name': 'Linux Binary Test',
            'config': {
                'bind_host': '0.0.0.0',
                'bind_port': '4433',
                'listen_host': '',
                'listen_port': '',
                'enable_bind': True,
                'enable_listen': False,
                'platform': 'linux',
                'payload_name': 'test_linux_payload'
            },
            'expected_type': 'executable',
            'expected_extension': None  # Linux binaries have no extension
        },
        {
            'name': 'Python Script Test',
            'config': {
                'bind_host': '',
                'bind_port': '',
                'listen_host': '192.168.1.100',
                'listen_port': '8080',
                'enable_bind': False,
                'enable_listen': True,
                'platform': 'python',
                'payload_name': 'test_python_payload'
            },
            'expected_type': 'script',
            'expected_extension': '.py'
        },
        {
            'name': 'Windows Cross-Compile Test',
            'config': {
                'bind_host': '0.0.0.0',
                'bind_port': '9999',
                'listen_host': 'attacker.com',
                'listen_port': '443',
                'enable_bind': True,
                'enable_listen': True,
                'platform': 'windows',
                'payload_name': 'test_windows_payload'
            },
            'expected_type': 'executable',  # May fall back to script if Wine not available
            'expected_extension': '.exe'  # Or .py if fallback
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['name']}")
        print("-"*50)
        
        start_time = time.time()
        
        try:
            # Generate payload
            result = web_payload_gen.generate_payload(test_case['config'])
            
            elapsed_time = time.time() - start_time
            
            if result['success']:
                print(f"✓ Generation successful in {elapsed_time:.2f} seconds")
                print(f"  Payload Path: {result['payload_path']}")
                print(f"  Type: {result['payload_type']}")
                print(f"  Platform: {result['platform']}")
                print(f"  Size: {result['size']:,} bytes")
                print(f"  Filename: {result['filename']}")
                
                # Verify file exists
                if os.path.exists(result['payload_path']):
                    print(f"  ✓ File exists at specified path")
                    
                    # Check file size
                    actual_size = os.path.getsize(result['payload_path'])
                    if actual_size == result['size']:
                        print(f"  ✓ File size matches ({actual_size:,} bytes)")
                    else:
                        print(f"  ✗ File size mismatch! Expected: {result['size']}, Got: {actual_size}")
                    
                    # Check file type
                    if test_case['expected_extension']:
                        if result['filename'].endswith(test_case['expected_extension']):
                            print(f"  ✓ File extension matches expected: {test_case['expected_extension']}")
                        elif test_case['name'] == 'Windows Cross-Compile Test' and result['filename'].endswith('.py'):
                            print(f"  ⚠ Fell back to Python script (Wine/PyInstaller not available)")
                        else:
                            print(f"  ✗ Unexpected file extension: {result['filename']}")
                    
                    # Check if file is readable
                    try:
                        with open(result['payload_path'], 'rb') as f:
                            header = f.read(100)
                            if header:
                                print(f"  ✓ File is readable")
                                
                                # Check file signatures
                                if header.startswith(b'MZ'):
                                    print(f"  ✓ Windows PE executable detected")
                                elif header.startswith(b'\x7fELF'):
                                    print(f"  ✓ Linux ELF executable detected")
                                elif b'#!/usr/bin/env python' in header or b'from requirements import' in header:
                                    print(f"  ✓ Python script detected")
                            else:
                                print(f"  ✗ File appears to be empty")
                    except Exception as e:
                        print(f"  ✗ Error reading file: {e}")
                    
                    success_count += 1
                else:
                    print(f"  ✗ File does not exist at: {result['payload_path']}")
                
                # Check for warnings
                if 'warning' in result:
                    print(f"  ⚠ Warning: {result['warning']}")
                
            else:
                print(f"✗ Generation failed: {result['message']}")
                
        except Exception as e:
            print(f"✗ Test crashed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {len(test_cases)}")
    print(f"Tests Passed: {success_count}")
    print(f"Tests Failed: {len(test_cases) - success_count}")
    
    if success_count == len(test_cases):
        print("\n✓ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n✗ {len(test_cases) - success_count} test(s) failed")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    
    print("\n" + "="*70)
    print("DEPENDENCY CHECK")
    print("="*70)
    
    dependencies = {
        'PyInstaller': False,
        'Wine': False,
        'Python3': False
    }
    
    # Check PyInstaller
    try:
        import PyInstaller
        dependencies['PyInstaller'] = True
        print("✓ PyInstaller: Installed (Python module)")
    except ImportError:
        import shutil
        if shutil.which('pyinstaller'):
            dependencies['PyInstaller'] = True
            print("✓ PyInstaller: Installed (command line)")
        else:
            print("✗ PyInstaller: Not installed")
            print("  Install with: pip install pyinstaller")
    
    # Check Wine
    import shutil
    if shutil.which('wine'):
        dependencies['Wine'] = True
        print("✓ Wine: Installed")
    else:
        print("✗ Wine: Not installed (optional for Windows cross-compilation)")
        print("  Install with: sudo apt-get install wine wine32 wine64")
    
    # Check Python3
    if shutil.which('python3'):
        dependencies['Python3'] = True
        print("✓ Python3: Installed")
    else:
        print("✗ Python3: Not installed")
    
    # Check if directories exist
    print("\n[Directory Structure]")
    dirs_to_check = [
        'Application',
        'Application/Stitch_Vars',
        'Configuration',
        'Payloads'
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}: Exists")
        else:
            print(f"✗ {dir_path}: Missing")
            os.makedirs(dir_path, exist_ok=True)
            print(f"  Created: {dir_path}")
    
    return dependencies


if __name__ == "__main__":
    print("\n" + "="*70)
    print("WEB PAYLOAD GENERATION TEST SUITE")
    print("="*70)
    
    # Check dependencies first
    deps = check_dependencies()
    
    if not deps['PyInstaller']:
        print("\n⚠ WARNING: PyInstaller not installed - only Python scripts will be generated")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Run tests
    success = test_payload_generation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)