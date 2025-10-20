#!/usr/bin/env python3
"""
Elite WiFi Keys Command - Extract WiFi passwords from system
Uses direct API calls and registry access
"""

import os
import sys
import ctypes
import subprocess
from ctypes import wintypes

def elite_wifikeys():
    """
    Extract WiFi passwords using multiple methods:
    - Windows: WLAN API and netsh
    - Linux: NetworkManager and wpa_supplicant
    - macOS: Keychain access
    """
    
    try:
        if os.name == 'nt':
            return _extract_wifi_windows()
        elif sys.platform == 'darwin':
            return _extract_wifi_macos()
        else:
            return _extract_wifi_linux()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "wifi_networks": []
        }

def _extract_wifi_windows():
    """Extract WiFi passwords on Windows using WLAN API"""
    wlanapi = None
    wifi_networks = []
    
    try:
        # Load wlanapi.dll
        wlanapi = ctypes.windll.LoadLibrary("wlanapi.dll")
        
        # Get WiFi networks using WLAN API
        api_networks = _get_wifi_wlan_api(wlanapi)
        wifi_networks.extend(api_networks)
        
    except Exception as e:
        print(f"WLAN API failed: {e}")
    
    # Fallback to netsh command
    try:
        netsh_networks = _get_wifi_netsh()
        
        # Merge results, avoiding duplicates
        existing_ssids = {net['ssid'] for net in wifi_networks}
        for net in netsh_networks:
            if net['ssid'] not in existing_ssids:
                wifi_networks.append(net)
                
    except Exception as e:
        print(f"Netsh fallback failed: {e}")
    
    return {
        "success": len(wifi_networks) > 0,
        "method": "wlan_api_and_netsh",
        "network_count": len(wifi_networks),
        "wifi_networks": wifi_networks
    }

def _get_wifi_wlan_api(wlanapi):
    """Get WiFi networks using Windows WLAN API"""
    networks = []
    
    try:
        # WLAN structures
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8)
            ]
        
        class WLAN_INTERFACE_INFO(ctypes.Structure):
            _fields_ = [
                ("InterfaceGuid", GUID),
                ("strInterfaceDescription", wintypes.WCHAR * 256),
                ("isState", ctypes.c_int)
            ]
        
        class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
            _fields_ = [
                ("dwNumberOfItems", wintypes.DWORD),
                ("dwIndex", wintypes.DWORD),
                ("InterfaceInfo", WLAN_INTERFACE_INFO * 1)
            ]
        
        # Open WLAN handle
        client_handle = wintypes.HANDLE()
        negotiated_version = wintypes.DWORD()
        
        result = wlanapi.WlanOpenHandle(
            2,  # Client version
            None,  # Reserved
            ctypes.byref(negotiated_version),
            ctypes.byref(client_handle)
        )
        
        if result != 0:
            return networks
        
        try:
            # Enumerate interfaces
            interface_list = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()
            
            result = wlanapi.WlanEnumInterfaces(
                client_handle,
                None,
                ctypes.byref(interface_list)
            )
            
            if result == 0 and interface_list:
                # Get profiles for each interface
                for i in range(interface_list.contents.dwNumberOfItems):
                    interface = interface_list.contents.InterfaceInfo[i]
                    
                    # Get profile list
                    profile_networks = _get_interface_profiles(
                        wlanapi, client_handle, interface.InterfaceGuid
                    )
                    networks.extend(profile_networks)
                
                # Free interface list
                wlanapi.WlanFreeMemory(interface_list)
        
        finally:
            # Close WLAN handle
            wlanapi.WlanCloseHandle(client_handle, None)
    
    except Exception as e:
        print(f"WLAN API enumeration failed: {e}")
    
    return networks

def _get_interface_profiles(wlanapi, client_handle, interface_guid):
    """Get WiFi profiles for a specific interface"""
    networks = []
    
    try:
        # WLAN profile structures
        class WLAN_PROFILE_INFO(ctypes.Structure):
            _fields_ = [
                ("strProfileName", wintypes.WCHAR * 256),
                ("dwFlags", wintypes.DWORD)
            ]
        
        class WLAN_PROFILE_INFO_LIST(ctypes.Structure):
            _fields_ = [
                ("dwNumberOfItems", wintypes.DWORD),
                ("dwIndex", wintypes.DWORD),
                ("ProfileInfo", WLAN_PROFILE_INFO * 1)
            ]
        
        # Get profile list
        profile_list = ctypes.POINTER(WLAN_PROFILE_INFO_LIST)()
        
        result = wlanapi.WlanGetProfileList(
            client_handle,
            ctypes.byref(interface_guid),
            None,
            ctypes.byref(profile_list)
        )
        
        if result == 0 and profile_list:
            try:
                # Get password for each profile
                for i in range(profile_list.contents.dwNumberOfItems):
                    profile = profile_list.contents.ProfileInfo[i]
                    profile_name = profile.strProfileName
                    
                    # Get profile XML
                    profile_xml = _get_profile_xml(
                        wlanapi, client_handle, interface_guid, profile_name
                    )
                    
                    if profile_xml:
                        # Extract password from XML
                        password = _extract_password_from_xml(profile_xml)
                        
                        networks.append({
                            'ssid': profile_name,
                            'password': password,
                            'security': _get_security_type_from_xml(profile_xml),
                            'source': 'wlan_api'
                        })
            
            finally:
                # Free profile list
                wlanapi.WlanFreeMemory(profile_list)
    
    except Exception as e:
        print(f"Profile enumeration failed: {e}")
    
    return networks

