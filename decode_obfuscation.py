#!/usr/bin/env python3
"""
Script to decode obfuscated Configuration files
"""

import base64
import zlib
import re
import os

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
            if 'subprocess' in original_code:
                print("WARNING: Contains subprocess calls")
            if 'eval' in original_code:
                print("WARNING: Contains eval calls")
            if 'exec' in original_code:
                print("WARNING: Contains exec calls")
            
            return original_code
            
        except Exception as e:
            print(f"ERROR decoding {filepath}: {e}")
            return None
    else:
        print(f"No obfuscated pattern found in {filepath}")
        return None

def main():
    """Decode all obfuscated files"""
    
    obfuscated_files = [
        'Configuration/st_encryption.py',
        'Configuration/st_protocol.py'
    ]
    
    for filepath in obfuscated_files:
        if os.path.exists(filepath):
            decoded = decode_obfuscated_file(filepath)
            
            if decoded:
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
                print("-" * 50)
        else:
            print(f"File not found: {filepath}")

if __name__ == "__main__":
    main()