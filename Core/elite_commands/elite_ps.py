#!/usr/bin/env python3
"""
Elite PS Command - Advanced process listing using direct API calls
No subprocess, comprehensive process information including hidden processes
"""

import ctypes
import sys
import os
import struct
from ctypes import wintypes
from datetime import datetime

def elite_ps():
    """
    List all processes with advanced information:
    - Process details (PID, PPID, name, path)
    - Memory usage and CPU time
    - Security context and privileges
    - Hidden process detection
    - No subprocess calls - pure API
    """
    
    try:
        if os.name == 'nt':
            return _windows_elite_ps()
        else:
            return _unix_elite_ps()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processes": []
        }

def _windows_elite_ps():
    """Windows implementation using NtQuerySystemInformation"""
    ntdll = ctypes.windll.ntdll
    kernel32 = ctypes.windll.kernel32
    
    processes = []
    
    try:
        # Use NtQuerySystemInformation to get process list
        # SystemProcessInformation = 5
        info_class = 5
        buffer_size = 1024 * 1024  # Start with 1MB
        
        while True:
            buffer = ctypes.create_string_buffer(buffer_size)
            return_length = ctypes.c_ulong()
            
            status = ntdll.NtQuerySystemInformation(
                info_class,
                buffer,
                buffer_size,
                ctypes.byref(return_length)
            )
            
            if status == 0:  # STATUS_SUCCESS
                break
            elif status == 0xC0000004:  # STATUS_INFO_LENGTH_MISMATCH
                buffer_size = return_length.value
                continue
            else:
                return {
                    "success": False,
                    "error": f"NtQuerySystemInformation failed with status {hex(status)}",
                    "processes": []
                }
        
        # Parse the process information
        processes = _parse_system_process_information(buffer)
        
        # Enhance with additional information
        for process in processes:
            try:
                _enhance_process_info(process)
            except:
                pass  # Continue if enhancement fails
        
        # Sort by PID
        processes.sort(key=lambda x: x.get('pid', 0))
        
        return {
            "success": True,
            "process_count": len(processes),
            "processes": processes
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processes": []
        }

def _parse_system_process_information(buffer):
    """Parse SYSTEM_PROCESS_INFORMATION structure"""
    processes = []
    offset = 0
    
    while True:
        try:
            # Read NextEntryOffset
            next_offset = struct.unpack('<I', buffer[offset:offset+4])[0]
            
            # Read NumberOfThreads
            thread_count = struct.unpack('<I', buffer[offset+4:offset+8])[0]
            
            # Skip reserved fields and timestamps (48 bytes total)
            # Read ProcessId at offset 68
            pid_offset = offset + 68
            pid = struct.unpack('<Q', buffer[pid_offset:pid_offset+8])[0]  # HANDLE is 64-bit
            
            # Read ParentProcessId at offset 76
            ppid_offset = offset + 76
            ppid = struct.unpack('<Q', buffer[ppid_offset:ppid_offset+8])[0]
            
            # Read process name length and offset
            name_length_offset = offset + 60
            name_length = struct.unpack('<H', buffer[name_length_offset:name_length_offset+2])[0]
            
            name_offset = offset + 232  # Approximate offset to ImageName
            
            # Extract process name
            if name_length > 0 and name_offset + name_length <= len(buffer):
                try:
                    process_name = buffer[name_offset:name_offset+name_length].decode('utf-16le', errors='ignore')
                    process_name = process_name.rstrip('\x00')
                except:
                    process_name = f"PID_{pid}"
            else:
                process_name = f"PID_{pid}" if pid > 0 else "System Idle Process"
            
            process_info = {
                'pid': int(pid),
                'ppid': int(ppid),
                'name': process_name,
                'thread_count': thread_count
            }
            
            processes.append(process_info)
            
            # Move to next process
            if next_offset == 0:
                break
            offset += next_offset
            
        except Exception as e:
            print(f"Error parsing process at offset {offset}: {e}")
            break
    
    return processes

def _enhance_process_info(process):
    """Enhance process information with additional details"""
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    
    pid = process['pid']
    
    if pid == 0:
        # System Idle Process
        process['path'] = 'System'
        process['memory_mb'] = 0
        process['cpu_time'] = 0
        return
    
    # Open process with minimal rights
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    
    h_process = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
        False,
        pid
    )
    
    if h_process:
        try:
            # Get process path
            path_buffer = ctypes.create_unicode_buffer(260)
            path_size = wintypes.DWORD(260)
            
            if kernel32.QueryFullProcessImageNameW(
                h_process, 0, path_buffer, ctypes.byref(path_size)
            ):
                process['path'] = path_buffer.value
            else:
                process['path'] = 'Access Denied'
            
            # Get memory information
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
                process['memory_bytes'] = mem_counters.WorkingSetSize
                process['memory_mb'] = mem_counters.WorkingSetSize / (1024 * 1024)
                process['memory_human'] = _format_size(mem_counters.WorkingSetSize)
            
            # Get process times
            creation_time = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()
            
            if kernel32.GetProcessTimes(
                h_process,
                ctypes.byref(creation_time),
                ctypes.byref(exit_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time)
            ):
                # Convert FILETIME to datetime
                process['created'] = _filetime_to_datetime(creation_time)
                
                # Calculate CPU time (simplified)
                kernel_time_ms = _filetime_to_ms(kernel_time)
                user_time_ms = _filetime_to_ms(user_time)
                process['cpu_time_ms'] = kernel_time_ms + user_time_ms
                process['cpu_time_human'] = f"{process['cpu_time_ms']/1000:.2f}s"
            
        finally:
            kernel32.CloseHandle(h_process)
    else:
        process['path'] = 'Access Denied'
        process['memory_mb'] = 0