def _get_profile_xml(wlanapi, client_handle, interface_guid, profile_name):
    """Get WiFi profile XML"""
    try:
        profile_xml = ctypes.c_wchar_p()
        flags = wintypes.DWORD(0x00000001)  # WLAN_PROFILE_GET_PLAINTEXT_KEY
        
        result = wlanapi.WlanGetProfile(
            client_handle,
            ctypes.byref(interface_guid),
            profile_name,
            None,
            ctypes.byref(profile_xml),
            ctypes.byref(flags),
            None
        )
        
        if result == 0 and profile_xml:
            xml_content = profile_xml.value
            wlanapi.WlanFreeMemory(profile_xml)
            return xml_content
    
    except Exception as e:
        print(f"Profile XML extraction failed: {e}")
    
    return None

def _extract_password_from_xml(xml_content):
    """Extract password from WiFi profile XML"""
    try:
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(xml_content)
        
        # Look for keyMaterial element
        for elem in root.iter():
            if elem.tag.endswith('keyMaterial'):
                return elem.text
        
        # Look for passPhrase element
        for elem in root.iter():
            if elem.tag.endswith('passPhrase'):
                return elem.text
                
    except Exception as e:
        print(f"XML password extraction failed: {e}")
    
    return '[No Password]'

def _get_security_type_from_xml(xml_content):
    """Extract security type from WiFi profile XML"""
    try:
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(xml_content)
        
        # Look for authentication and encryption elements
        auth_type = 'Unknown'
        encryption = 'Unknown'
        
        for elem in root.iter():
            if elem.tag.endswith('authentication'):
                auth_type = elem.text
            elif elem.tag.endswith('encryption'):
                encryption = elem.text
        
        return f"{auth_type}/{encryption}"
        
    except:
        return 'Unknown'

def _get_wifi_netsh():
    """Get WiFi networks using netsh command (fallback)"""
    networks = []
    
    try:
        # Get list of profiles
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'profiles'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return networks
        
        # Parse profile names
        profile_names = []
        for line in result.stdout.split('\n'):
            if 'All User Profile' in line:
                # Extract profile name
                parts = line.split(':')
                if len(parts) > 1:
                    profile_name = parts[1].strip()
                    profile_names.append(profile_name)
        
        # Get password for each profile
        for profile_name in profile_names:
            try:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'profile', profile_name, 'key=clear'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    password = '[No Password]'
                    security = 'Unknown'
                    
                    # Parse output
                    for line in result.stdout.split('\n'):
                        if 'Key Content' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                password = parts[1].strip()
                        elif 'Authentication' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                security = parts[1].strip()
                    
                    networks.append({
                        'ssid': profile_name,
                        'password': password,
                        'security': security,
                        'source': 'netsh'
                    })
            
            except Exception as e:
                print(f"Failed to get password for {profile_name}: {e}")
                continue
    
    except Exception as e:
        print(f"Netsh command failed: {e}")
    
    return networks

def _extract_wifi_linux():
    """Extract WiFi passwords on Linux"""
    networks = []
    
    try:
        # Method 1: NetworkManager
        nm_networks = _get_wifi_networkmanager()
        networks.extend(nm_networks)
        
        # Method 2: wpa_supplicant
        wpa_networks = _get_wifi_wpa_supplicant()
        
        # Merge results
        existing_ssids = {net['ssid'] for net in networks}
        for net in wpa_networks:
            if net['ssid'] not in existing_ssids:
                networks.append(net)
    
    except Exception as e:
        print(f"Linux WiFi extraction failed: {e}")
    
    return {
        "success": len(networks) > 0,
        "method": "networkmanager_and_wpa",
        "network_count": len(networks),
        "wifi_networks": networks
    }

