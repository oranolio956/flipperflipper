#!/usr/bin/env python3
"""
Elite Kill Command - Terminate processes using direct API calls
Multiple termination methods, no subprocess
"""

import ctypes
import os
import sys
import time
from ctypes import wintypes

def elite_kill(pid, force=False):
    """
    Terminate process using direct API calls:
    - Windows: Uses TerminateProcess API
    - Unix: Uses kill system call
    - Multiple termination methods
    - Force option for stubborn processes
    """
    
    if not isinstance(pid, int) or pid <= 0:
        return {
            "success": False,
            "error": f"Invalid PID: {pid}",
            "pid": pid
        }
    
    try:
        if os.name == 'nt':
            return _windows_elite_kill(pid, force)
        else:
            return _unix_elite_kill(pid, force)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "pid": pid
        }

def _windows_elite_kill(pid, force):
    """Windows implementation using TerminateProcess API"""
    kernel32 = ctypes.windll.kernel32
    
    # Check if process exists first
    if not _process_exists_windows(pid):
        return {
            "success": False,
            "error": f"Process {pid} not found",
            "pid": pid
        }
    
    # Get process information
    process_info = _get_process_info_windows(pid)
    
    # Try graceful termination first (unless force is specified)
    if not force:
        if _graceful_terminate_windows(pid):
            # Wait a bit to see if it terminates
            time.sleep(2)
            if not _process_exists_windows(pid):
                return {
                    "success": True,
                    "method": "graceful",
                    "pid": pid,
                    "process_info": process_info
                }
    
    # Force termination
    PROCESS_TERMINATE = 0x0001
    
    h_process = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    
    if not h_process:
        error_code = kernel32.GetLastError()
        return {
            "success": False,
            "error": f"OpenProcess failed with error {error_code}",
            "pid": pid,
            "process_info": process_info
        }
    
    try:
        # Terminate the process
        success = kernel32.TerminateProcess(h_process, 1)
        
        if success:
            # Wait for process to actually terminate
            wait_result = kernel32.WaitForSingleObject(h_process, 5000)  # 5 second timeout
            
            return {
                "success": True,
                "method": "force" if force else "terminate",
                "pid": pid,
                "process_info": process_info,
                "wait_result": wait_result
            }
        else:
            error_code = kernel32.GetLastError()
            return {
                "success": False,
                "error": f"TerminateProcess failed with error {error_code}",
                "pid": pid,
                "process_info": process_info
            }
    
    finally:
        kernel32.CloseHandle(h_process)

def _unix_elite_kill(pid, force):
    """Unix implementation using kill system call"""
    import signal
    
    # Check if process exists
    if not _process_exists_unix(pid):
        return {
            "success": False,
            "error": f"Process {pid} not found",
            "pid": pid
        }
    
    # Get process information
    process_info = _get_process_info_unix(pid)
    
    try:
        if force:
            # Send SIGKILL (cannot be caught or ignored)
            os.kill(pid, signal.SIGKILL)
            method = "SIGKILL"
        else:
            # Try SIGTERM first (graceful)
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit to see if it terminates
            time.sleep(2)
            if not _process_exists_unix(pid):
                return {
                    "success": True,
                    "method": "SIGTERM",
                    "pid": pid,
                    "process_info": process_info
                }
            
            # If still running, use SIGKILL
            os.kill(pid, signal.SIGKILL)
            method = "SIGTERM->SIGKILL"
        
        # Wait a moment and check if process is gone
        time.sleep(1)
        still_exists = _process_exists_unix(pid)
        
        return {
            "success": not still_exists,
            "method": method,
            "pid": pid,
            "process_info": process_info,
            "still_exists": still_exists
        }
        
    except OSError as e:
        if e.errno == 3:  # ESRCH - No such process
            return {
                "success": True,
                "method": "already_dead",
                "pid": pid,
                "process_info": process_info
            }
        elif e.errno == 1:  # EPERM - Operation not permitted
            return {
                "success": False,
                "error": f"Permission denied to kill process {pid}",
                "pid": pid,
                "process_info": process_info
            }
        else:
            return {
                "success": False,
                "error": f"Kill failed: {e}",
                "pid": pid,
                "process_info": process_info
            }

def _process_exists_windows(pid):
    """Check if process exists on Windows"""
    kernel32 = ctypes.windll.kernel32
    
    PROCESS_QUERY_INFORMATION = 0x0400
    h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    
    if h_process:
        kernel32.CloseHandle(h_process)
        return True
    
    return False

def _process_exists_unix(pid):
    """Check if process exists on Unix"""
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks existence
        return True
    except OSError:
        return False

