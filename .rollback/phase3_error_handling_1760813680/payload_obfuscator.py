#!/usr/bin/env python3
"""
Payload obfuscation module
Compress and encode Python code for obfuscation
"""

import base64
import zlib
import random
import string

def obfuscate_code(source_code):
    """Obfuscate Python source code"""
    # Compress the code
    compressed = zlib.compress(source_code.encode())
    
    # Base64 encode
    encoded = base64.b64encode(compressed).decode()
    
    # Generate random variable names
    var1 = ''.join(random.choices(string.ascii_letters, k=8))
    var2 = ''.join(random.choices(string.ascii_letters, k=8))
    
    # Create obfuscated loader
    obfuscated = f"""
import base64
import zlib
exec(zlib.decompress(base64.b64decode('{encoded}')))
"""
    
    return obfuscated

def obfuscate_file(input_path, output_path):
    """Obfuscate a Python file"""
    with open(input_path, 'r') as f:
        source_code = f.read()
        
    obfuscated = obfuscate_code(source_code)
    
    with open(output_path, 'w') as f:
        f.write(obfuscated)
        
    return output_path
