#!/usr/bin/env python3
"""
Build Tools Manager for Stitch RAT
Handles detection, installation, and management of payload compilation tools
"""

import os
import sys
import platform
import subprocess
import shutil
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile
import json

class BuildToolsManager:
    """Manages payload compilation build tools"""
    
    def __init__(self):
        self.platform_system = platform.system().lower()
        self.architecture = platform.architecture()[0]
        self.python_version = platform.python_version()
        
        # Tool paths and configurations
        self.tools_config = {
            'pyinstaller': {
                'command': 'pyinstaller',
                'install_cmd': [sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
                'test_cmd': ['pyinstaller', '--version'],
                'platforms': ['windows', 'linux', 'darwin'],
                'required_for': ['windows', 'linux', 'macos']
            },
            'py2exe': {
                'module': 'py2exe',
                'install_cmd': [sys.executable, '-m', 'pip', 'install', 'py2exe'],
                'platforms': ['windows'],
                'required_for': ['windows']
            },
            'nsis': {
                'windows_path': r"C:\Program Files (x86)\NSIS\makensis.exe",
                'alt_paths': [
                    r"C:\Program Files\NSIS\makensis.exe",
                    r"C:\NSIS\makensis.exe"
                ],
                'platforms': ['windows'],
                'required_for': ['windows_installers']
            },
            'makeself': {
                'script_path': 'Tools/makeself/makeself.sh',
                'platforms': ['linux', 'darwin'],
                'required_for': ['linux_installers', 'macos_installers']
            }
        }
    
    def detect_all_tools(self) -> Dict[str, Dict]:
        """Detect all available build tools and their status"""
        results = {}
        
        for tool_name, config in self.tools_config.items():
            results[tool_name] = self._detect_single_tool(tool_name, config)
        
        return results
    
    def _detect_single_tool(self, tool_name: str, config: Dict) -> Dict:
        """Detect a single build tool"""
        result = {
            'name': tool_name,
            'available': False,
            'version': None,
            'path': None,
            'platform_supported': self.platform_system in config.get('platforms', []),
            'install_method': 'automatic' if 'install_cmd' in config else 'manual',
            'error': None
        }
        
        try:
            if tool_name == 'pyinstaller':
                result.update(self._detect_pyinstaller())
            elif tool_name == 'py2exe':
                result.update(self._detect_py2exe())
            elif tool_name == 'nsis':
                result.update(self._detect_nsis())
            elif tool_name == 'makeself':
                result.update(self._detect_makeself())
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _detect_pyinstaller(self) -> Dict:
        """Detect PyInstaller installation"""
        result = {'available': False}
        
        # Check if pyinstaller command is available
        pyinstaller_path = shutil.which('pyinstaller')
        if pyinstaller_path:
            try:
                # Get version
                version_result = subprocess.run(
                    ['pyinstaller', '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if version_result.returncode == 0:
                    result.update({
                        'available': True,
                        'version': version_result.stdout.strip(),
                        'path': pyinstaller_path
                    })
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                result['error'] = f"PyInstaller found but not working: {e}"
        
        return result
    
    def _detect_py2exe(self) -> Dict:
        """Detect py2exe installation (Windows only)"""
        result = {'available': False}
        
        if self.platform_system != 'windows':
            return result
        
        try:
            # Try to import py2exe
            spec = importlib.util.find_spec('py2exe')
            if spec is not None:
                import py2exe
                result.update({
                    'available': True,
                    'version': getattr(py2exe, '__version__', 'unknown'),
                    'path': py2exe.__file__
                })
        except ImportError as e:
            result['error'] = f"py2exe not installed: {e}"
        except Exception as e:
            result['error'] = f"py2exe detection error: {e}"
        
        return result
    
    def _detect_nsis(self) -> Dict:
        """Detect NSIS installation (Windows only)"""
        result = {'available': False}
        
        if self.platform_system != 'windows':
            return result
        
        # Check standard installation paths
        paths_to_check = [self.tools_config['nsis']['windows_path']] + \
                        self.tools_config['nsis']['alt_paths']
        
        for nsis_path in paths_to_check:
            if os.path.exists(nsis_path):
                try:
                    # Test NSIS by getting version
                    version_result = subprocess.run(
                        [nsis_path, '/VERSION'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    result.update({
                        'available': True,
                        'version': version_result.stdout.strip() if version_result.returncode == 0 else 'unknown',
                        'path': nsis_path
                    })
                    break
                except Exception as e:
                    result['error'] = f"NSIS found but not working: {e}"
        
        return result
    
    def _detect_makeself(self) -> Dict:
        """Detect Makeself installation (Linux/macOS)"""
        result = {'available': False}
        
        if self.platform_system == 'windows':
            return result
        
        # Check if makeself script exists in Tools directory
        makeself_path = Path(self.tools_config['makeself']['script_path'])
        if makeself_path.exists():
            result.update({
                'available': True,
                'version': 'bundled',
                'path': str(makeself_path.absolute())
            })
        else:
            # Check if makeself is available system-wide
            makeself_system = shutil.which('makeself')
            if makeself_system:
                result.update({
                    'available': True,
                    'version': 'system',
                    'path': makeself_system
                })
        
        return result
    
    def install_tool(self, tool_name: str) -> Tuple[bool, str]:
        """Install a specific build tool"""
        if tool_name not in self.tools_config:
            return False, f"Unknown tool: {tool_name}"
        
        config = self.tools_config[tool_name]
        
        # Check if tool supports automatic installation
        if 'install_cmd' not in config:
            return False, f"{tool_name} requires manual installation"
        
        # Check platform support
        if self.platform_system not in config.get('platforms', []):
            return False, f"{tool_name} not supported on {self.platform_system}"
        
        try:
            # Run installation command
            install_result = subprocess.run(
                config['install_cmd'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if install_result.returncode == 0:
                # Verify installation
                detection_result = self._detect_single_tool(tool_name, config)
                if detection_result['available']:
                    return True, f"{tool_name} installed successfully"
                else:
                    return False, f"{tool_name} installation completed but tool not detected"
            else:
                return False, f"Installation failed: {install_result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, f"{tool_name} installation timed out"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def install_missing_tools(self, required_tools: List[str] = None) -> Dict[str, Tuple[bool, str]]:
        """Install all missing tools that can be automatically installed"""
        if required_tools is None:
            required_tools = ['pyinstaller']  # Default essential tool
        
        results = {}
        all_tools = self.detect_all_tools()
        
        for tool_name in required_tools:
            if tool_name in all_tools:
                tool_info = all_tools[tool_name]
                if not tool_info['available'] and tool_info['platform_supported']:
                    if tool_info['install_method'] == 'automatic':
                        success, message = self.install_tool(tool_name)
                        results[tool_name] = (success, message)
                    else:
                        results[tool_name] = (False, f"{tool_name} requires manual installation")
                elif tool_info['available']:
                    results[tool_name] = (True, f"{tool_name} already available")
                else:
                    results[tool_name] = (False, f"{tool_name} not supported on this platform")
        
        return results
    
    def get_compilation_capabilities(self) -> Dict[str, List[str]]:
        """Get what payload types can be compiled on current platform"""
        tools = self.detect_all_tools()
        capabilities = {
            'windows_exe': [],
            'linux_binary': [],
            'macos_app': [],
            'windows_installer': [],
            'linux_installer': [],
            'macos_installer': []
        }
        
        # Windows executables
        if tools['py2exe']['available'] or tools['pyinstaller']['available']:
            capabilities['windows_exe'] = ['py2exe'] if tools['py2exe']['available'] else []
            if tools['pyinstaller']['available']:
                capabilities['windows_exe'].append('pyinstaller')
        
        # Linux binaries
        if tools['pyinstaller']['available'] and self.platform_system == 'linux':
            capabilities['linux_binary'] = ['pyinstaller']
        
        # macOS apps
        if tools['pyinstaller']['available'] and self.platform_system == 'darwin':
            capabilities['macos_app'] = ['pyinstaller']
        
        # Installers
        if tools['nsis']['available']:
            capabilities['windows_installer'] = ['nsis']
        
        if tools['makeself']['available']:
            if self.platform_system == 'linux':
                capabilities['linux_installer'] = ['makeself']
            elif self.platform_system == 'darwin':
                capabilities['macos_installer'] = ['makeself']
        
        return capabilities
    
    def get_recommended_tools_for_target(self, target_os: str) -> List[str]:
        """Get recommended tools for targeting a specific OS"""
        recommendations = {
            'windows': ['pyinstaller', 'py2exe', 'nsis'],
            'linux': ['pyinstaller', 'makeself'],
            'macos': ['pyinstaller', 'makeself'],
            'auto': ['pyinstaller']  # Universal tool
        }
        
        return recommendations.get(target_os, ['pyinstaller'])
    
    def create_build_environment_info(self) -> Dict:
        """Create comprehensive build environment information"""
        tools = self.detect_all_tools()
        capabilities = self.get_compilation_capabilities()
        
        return {
            'platform': {
                'system': self.platform_system,
                'architecture': self.architecture,
                'python_version': self.python_version
            },
            'tools': tools,
            'capabilities': capabilities,
            'recommendations': {
                'windows': self.get_recommended_tools_for_target('windows'),
                'linux': self.get_recommended_tools_for_target('linux'),
                'macos': self.get_recommended_tools_for_target('macos')
            }
        }

# Global instance
build_tools_manager = BuildToolsManager()

def get_build_tools_status() -> Dict:
    """Get current build tools status - for API use"""
    return build_tools_manager.detect_all_tools()

def install_missing_build_tools(required_tools: List[str] = None) -> Dict:
    """Install missing build tools - for API use"""
    return build_tools_manager.install_missing_tools(required_tools)

def get_compilation_capabilities() -> Dict:
    """Get compilation capabilities - for API use"""
    return build_tools_manager.get_compilation_capabilities()

if __name__ == "__main__":
    # Test the build tools manager
    manager = BuildToolsManager()
    
    print("=== Build Tools Detection ===")
    tools = manager.detect_all_tools()
    for tool_name, info in tools.items():
        status = "✅ Available" if info['available'] else "❌ Missing"
        version = f" (v{info['version']})" if info['version'] else ""
        print(f"{tool_name}: {status}{version}")
        if info['error']:
            print(f"  Error: {info['error']}")
    
    print("\n=== Compilation Capabilities ===")
    capabilities = manager.get_compilation_capabilities()
    for cap_type, tools_list in capabilities.items():
        if tools_list:
            print(f"{cap_type}: {', '.join(tools_list)}")
    
    print("\n=== Build Environment Info ===")
    env_info = manager.create_build_environment_info()
    print(json.dumps(env_info, indent=2))