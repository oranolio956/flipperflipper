#!/usr/bin/env python3
"""
Elite Shell Command - Execute commands using direct API calls
No subprocess, uses Windows API or direct system calls
"""

import ctypes
import os
import sys
import tempfile
import time
from ctypes import wintypes

def elite_shell(command, timeout=30):
    """
    Execute shell command using direct API calls:
    - Windows: Uses CreateProcess API directly
    - Unix: Uses fork/exec system calls
    - No subprocess module usage
    - Captures stdout/stderr
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
        if os.name == 'nt':
            return _windows_elite_shell(command, timeout)
        else:
            return _unix_elite_shell(command, timeout)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "exit_code": -1
        }

def _windows_elite_shell(command, timeout):
    """Windows implementation using CreateProcess API"""
    kernel32 = ctypes.windll.kernel32
    
    # Create temporary files for stdout/stderr
    stdout_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
    stderr_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
    
    try:
        # STARTUPINFO structure
        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR),
                ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD),
                ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD),
                ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD),
                ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
                ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE),
                ("hStdError", wintypes.HANDLE)
            ]
        
        # PROCESS_INFORMATION structure
        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("hProcess", wintypes.HANDLE),
                ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD)
            ]
        
        # Get handles to temp files
        stdout_handle = kernel32.CreateFileW(
            stdout_file.name,
            0x40000000,  # GENERIC_WRITE
            0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
            None,
            3,  # OPEN_EXISTING
            0,
            None
        )
        
        stderr_handle = kernel32.CreateFileW(
            stderr_file.name,
            0x40000000,  # GENERIC_WRITE
            0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
            None,
            3,  # OPEN_EXISTING
            0,
            None
        )
        
        # Setup STARTUPINFO
        startup_info = STARTUPINFO()
        startup_info.cb = ctypes.sizeof(STARTUPINFO)
        startup_info.dwFlags = 0x00000100  # STARTF_USESTDHANDLES
        startup_info.hStdOutput = stdout_handle
        startup_info.hStdError = stderr_handle
        startup_info.hStdInput = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        
        process_info = PROCESS_INFORMATION()
        
        # Prepare command line (use cmd.exe for shell features)
        cmd_line = f'cmd.exe /c "{command}"'
        
        # Create process
        success = kernel32.CreateProcessW(
            None,  # lpApplicationName
            cmd_line,  # lpCommandLine
            None,  # lpProcessAttributes
            None,  # lpThreadAttributes
            True,  # bInheritHandles
            0x08000000,  # CREATE_NO_WINDOW
            None,  # lpEnvironment
            None,  # lpCurrentDirectory
            ctypes.byref(startup_info),
            ctypes.byref(process_info)
        )
        
        if not success:
            error_code = kernel32.GetLastError()
            return {
                "success": False,
                "error": f"CreateProcess failed with error {error_code}",
                "stdout": "",
                "stderr": "",
                "exit_code": -1
            }
        
        # Wait for process to complete
        wait_result = kernel32.WaitForSingleObject(
            process_info.hProcess, 
            timeout * 1000  # Convert to milliseconds
        )
        
        # Get exit code
        exit_code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(process_info.hProcess, ctypes.byref(exit_code))
        
        # Close process handles
        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(process_info.hThread)
        kernel32.CloseHandle(stdout_handle)
        kernel32.CloseHandle(stderr_handle)
        
        # Read output files
        stdout_file.close()
        stderr_file.close()
        
        with open(stdout_file.name, 'rb') as f:
            stdout_data = f.read().decode('utf-8', errors='replace')
        
        with open(stderr_file.name, 'rb') as f:
            stderr_data = f.read().decode('utf-8', errors='replace')
        
        # Determine success based on wait result and exit code
        if wait_result == 0:  # WAIT_OBJECT_0 (success)
            success = True
        elif wait_result == 0x102:  # WAIT_TIMEOUT
            success = False
            stderr_data += f"\nCommand timed out after {timeout} seconds"
        else:
            success = False
            stderr_data += f"\nWait failed with result {wait_result}"
        
        return {
            "success": success and exit_code.value == 0,
            "stdout": stdout_data,
            "stderr": stderr_data,
            "exit_code": exit_code.value,
            "timed_out": wait_result == 0x102
        }
        
    finally:
        # Clean up temp files
        try:
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)
        except:
            pass

def _unix_elite_shell(command, timeout):
    """Unix implementation using fork/exec"""
    import signal
    import select
    
    # Create pipes for stdout and stderr
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()
    
    try:
        # Fork process
        pid = os.fork()
        
        if pid == 0:
            # Child process
            try:
                # Close read ends
                os.close(stdout_r)
                os.close(stderr_r)
                
                # Redirect stdout and stderr
                os.dup2(stdout_w, 1)
                os.dup2(stderr_w, 2)
                
                # Close write ends
                os.close(stdout_w)
                os.close(stderr_w)
                
                # Execute command
                os.execl('/bin/sh', 'sh', '-c', command)
                
            except Exception as e:
                os._exit(1)
        
        else:
            # Parent process
            # Close write ends
            os.close(stdout_w)
            os.close(stderr_w)
            
            # Set up timeout
            def timeout_handler(signum, frame):
                raise TimeoutError("Command timed out")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            stdout_data = b""
            stderr_data = b""
            
            try:
                # Read output with select
                while True:
                    ready, _, _ = select.select([stdout_r, stderr_r], [], [], 1)
                    
                    if not ready:
                        # Check if process is still running
                        try:
                            wpid, status = os.waitpid(pid, os.WNOHANG)
                            if wpid == pid:
                                # Process finished
                                break
                        except OSError:
                            break
                        continue
                    
                    for fd in ready:
                        data = os.read(fd, 4096)
                        if not data:
                            continue
                        
                        if fd == stdout_r:
                            stdout_data += data
                        elif fd == stderr_r:
                            stderr_data += data
                
                # Wait for process to finish
                _, status = os.waitpid(pid, 0)
                exit_code = os.WEXITSTATUS(status)
                timed_out = False
                
            except TimeoutError:
                # Kill the process
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(1)
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                except:
                    pass
                
                exit_code = -1
                timed_out = True
                stderr_data += f"\nCommand timed out after {timeout} seconds".encode()
                
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                os.close(stdout_r)
                os.close(stderr_r)
            
            return {
                "success": not timed_out and exit_code == 0,
                "stdout": stdout_data.decode('utf-8', errors='replace'),
                "stderr": stderr_data.decode('utf-8', errors='replace'),
                "exit_code": exit_code,
                "timed_out": timed_out
            }
    
    except Exception as e:
        # Clean up pipes
        for fd in [stdout_r, stderr_r, stdout_w, stderr_w]:
            try:
                os.close(fd)
            except:
                pass
        
        raise e

if __name__ == "__main__":
    # Test the elite shell command
    print("Testing Elite Shell Command...")
    
    # Test basic command
    print("\n1. Testing 'echo Hello World':")
    result = elite_shell("echo Hello World")
    
    if result["success"]:
        print(f"✓ Success (exit code: {result['exit_code']})")
        print(f"  stdout: {repr(result['stdout'])}")
    else:
        print(f"✗ Failed: {result.get('error', 'Unknown error')}")
        print(f"  stderr: {repr(result['stderr'])}")
    
    # Test command with error
    print("\n2. Testing command that fails:")
    result = elite_shell("nonexistent_command_12345")
    
    print(f"Exit code: {result['exit_code']}")
    print(f"stderr: {repr(result['stderr'][:100])}")
    
    # Test directory listing
    print("\n3. Testing directory listing:")
    if os.name == 'nt':
        result = elite_shell("dir")
    else:
        result = elite_shell("ls -la")
    
    if result["success"]:
        print(f"✓ Success")
        print(f"  Output length: {len(result['stdout'])} chars")
        print(f"  First line: {result['stdout'].split(chr(10))[0] if result['stdout'] else 'Empty'}")
    else:
        print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    
    # Test timeout
    print("\n4. Testing timeout (3 second limit):")
    if os.name == 'nt':
        result = elite_shell("ping -n 10 127.0.0.1", timeout=3)
    else:
        result = elite_shell("sleep 10", timeout=3)
    
    print(f"Timed out: {result.get('timed_out', False)}")
    print(f"Exit code: {result['exit_code']}")