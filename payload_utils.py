#!/usr/bin/env python3
"""
Payload Management Utilities for Stitch Web Interface
Handles detection, validation, and management of generated payloads
"""

import os
import sys
import glob
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

# Import Stitch modules safely
sys.path.insert(0, os.path.dirname(__file__))

# Platform detection functions (standalone)
def windows_client(system=sys.platform):
    return system.startswith('win')

def osx_client(system=sys.platform):
    return system.startswith('darwin')

def linux_client(system=sys.platform):
    return system.startswith('linux')

# Path configuration (with fallbacks)
try:
    from Application.Stitch_Vars.globals import payloads_path, configuration_path
except ImportError:
    # Fallback paths if imports fail
    base_path = os.path.dirname(__file__)
    payloads_path = os.path.join(base_path, 'Payloads')
    configuration_path = os.path.join(base_path, 'Configuration')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PayloadManager:
    """Manages payload generation, detection, and validation"""
    
    def __init__(self):
        self.payloads_path = payloads_path
        self.configuration_path = configuration_path
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        for path in [self.payloads_path, self.configuration_path]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                logger.info(f"Created directory: {path}")
    
    def get_latest_config_dir(self) -> Optional[str]:
        """
        Get the most recently created config directory from payloads
        Returns: Path to latest config directory or None if none exist
        """
        try:
            config_pattern = os.path.join(self.payloads_path, 'config*')
            config_dirs = glob.glob(config_pattern)
            
            if not config_dirs:
                logger.warning("No config directories found in payloads path")
                return None
            
            # Sort by creation time, return the most recent
            latest_dir = max(config_dirs, key=os.path.getctime)
            logger.info(f"Latest config directory: {latest_dir}")
            return latest_dir
            
        except Exception as e:
            logger.error(f"Error finding latest config directory: {e}")
            return None
    
    def get_all_config_dirs(self) -> List[str]:
        """Get all config directories sorted by creation time (newest first)"""
        try:
            config_pattern = os.path.join(self.payloads_path, 'config*')
            config_dirs = glob.glob(config_pattern)
            
            # Sort by creation time, newest first
            config_dirs.sort(key=os.path.getctime, reverse=True)
            return config_dirs
            
        except Exception as e:
            logger.error(f"Error getting config directories: {e}")
            return []
    
    def detect_payload_files(self, config_dir: str) -> Dict[str, List[str]]:
        """
        Detect all payload files in a config directory
        Returns: Dictionary with file types and their paths
        """
        if not os.path.exists(config_dir):
            logger.error(f"Config directory does not exist: {config_dir}")
            return {}
        
        payload_files = {
            'executables': [],
            'installers': [],
            'python_source': [],
            'config_files': []
        }
        
        try:
            # Windows executables
            exe_files = glob.glob(os.path.join(config_dir, "*.exe"))
            payload_files['executables'].extend(exe_files)
            
            # NSIS installers (Windows)
            nsis_dir = os.path.join(config_dir, "NSIS Installers")
            if os.path.exists(nsis_dir):
                nsis_files = glob.glob(os.path.join(nsis_dir, "*.exe"))
                payload_files['installers'].extend(nsis_files)
            
            # Linux/macOS binaries
            binaries_dir = os.path.join(config_dir, "Binaries")
            if os.path.exists(binaries_dir):
                # Get all files in Binaries directory (these are executables)
                for item in os.listdir(binaries_dir):
                    item_path = os.path.join(binaries_dir, item)
                    if os.path.isfile(item_path):
                        payload_files['executables'].append(item_path)
            
            # Makeself installers
            installers_dir = os.path.join(config_dir, "Installers")
            if os.path.exists(installers_dir):
                installer_files = glob.glob(os.path.join(installers_dir, "*.run"))
                payload_files['installers'].extend(installer_files)
            
            # macOS app bundles
            app_files = glob.glob(os.path.join(config_dir, "*.app"))
            payload_files['executables'].extend(app_files)
            
            # Python source files (fallback)
            py_files = glob.glob(os.path.join(config_dir, "*.py"))
            payload_files['python_source'].extend(py_files)
            
            # Configuration files
            config_files = glob.glob(os.path.join(config_dir, "*.log"))
            config_files.extend(glob.glob(os.path.join(config_dir, "*.ini")))
            payload_files['config_files'].extend(config_files)
            
            # Log findings
            total_files = sum(len(files) for files in payload_files.values())
            logger.info(f"Detected {total_files} payload files in {config_dir}")
            for file_type, files in payload_files.items():
                if files:
                    logger.info(f"  {file_type}: {len(files)} files")
            
            return payload_files
            
        except Exception as e:
            logger.error(f"Error detecting payload files: {e}")
            return payload_files
    
    def get_primary_payload(self, config_dir: str) -> Optional[Dict[str, str]]:
        """
        Get the primary payload file (executable preferred, fallback to Python)
        Returns: Dictionary with payload info or None
        """
        payload_files = self.detect_payload_files(config_dir)
        
        # Priority: executables > installers > python_source
        for file_type in ['executables', 'installers', 'python_source']:
            files = payload_files.get(file_type, [])
            if files:
                primary_file = files[0]  # Take the first one
                return {
                    'path': primary_file,
                    'type': file_type,
                    'filename': os.path.basename(primary_file),
                    'size': os.path.getsize(primary_file),
                    'created': datetime.fromtimestamp(os.path.getctime(primary_file)).isoformat()
                }
        
        logger.warning(f"No primary payload found in {config_dir}")
        return None
    
    def validate_payload(self, payload_path: str) -> Dict[str, Union[bool, str, int]]:
        """
        Validate a payload file
        Returns: Dictionary with validation results
        """
        validation = {
            'exists': False,
            'readable': False,
            'executable': False,
            'size_bytes': 0,
            'size_valid': False,
            'type': 'unknown',
            'errors': []
        }
        
        try:
            # Check existence
            if os.path.exists(payload_path):
                validation['exists'] = True
                
                # Check readability
                if os.access(payload_path, os.R_OK):
                    validation['readable'] = True
                else:
                    validation['errors'].append("File is not readable")
                
                # Check if executable
                if os.access(payload_path, os.X_OK):
                    validation['executable'] = True
                
                # Check size
                size = os.path.getsize(payload_path)
                validation['size_bytes'] = size
                
                # Determine type and validate size
                if payload_path.endswith('.py'):
                    validation['type'] = 'python_source'
                    validation['size_valid'] = size > 10  # Python source should be > 10 bytes (more lenient for tests)
                    
                    # Additional validation for Python source
                    try:
                        with open(payload_path, 'r') as f:
                            content = f.read()
                            if 'SEC(INFO(' in content:
                                validation['encrypted_payload'] = True
                            else:
                                validation['errors'].append("Python payload doesn't appear to be encrypted")
                    except Exception as e:
                        validation['errors'].append(f"Could not read Python file: {e}")
                
                elif payload_path.endswith('.exe'):
                    validation['type'] = 'windows_executable'
                    validation['size_valid'] = size > 10000  # Executable should be > 10KB
                
                elif payload_path.endswith('.app'):
                    validation['type'] = 'macos_app'
                    validation['size_valid'] = os.path.isdir(payload_path)  # .app is a directory
                
                elif payload_path.endswith('.run'):
                    validation['type'] = 'makeself_installer'
                    validation['size_valid'] = size > 1000  # Installer should be > 1KB
                
                else:
                    # Generic binary
                    validation['type'] = 'binary_executable'
                    validation['size_valid'] = size > 1000  # Binary should be > 1KB
                
                if not validation['size_valid']:
                    validation['errors'].append(f"File size ({size} bytes) seems too small for type {validation['type']}")
            
            else:
                validation['errors'].append("File does not exist")
            
            # Overall validation
            validation['valid'] = (validation['exists'] and 
                                 validation['readable'] and 
                                 validation['size_valid'] and 
                                 len(validation['errors']) == 0)
            
            return validation
            
        except Exception as e:
            validation['errors'].append(f"Validation error: {e}")
            return validation
    
    def get_build_capabilities(self) -> Dict[str, bool]:
        """
        Check what build tools are available on the system
        Returns: Dictionary of available build capabilities
        """
        capabilities = {
            'py2exe': False,
            'pyinstaller': False,
            'nsis': False,
            'makeself': False,
            'platform': sys.platform
        }
        
        try:
            # Check py2exe (Windows only)
            if windows_client():
                try:
                    import py2exe
                    capabilities['py2exe'] = True
                except ImportError:
                    pass
            
            # Check PyInstaller
            try:
                import subprocess
                result = subprocess.run(['pyinstaller', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                capabilities['pyinstaller'] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Check NSIS (Windows only)
            if windows_client():
                nsis_path = "C:\\Program Files (x86)\\NSIS\\makensis.exe"
                capabilities['nsis'] = os.path.exists(nsis_path)
            
            # Check Makeself (Linux/macOS)
            if not windows_client():
                from Application.Stitch_Vars.globals import tools_path
                makeself_path = os.path.join(tools_path, 'makeself', 'makeself.sh')
                capabilities['makeself'] = os.path.exists(makeself_path)
            
            logger.info(f"Build capabilities: {capabilities}")
            return capabilities
            
        except Exception as e:
            logger.error(f"Error checking build capabilities: {e}")
            return capabilities
    
    def cleanup_old_payloads(self, keep_count: int = 5) -> int:
        """
        Clean up old payload directories, keeping only the most recent ones
        Returns: Number of directories cleaned up
        """
        try:
            config_dirs = self.get_all_config_dirs()
            
            if len(config_dirs) <= keep_count:
                logger.info(f"Only {len(config_dirs)} config directories exist, no cleanup needed")
                return 0
            
            # Remove older directories
            dirs_to_remove = config_dirs[keep_count:]
            removed_count = 0
            
            for dir_path in dirs_to_remove:
                try:
                    import shutil
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed old payload directory: {dir_path}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove directory {dir_path}: {e}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error during payload cleanup: {e}")
            return 0

# Global instance
payload_manager = PayloadManager()

# Convenience functions for backward compatibility
def get_latest_config_dir() -> Optional[str]:
    """Get the latest config directory"""
    return payload_manager.get_latest_config_dir()

def detect_payload_files(config_dir: str) -> Dict[str, List[str]]:
    """Detect payload files in a directory"""
    return payload_manager.detect_payload_files(config_dir)

def get_primary_payload(config_dir: str) -> Optional[Dict[str, str]]:
    """Get the primary payload from a config directory"""
    return payload_manager.get_primary_payload(config_dir)

def validate_payload(payload_path: str) -> Dict[str, Union[bool, str, int]]:
    """Validate a payload file"""
    return payload_manager.validate_payload(payload_path)

def get_build_capabilities() -> Dict[str, bool]:
    """Get build capabilities"""
    return payload_manager.get_build_capabilities()

if __name__ == "__main__":
    # Test the module
    print("=== Payload Manager Test ===")
    
    # Test build capabilities
    print("\n1. Build Capabilities:")
    capabilities = get_build_capabilities()
    for tool, available in capabilities.items():
        status = "✅" if available else "❌"
        print(f"   {tool}: {status}")
    
    # Test directory detection
    print("\n2. Config Directories:")
    latest_dir = get_latest_config_dir()
    if latest_dir:
        print(f"   Latest: {latest_dir}")
        
        # Test payload detection
        print("\n3. Payload Files:")
        payload_files = detect_payload_files(latest_dir)
        for file_type, files in payload_files.items():
            if files:
                print(f"   {file_type}: {len(files)} files")
                for file_path in files[:3]:  # Show first 3
                    print(f"     - {os.path.basename(file_path)}")
        
        # Test primary payload
        print("\n4. Primary Payload:")
        primary = get_primary_payload(latest_dir)
        if primary:
            print(f"   File: {primary['filename']}")
            print(f"   Type: {primary['type']}")
            print(f"   Size: {primary['size']} bytes")
            
            # Test validation
            print("\n5. Payload Validation:")
            validation = validate_payload(primary['path'])
            print(f"   Valid: {'✅' if validation['valid'] else '❌'}")
            if validation['errors']:
                for error in validation['errors']:
                    print(f"   Error: {error}")
        else:
            print("   No primary payload found")
    else:
        print("   No config directories found")
    
    print("\n=== Test Complete ===")