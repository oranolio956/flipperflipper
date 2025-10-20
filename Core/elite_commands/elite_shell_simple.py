#!/usr/bin/env python3
"""
Elite Shell Command - Simplified version using os.popen for now
Will be replaced with full API version later
"""

import os
import sys
import time

def elite_shell(command, timeout=30):
    """
    Execute shell command - simplified version
    """
    
    if not command or not command.strip():
        return {
            "success": False,
            "error": "Empty command provided",
            "stdout": "",
            "stderr": "",
            "exit_code": -1
        }
    
    try:
        # Use os.popen for now (will replace with API calls later)
        with os.popen(command + ' 2>&1') as proc:
            output = proc.read()
            exit_code = proc.close()
            
            if exit_code is None:
                exit_code = 0
        
        return {
            "success": exit_code == 0,
            "stdout": output,
            "stderr": "",
            "exit_code": exit_code,
            "command": command
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "exit_code": -1
        }

# Alias for the main function
def elite_shell_simple(command, timeout=30):
    return elite_shell(command, timeout)

if __name__ == "__main__":
    # Test the simplified shell command
    print("Testing Elite Shell Command (Simplified)...")
    
    # Test basic command
    result = elite_shell("echo 'Hello World'")
    print(f"Echo test: {result['success']}")
    print(f"Output: {repr(result['stdout'].strip())}")
    
    # Test directory listing  
    result = elite_shell("ls -la" if os.name != 'nt' else "dir")
    print(f"Directory listing: {result['success']}")
    print(f"Output length: {len(result['stdout'])} chars")