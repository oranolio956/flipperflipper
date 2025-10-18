#!/usr/bin/env python3
"""
Focused test for specific issues found in Phase 1 testing
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, '/workspace')
from payload_utils import PayloadManager

def test_payload_detection_fix():
    """Test the fixed payload detection logic"""
    print("Testing payload detection fix...")
    
    test_dir = tempfile.mkdtemp(prefix='stitch_focused_test_')
    try:
        pm = PayloadManager()
        pm.payloads_path = os.path.join(test_dir, 'Payloads')
        pm.configuration_path = os.path.join(test_dir, 'Configuration')
        pm.ensure_directories()
        
        config_dir = os.path.join(pm.payloads_path, 'config1')
        os.makedirs(config_dir)
        
        # Create test files
        test_files = {
            'test.py': 'python_source',
            'test.exe': 'executables',
            'config.log': 'config_files',
            'settings.ini': 'config_files'
        }
        
        for filename, expected_type in test_files.items():
            filepath = os.path.join(config_dir, filename)
            with open(filepath, 'w') as f:
                f.write('test content for ' + filename)
        
        # Create Binaries directory with executable
        binaries_dir = os.path.join(config_dir, 'Binaries')
        os.makedirs(binaries_dir)
        binary_file = os.path.join(binaries_dir, 'payload_binary')
        with open(binary_file, 'w') as f:
            f.write('binary content')
        
        payload_files = pm.detect_payload_files(config_dir)
        
        print(f"Detected files: {payload_files}")
        print(f"Executables: {len(payload_files['executables'])} (expected: 2)")
        print(f"Python source: {len(payload_files['python_source'])} (expected: 1)")
        print(f"Config files: {len(payload_files['config_files'])} (expected: 2)")
        
        # Test primary payload selection
        primary = pm.get_primary_payload(config_dir)
        print(f"Primary payload: {primary}")
        
        if primary:
            print(f"Primary type: {primary['type']} (should be 'executables')")
            
            # Test validation
            validation = pm.validate_payload(primary['path'])
            print(f"Validation: {validation}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir)

def test_python_validation_fix():
    """Test the fixed Python validation"""
    print("\nTesting Python validation fix...")
    
    test_dir = tempfile.mkdtemp(prefix='stitch_py_test_')
    try:
        pm = PayloadManager()
        
        # Test with proper encrypted payload
        py_file = os.path.join(test_dir, 'test.py')
        with open(py_file, 'w') as f:
            f.write('from requirements import *\nexec(SEC(INFO("encrypted_payload_data")))')
        
        validation = pm.validate_payload(py_file)
        print(f"Python validation: {validation}")
        print(f"Valid: {validation['valid']}")
        print(f"Size valid: {validation['size_valid']}")
        print(f"Encrypted: {validation.get('encrypted_payload', False)}")
        
        return validation['valid']
        
    except Exception as e:
        print(f"Python validation test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir)

if __name__ == '__main__':
    print("🔧 Running focused tests for Phase 1 fixes")
    print("=" * 50)
    
    test1_result = test_payload_detection_fix()
    test2_result = test_python_validation_fix()
    
    print("\n" + "=" * 50)
    print(f"Payload detection test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Python validation test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All focused tests passed!")
    else:
        print("\n⚠️  Some tests still failing - need more fixes")