def _get_process_info_windows(pid):
    """Get basic process information on Windows"""
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    
    info = {"pid": pid}
    
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    
    h_process = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
    )
    
    if h_process:
        try:
            # Get process name
            path_buffer = ctypes.create_unicode_buffer(260)
            path_size = wintypes.DWORD(260)
            
            if kernel32.QueryFullProcessImageNameW(
                h_process, 0, path_buffer, ctypes.byref(path_size)
            ):
                info["path"] = path_buffer.value
                info["name"] = os.path.basename(path_buffer.value)
            
            # Get memory usage
            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)
                ]
            
            mem_counters = PROCESS_MEMORY_COUNTERS()
            mem_counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            
            if psapi.GetProcessMemoryInfo(
                h_process, ctypes.byref(mem_counters), mem_counters.cb
            ):
                info["memory_mb"] = mem_counters.WorkingSetSize / (1024 * 1024)
        
        finally:
            kernel32.CloseHandle(h_process)
    
    return info

def _get_process_info_unix(pid):
    """Get basic process information on Unix"""
    info = {"pid": pid}
    
    try:
        # Read from /proc/pid/status
        with open(f'/proc/{pid}/status', 'r') as f:
            for line in f:
                if line.startswith('Name:'):
                    info["name"] = line.split('\t')[1].strip()
                elif line.startswith('VmRSS:'):
                    mem_kb = int(line.split()[1])
                    info["memory_mb"] = mem_kb / 1024
        
        # Read command line
        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmdline = f.read().replace('\x00', ' ').strip()
                info["cmdline"] = cmdline if cmdline else info.get("name", "Unknown")
        except:
            pass
        
        # Read executable path
        try:
            info["path"] = os.readlink(f'/proc/{pid}/exe')
        except:
            pass
    
    except (IOError, OSError):
        pass
    
    return info

def _graceful_terminate_windows(pid):
    """Try to gracefully terminate Windows process"""
    user32 = ctypes.windll.user32
    
    # Find main window of the process
    def enum_windows_callback(hwnd, pid_to_find):
        window_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        
        if window_pid.value == pid_to_find:
            # Send WM_CLOSE message
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            return False  # Stop enumeration
        
        return True
    
    # Define callback type
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    callback = EnumWindowsProc(lambda hwnd, lparam: enum_windows_callback(hwnd, lparam))
    
    try:
        user32.EnumWindows(callback, pid)
        return True
    except:
        return False

def elite_kill_by_name(process_name, force=False):
    """Kill all processes with given name"""
    if os.name == 'nt':
        processes = _find_processes_by_name_windows(process_name)
    else:
        processes = _find_processes_by_name_unix(process_name)
    
    results = []
    
    for pid in processes:
        result = elite_kill(pid, force)
        results.append(result)
    
    successful_kills = len([r for r in results if r["success"]])
    
    return {
        "success": successful_kills > 0,
        "process_name": process_name,
        "found_processes": len(processes),
        "successful_kills": successful_kills,
        "results": results
    }

def _find_processes_by_name_windows(process_name):
    """Find processes by name on Windows"""
    # This would use the same NtQuerySystemInformation as in elite_ps
    # For now, return empty list
    return []

def _find_processes_by_name_unix(process_name):
    """Find processes by name on Unix"""
    pids = []
    
    try:
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
            
            try:
                with open(f'/proc/{pid_dir}/comm', 'r') as f:
                    name = f.read().strip()
                    if name == process_name:
                        pids.append(int(pid_dir))
            except:
                continue
    except:
        pass
    
    return pids

if __name__ == "__main__":
    # Test the elite kill command
    import subprocess
    
    print("Testing Elite Kill Command...")
    
    # Start a test process
    if os.name == 'nt':
        # Start a ping process that will run for a while
        test_proc = subprocess.Popen(['ping', '-n', '100', '127.0.0.1'])
    else:
        # Start a sleep process
        test_proc = subprocess.Popen(['sleep', '60'])
    
    test_pid = test_proc.pid
    print(f"Started test process with PID: {test_pid}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test killing the process
    print(f"\nAttempting to kill PID {test_pid}...")
    result = elite_kill(test_pid)
    
    if result["success"]:
        print(f"✓ Successfully killed process")
        print(f"  Method: {result['method']}")
        if 'process_info' in result:
            info = result['process_info']
            print(f"  Process: {info.get('name', 'Unknown')}")
            if 'memory_mb' in info:
                print(f"  Memory: {info['memory_mb']:.1f} MB")
    else:
        print(f"✗ Failed to kill process: {result['error']}")
    
    # Test killing non-existent process
    print(f"\nTesting kill of non-existent PID 99999...")
    result = elite_kill(99999)
    
    if not result["success"]:
        print(f"✓ Correctly failed: {result['error']}")
    else:
        print(f"✗ Unexpectedly succeeded")
    
    # Clean up
    try:
        test_proc.terminate()
        test_proc.wait(timeout=5)
    except:
        try:
            test_proc.kill()
        except:
            pass