def _get_wifi_networkmanager():
    """Get WiFi networks from NetworkManager"""
    networks = []
    
    try:
        # Check if NetworkManager is available
        nm_dir = '/etc/NetworkManager/system-connections'
        if not os.path.exists(nm_dir):
            return networks
        
        # Read connection files
        for filename in os.listdir(nm_dir):
            filepath = os.path.join(nm_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Parse connection file
                ssid = None
                password = None
                security = None
                
                for line in content.split('\n'):
                    line = line.strip()
                    
                    if line.startswith('ssid='):
                        ssid = line.split('=', 1)[1]
                    elif line.startswith('psk='):
                        password = line.split('=', 1)[1]
                    elif line.startswith('key-mgmt='):
                        security = line.split('=', 1)[1]
                
                if ssid:
                    networks.append({
                        'ssid': ssid,
                        'password': password or '[No Password]',
                        'security': security or 'Unknown',
                        'source': 'networkmanager'
                    })
            
            except Exception as e:
                print(f"Failed to read {filepath}: {e}")
                continue
    
    except Exception as e:
        print(f"NetworkManager extraction failed: {e}")
    
    return networks

def _get_wifi_wpa_supplicant():
    """Get WiFi networks from wpa_supplicant"""
    networks = []
    
    try:
        # Common wpa_supplicant config locations
        config_paths = [
            '/etc/wpa_supplicant/wpa_supplicant.conf',
            '/etc/wpa_supplicant.conf'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    # Parse wpa_supplicant config
                    current_network = {}
                    in_network = False
                    
                    for line in content.split('\n'):
                        line = line.strip()
                        
                        if line.startswith('network={'):
                            in_network = True
                            current_network = {}
                        elif line == '}' and in_network:
                            in_network = False
                            if 'ssid' in current_network:
                                networks.append({
                                    'ssid': current_network.get('ssid', 'Unknown'),
                                    'password': current_network.get('psk', '[No Password]'),
                                    'security': current_network.get('key_mgmt', 'WPA-PSK'),
                                    'source': 'wpa_supplicant'
                                })
                        elif in_network and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"')
                            current_network[key] = value
                
                except Exception as e:
                    print(f"Failed to read {config_path}: {e}")
                    continue
    
    except Exception as e:
        print(f"wpa_supplicant extraction failed: {e}")
    
    return networks

def _extract_wifi_macos():
    """Extract WiFi passwords on macOS"""
    networks = []
    
    try:
        # Use security command to access keychain
        result = subprocess.run(
            ['security', 'dump-keychain'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse keychain dump for WiFi passwords
            current_item = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if line.startswith('keychain:'):
                    if current_item and 'ssid' in current_item:
                        networks.append(current_item)
                    current_item = {}
                elif 'AirPort network password' in line:
                    current_item['type'] = 'wifi'
                elif line.startswith('"acct"'):
                    # Extract SSID
                    parts = line.split('=')
                    if len(parts) > 1:
                        ssid = parts[1].strip().strip('"')
                        current_item['ssid'] = ssid
                elif line.startswith('password:'):
                    # Extract password
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        password = parts[1].strip().strip('"')
                        current_item['password'] = password
            
            # Add last item
            if current_item and 'ssid' in current_item:
                networks.append(current_item)
    
    except Exception as e:
        print(f"macOS WiFi extraction failed: {e}")
    
    # Format results
    formatted_networks = []
    for net in networks:
        if net.get('type') == 'wifi':
            formatted_networks.append({
                'ssid': net.get('ssid', 'Unknown'),
                'password': net.get('password', '[Access Denied]'),
                'security': 'WPA/WPA2',
                'source': 'keychain'
            })
    
    return {
        "success": len(formatted_networks) > 0,
        "method": "keychain_access",
        "network_count": len(formatted_networks),
        "wifi_networks": formatted_networks
    }

if __name__ == "__main__":
    # Test the elite wifikeys command
    print("Testing Elite WiFi Keys Command...")
    
    result = elite_wifikeys()
    
    if result["success"]:
        print(f"✓ WiFi extraction successful!")
        print(f"  Method: {result['method']}")
        print(f"  Networks found: {result['network_count']}")
        
        if result['wifi_networks']:
            print("\nWiFi Networks:")
            for i, network in enumerate(result['wifi_networks'][:5]):  # Show first 5
                print(f"  {i+1}. SSID: {network['ssid']}")
                print(f"     Password: {network['password']}")
                print(f"     Security: {network['security']}")
                print(f"     Source: {network['source']}")
                print()
        else:
            print("  No WiFi networks found")
    else:
        print(f"✗ WiFi extraction failed: {result['error']}")
        
        if os.name == 'nt':
            print("  Tip: Run as Administrator for full access")
        else:
            print("  Tip: Run as root or check file permissions")