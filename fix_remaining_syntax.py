#!/usr/bin/env python3
"""
Fix remaining syntax errors with precision
"""

import os
import re
import subprocess
import py_compile

def find_syntax_errors():
    """Find all files with syntax errors"""
    errors = {}
    
    for root, dirs, files in os.walk('/workspace'):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.rollback', '.backup_1760821534']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # Try to compile
                result = subprocess.run(
                    f'python3 -m py_compile {filepath}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    errors[filepath] = result.stderr
                    
    return errors

def fix_file_syntax(filepath, error_msg):
    """Fix syntax in a specific file based on error"""
    print(f"\nFixing {os.path.basename(filepath)}")
    print(f"  Error: {error_msg.split('SyntaxError:')[-1].strip()[:100] if 'SyntaxError' in error_msg else 'Parse error'}")
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        original = content
        
        # Fix unmatched parentheses in regex patterns
        if "unmatched ')'" in error_msg:
            # Fix has_key conversion that went wrong
            content = re.sub(r' in ([^)]+)\)', r'.\1)', content)
            
        # Fix invalid syntax from bad print conversions
        if "invalid syntax" in error_msg:
            # Fix print statements that were incorrectly converted
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Fix print with multiple args not in parens
                if 'print(' in line and line.count('(') != line.count(')'):
                    # Balance parentheses
                    opens = line.count('(')
                    closes = line.count(')')
                    if opens > closes:
                        line += ')' * (opens - closes)
                    elif closes > opens:
                        line = line.replace(')', '', closes - opens)
                        
                fixed_lines.append(line)
                
            content = '\n'.join(fixed_lines)
            
        # Fix specific web_app_real.py issue
        if 'web_app_real.py' in filepath:
            # Fix any lingering print statement issues
            content = re.sub(r'print\s+([^(][^,\n]+)$', r'print(\1)', content, flags=re.MULTILINE)
            
        # Fix specific web_payload_generator.py issues
        if 'web_payload_generator.py' in filepath:
            # Remove duplicate cleanup functions or fix indentation
            lines = content.split('\n')
            fixed_lines = []
            in_cleanup = False
            cleanup_count = 0
            
            for i, line in enumerate(lines):
                if 'def cleanup_old_payloads' in line:
                    cleanup_count += 1
                    if cleanup_count > 1:
                        # Skip duplicate cleanup function
                        in_cleanup = True
                        continue
                        
                if in_cleanup:
                    # Skip until next function or class
                    if line.startswith('def ') or line.startswith('class '):
                        in_cleanup = False
                        fixed_lines.append(line)
                    continue
                    
                fixed_lines.append(line)
                
            content = '\n'.join(fixed_lines)
            
        # Fix stitch_cmd.py specific issues
        if 'stitch_cmd.py' in filepath:
            # Fix any regex with unescaped characters
            content = re.sub(r'\\([^\\nrt"\'])', r'\\\\\1', content)
            
        # Save if modified
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Test if it's fixed
            result = subprocess.run(
                f'python3 -m py_compile {filepath}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"  ✓ Fixed successfully")
                return True
            else:
                print(f"  ⚠ Still has issues, attempting alternate fix...")
                
                # Restore and try alternate fix
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # More aggressive fixes
                
                # Fix all print statements
                content = re.sub(r'\bprint\s+(".*?")', r'print(\1)', content)
                content = re.sub(r"\bprint\s+('.*?')", r"print(\1)", content)
                
                # Fix .has_key that was incorrectly converted
                content = re.sub(r'\.in\s+([^)]+)\)', r'.get(\1) is not None', content)
                
                # Balance all parentheses
                lines = content.split('\n')
                fixed_lines = []
                for line in lines:
                    opens = line.count('(')
                    closes = line.count(')')
                    if opens > closes and not line.strip().endswith('\\'):
                        line += ')' * (opens - closes)
                    fixed_lines.append(line)
                content = '\n'.join(fixed_lines)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # Final test
                result = subprocess.run(
                    f'python3 -m py_compile {filepath}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"  ✓ Fixed with alternate approach")
                    return True
                else:
                    print(f"  ✗ Manual intervention needed")
                    
    except Exception as e:
        print(f"  ✗ Error processing file: {e}")
        
    return False

def main():
    print("="*70)
    print("FIXING REMAINING SYNTAX ERRORS")
    print("="*70)
    
    # Find all syntax errors
    print("\n[SCANNING] Finding files with syntax errors...")
    errors = find_syntax_errors()
    
    print(f"Found {len(errors)} files with syntax errors")
    
    # Fix each file
    fixed = 0
    for filepath, error_msg in errors.items():
        if fix_file_syntax(filepath, error_msg):
            fixed += 1
            
    print("\n" + "="*70)
    print(f"RESULTS: Fixed {fixed}/{len(errors)} files")
    
    # Test critical imports
    print("\n[VALIDATION] Testing critical imports...")
    
    tests = [
        'from web_app_real import app',
        'from web_payload_generator import WebPayloadGenerator',
        'from Application.stitch_cmd import stitch_server'
    ]
    
    for test in tests:
        result = subprocess.run(
            f'python3 -c "{test}; print(\'OK\')"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ {test.split()[1]}")
        else:
            print(f"  ✗ {test.split()[1]}")
            
            # Show specific error
            if result.stderr:
                error_line = result.stderr.split('\n')[-2] if '\n' in result.stderr else result.stderr
                print(f"    Error: {error_line}")

if __name__ == "__main__":
    main()