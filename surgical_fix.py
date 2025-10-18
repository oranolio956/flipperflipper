#!/usr/bin/env python3
"""
SURGICAL FIX - Carefully fix the critical files with precision
"""

import os
import re
import shutil
import subprocess

def fix_critical_files():
    """Fix the most critical files with surgical precision"""
    
    # First, identify files with "unmatched ')'" errors
    files_to_fix = []
    
    critical_files = [
        '/workspace/web_app_real.py',
        '/workspace/web_payload_generator.py',
        '/workspace/Application/stitch_cmd.py',
        '/workspace/Application/stitch_pyld_config.py',
        '/workspace/Application/stitch_cross_compile.py',
        '/workspace/Application/stitch_utils.py'
    ]
    
    print("="*70)
    print("SURGICAL FIX - CRITICAL FILES")
    print("="*70)
    
    # Restore from backup first
    backup_dir = '/workspace/.backup_1760821534'
    
    if os.path.exists(backup_dir):
        print("\n[RESTORE] Restoring critical files from backup...")
        
        for filepath in critical_files:
            backup_path = filepath.replace('/workspace', backup_dir)
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, filepath)
                print(f"  ✓ Restored {os.path.basename(filepath)}")
                
    # Now apply minimal, careful fixes
    print("\n[FIX] Applying minimal fixes...")
    
    for filepath in critical_files:
        if not os.path.exists(filepath):
            continue
            
        print(f"\nProcessing {os.path.basename(filepath)}...")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        original = content
        
        # Fix only Python 2 print statements (carefully)
        # Match print followed by space and non-parenthesis
        content = re.sub(
            r'\bprint\s+(["\'])([^"\']*)\1(?=\s|$|;)',
            r'print(\1\2\1)',
            content
        )
        
        # Fix print with variable (no quotes)
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip comments
            if line.strip().startswith('#'):
                fixed_lines.append(line)
                continue
                
            # Fix print statements carefully
            if re.match(r'^\s*print\s+[^(]', line):
                # Extract the print content
                match = re.match(r'^(\s*)print\s+(.+?)(\s*#.*)?$', line)
                if match:
                    indent = match.group(1)
                    content_part = match.group(2)
                    comment = match.group(3) or ''
                    
                    # Don't wrap if it's already a valid expression
                    if not content_part.startswith('('):
                        line = f"{indent}print({content_part}){comment}"
                        
            fixed_lines.append(line)
            
        content = '\n'.join(fixed_lines)
        
        # Fix specific known issues
        
        # Fix raw_input -> input
        content = content.replace('raw_input(', 'input(')
        
        # Fix xrange -> range
        content = re.sub(r'\bxrange\(', 'range(', content)
        
        # Fix .has_key() - be more careful
        content = re.sub(
            r'(\w+)\.has_key\(([^)]+)\)',
            r'\2 in \1',
            content
        )
        
        # Fix iteritems, iterkeys, itervalues
        content = content.replace('.iteritems()', '.items()')
        content = content.replace('.iterkeys()', '.keys()')
        content = content.replace('.itervalues()', '.values()')
        
        # Fix Python 2 exceptions
        content = re.sub(
            r'except\s+(\w+),\s*(\w+):',
            r'except \1 as \2:',
            content
        )
        
        # Fix unicode() -> str()
        content = re.sub(r'\bunicode\(', 'str(', content)
        
        # Save if modified
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Test the file
            result = subprocess.run(
                f'python3 -m py_compile {filepath}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"  ✓ Fixed and verified")
            else:
                # Show the specific error
                error = result.stderr.split('SyntaxError:')[-1].strip() if 'SyntaxError' in result.stderr else 'Unknown error'
                print(f"  ✗ Still has error: {error[:100]}")
                
                # Try to pinpoint the line
                if 'line' in result.stderr:
                    match = re.search(r'line (\d+)', result.stderr)
                    if match:
                        line_num = int(match.group(1))
                        lines = content.split('\n')
                        if 0 < line_num <= len(lines):
                            print(f"    Line {line_num}: {lines[line_num-1][:80]}")
        else:
            print(f"  ℹ No changes needed")
            
            # Still test it
            result = subprocess.run(
                f'python3 -m py_compile {filepath}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  ✗ Has existing error")
                
    print("\n[VALIDATION] Testing critical imports...")
    
    tests = [
        ('Web App', 'from web_app_real import app'),
        ('C2 Server', 'from Application.stitch_cmd import stitch_server'),
        ('Payload Gen', 'from web_payload_generator import WebPayloadGenerator')
    ]
    
    passed = 0
    for name, test in tests:
        result = subprocess.run(
            f'python3 -c "{test}; print(\'OK\')"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}")
            
    print(f"\n[RESULT] {passed}/{len(tests)} critical imports working")
    
    if passed == len(tests):
        print("\n🎉 ALL CRITICAL COMPONENTS FIXED!")
    else:
        print("\n⚠️  Some components still need manual attention")

def main():
    fix_critical_files()

if __name__ == "__main__":
    main()