#!/usr/bin/env python3
"""
Script to decode ALL obfuscated Configuration files
"""

import base64
import zlib
import re
import os
import glob

def decode_obfuscated_file(filepath):
    """Decode a file with exec(SEC(INFO(...))) pattern"""
    
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the exec(SEC(INFO(...))) pattern
    match = re.search(r'exec\(SEC\(INFO\("(.+?)"\)\)\)', content, re.DOTALL)
    
    if match:
        encoded_data = match.group(1)
        
        try:
            # Decode base64
            decoded_b64 = base64.b64decode(encoded_data)
            
            # Decompress with zlib
            decompressed = zlib.decompress(decoded_b64)
            
            # Convert to string
            original_code = decompressed.decode('utf-8')
            
            print(f"Successfully decoded {filepath}")
            print(f"Original size: {len(encoded_data)} chars (base64)")
            print(f"Decoded size: {len(original_code)} chars")
            
            # Check for any suspicious content
            suspicious_found = []
            if 'subprocess' in original_code:
                suspicious_found.append("subprocess calls")
            if 'eval' in original_code:
                suspicious_found.append("eval calls")
            if 'exec(' in original_code:
                suspicious_found.append("exec calls")
            if 'os.system' in original_code:
                suspicious_found.append("os.system calls")
            
            if suspicious_found:
                print(f"WARNING: Contains {', '.join(suspicious_found)}")
            
            return original_code
            
        except Exception as e:
            print(f"ERROR decoding {filepath}: {e}")
            return None
    else:
        print(f"No obfuscated pattern found in {filepath}")
        return None

def main():
    """Decode all obfuscated files"""
    
    # Find all Python files in Configuration directory
    python_files = glob.glob('Configuration/*.py')
    
    decoded_count = 0
    
    for filepath in python_files:
        # Skip already decoded files
        if '_clean.py' in filepath:
            continue
            
        decoded = decode_obfuscated_file(filepath)
        
        if decoded:
            decoded_count += 1
            
            # Save clean version
            clean_path = filepath.replace('.py', '_clean.py')
            
            # Add header to clean file
            header = f"""#!/usr/bin/env python3
# Decoded from {filepath}
# Original was obfuscated with exec(SEC(INFO(...)))

"""
            
            with open(clean_path, 'w') as f:
                f.write(header + decoded)
            
            print(f"Clean version saved to {clean_path}")
            
            # Also replace the original with clean version
            backup_path = filepath + '.obfuscated_backup'
            os.rename(filepath, backup_path)
            
            # Create new clean file without the header for the original location
            with open(filepath, 'w') as f:
                f.write(decoded)
            
            print(f"Original replaced with clean version (backup: {backup_path})")
            
        print("-" * 50)
    
    print(f"\nDecoded {decoded_count} files total")

if __name__ == "__main__":
    main()