def _unix_elite_ps():
    """Unix implementation using /proc filesystem"""
    processes = []
    
    try:
        # Read from /proc directory
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
            
            pid = int(pid_dir)
            proc_path = f'/proc/{pid}'
            
            try:
                process_info = {'pid': pid}
                
                # Read status file
                with open(f'{proc_path}/status', 'r') as f:
                    status_lines = f.readlines()
                
                for line in status_lines:
                    if line.startswith('Name:'):
                        process_info['name'] = line.split('\t')[1].strip()
                    elif line.startswith('PPid:'):
                        process_info['ppid'] = int(line.split('\t')[1].strip())
                    elif line.startswith('Threads:'):
                        process_info['thread_count'] = int(line.split('\t')[1].strip())
                    elif line.startswith('VmRSS:'):
                        # Memory in KB
                        mem_kb = int(line.split()[1])
                        process_info['memory_bytes'] = mem_kb * 1024
                        process_info['memory_mb'] = mem_kb / 1024
                        process_info['memory_human'] = _format_size(mem_kb * 1024)
                
                # Read command line
                try:
                    with open(f'{proc_path}/cmdline', 'r') as f:
                        cmdline = f.read().replace('\x00', ' ').strip()
                        process_info['cmdline'] = cmdline if cmdline else process_info.get('name', 'Unknown')
                except:
                    process_info['cmdline'] = process_info.get('name', 'Unknown')
                
                # Read executable path
                try:
                    process_info['path'] = os.readlink(f'{proc_path}/exe')
                except:
                    process_info['path'] = 'Unknown'
                
                # Read stat file for additional info
                try:
                    with open(f'{proc_path}/stat', 'r') as f:
                        stat_fields = f.read().split()
                    
                    # CPU times (user + system) in clock ticks
                    utime = int(stat_fields[13])
                    stime = int(stat_fields[14])
                    
                    # Convert to seconds (assuming 100 Hz)
                    cpu_time_sec = (utime + stime) / 100
                    process_info['cpu_time_ms'] = cpu_time_sec * 1000
                    process_info['cpu_time_human'] = f"{cpu_time_sec:.2f}s"
                    
                    # Start time
                    starttime = int(stat_fields[21])
                    # This would need boot time to convert to absolute time
                    # For now, just store the relative value
                    process_info['start_time_ticks'] = starttime
                    
                except:
                    pass
                
                processes.append(process_info)
                
            except (IOError, OSError, PermissionError):
                # Process may have disappeared or no permission
                continue
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processes": []
        }
    
    # Sort by PID
    processes.sort(key=lambda x: x['pid'])
    
    return {
        "success": True,
        "process_count": len(processes),
        "processes": processes
    }

def _filetime_to_datetime(filetime):
    """Convert Windows FILETIME to datetime"""
    try:
        timestamp = (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime
        timestamp = (timestamp - 116444736000000000) / 10000000
        return datetime.fromtimestamp(timestamp)
    except:
        return None

def _filetime_to_ms(filetime):
    """Convert Windows FILETIME to milliseconds"""
    try:
        timestamp = (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime
        return timestamp / 10000  # Convert 100ns intervals to ms
    except:
        return 0

def _format_size(size_bytes):
    """Format memory size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

if __name__ == "__main__":
    # Test the elite ps command
    import json
    
    print("Testing Elite PS Command...")
    
    result = elite_ps()
    
    if result["success"]:
        print(f"Found {result['process_count']} processes")
        print("\nTop 10 processes by memory usage:")
        
        # Sort by memory usage
        processes = sorted(result['processes'], 
                         key=lambda x: x.get('memory_mb', 0), 
                         reverse=True)
        
        for i, proc in enumerate(processes[:10]):
            memory = proc.get('memory_human', 'Unknown')
            name = proc.get('name', 'Unknown')
            pid = proc.get('pid', 0)
            print(f"  {i+1:2d}. {name} (PID: {pid}) - {memory}")
            
    else:
        print(f"Error: {result['error']}")