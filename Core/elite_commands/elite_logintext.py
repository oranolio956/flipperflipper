#!/usr/bin/env python3
"""
Elite Login Text Command - Modify Windows login screen text and messages
Advanced login screen customization and message injection
"""

import ctypes
from ctypes import wintypes
import winreg
import os

class EliteLoginText:
    """Elite login screen text manipulation"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        
    def execute(self, action='set', message=None, title=None, legal_notice=None):
        """Manipulate login screen text and messages"""
        try:
            if action == 'set':
                return self._set_login_message(message, title)
            elif action == 'set_legal':
                return self._set_legal_notice(legal_notice, title)
            elif action == 'get':
                return self._get_login_messages()
            elif action == 'clear':
                return self._clear_login_messages()
            elif action == 'set_banner':
                return self._set_login_banner(message)
            elif action == 'set_shutdown_reason':
                return self._set_shutdown_reason_display()
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'available_actions': ['set', 'set_legal', 'get', 'clear', 'set_banner', 'set_shutdown_reason']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Login text operation failed: {str(e)}'
            }
    
    def _set_login_message(self, message, title):
        """Set login screen message"""
        try:
            if not message:
                message = "Welcome to this system. Please log in with your credentials."
            if not title:
                title = "System Notice"
            
            # Set login message via registry
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
                
                # Set legal notice caption (title)
                winreg.SetValueEx(key, "legalnoticecaption", 0, winreg.REG_SZ, title)
                
                # Set legal notice text (message)
                winreg.SetValueEx(key, "legalnoticetext", 0, winreg.REG_SZ, message)
                
                winreg.CloseKey(key)
                
                return {
                    'success': True,
                    'action': 'set',
                    'title': title,
                    'message': message,
                    'registry_path': r"HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
                    'note': 'Login message will appear on next login'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to set login message: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Login message setting failed: {str(e)}'
            }
    
    def _set_legal_notice(self, legal_notice, title):
        """Set legal notice for login screen"""
        try:
            if not legal_notice:
                legal_notice = """NOTICE TO USERS

This computer system is the private property of its owner, whether 
individual, corporate or government. It is for authorized use only. 
Users (authorized or unauthorized) have no explicit or implicit 
expectation of privacy.

Any or all uses of this system and all files on this system may be 
intercepted, monitored, recorded, copied, audited, inspected, and 
disclosed to your employer, to authorized site, government, and law 
enforcement personnel, as well as authorized officials of government 
agencies, both domestic and foreign.

By using this system, the user consents to such interception, monitoring, 
recording, copying, auditing, inspection, and disclosure at the 
discretion of such personnel or officials. Unauthorized or improper use 
of this system may result in civil and criminal penalties and 
administrative or disciplinary action, as appropriate. By continuing to 
use this system you indicate your awareness of and consent to these terms 
and conditions of use. LOG OFF IMMEDIATELY if you do not agree to the 
conditions stated in this warning.

**WARNING** Unauthorized access to this system is forbidden and will be 
prosecuted by law. By accessing this system, you agree that your actions 
may be monitored if unauthorized usage is suspected."""
            
            if not title:
                title = "LEGAL NOTICE"
            
            return self._set_login_message(legal_notice, title)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Legal notice setting failed: {str(e)}'
            }
    
    def _get_login_messages(self):
        """Get current login screen messages"""
        try:
            messages = {}
            
            # Get login messages from registry
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
                
                try:
                    title, _ = winreg.QueryValueEx(key, "legalnoticecaption")
                    messages['title'] = title
                except FileNotFoundError:
                    messages['title'] = None
                
                try:
                    text, _ = winreg.QueryValueEx(key, "legalnoticetext")
                    messages['message'] = text
                except FileNotFoundError:
                    messages['message'] = None
                
                winreg.CloseKey(key)
                
            except FileNotFoundError:
                messages['title'] = None
                messages['message'] = None
            
            # Get additional login customizations
            try:
                # Check for custom login background
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\\Policies\\Microsoft\\Windows\\System")
                
                try:
                    bg_enabled, _ = winreg.QueryValueEx(key, "DisableLogonBackgroundImage")
                    messages['background_disabled'] = bool(bg_enabled)
                except FileNotFoundError:
                    messages['background_disabled'] = False
                
                winreg.CloseKey(key)
                
            except FileNotFoundError:
                messages['background_disabled'] = False
            
            # Get shutdown button settings
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
                
                try:
                    shutdown_enabled, _ = winreg.QueryValueEx(key, "shutdownwithoutlogon")
                    messages['shutdown_without_logon'] = bool(shutdown_enabled)
                except FileNotFoundError:
                    messages['shutdown_without_logon'] = True  # Default is enabled
                
                winreg.CloseKey(key)
                
            except FileNotFoundError:
                messages['shutdown_without_logon'] = True
            
            return {
                'success': True,
                'action': 'get',
                'current_messages': messages,
                'has_login_message': messages['message'] is not None,
                'message_length': len(messages['message']) if messages['message'] else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get login messages: {str(e)}'
            }
    
    def _clear_login_messages(self):
        """Clear all login screen messages"""
        try:
            cleared_items = []
            
            # Clear login messages from registry
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", 
                                   0, winreg.KEY_SET_VALUE)
                
                # Remove legal notice caption
                try:
                    winreg.DeleteValue(key, "legalnoticecaption")
                    cleared_items.append("Legal notice caption")
                except FileNotFoundError:
                    pass
                
                # Remove legal notice text
                try:
                    winreg.DeleteValue(key, "legalnoticetext")
                    cleared_items.append("Legal notice text")
                except FileNotFoundError:
                    pass
                
                winreg.CloseKey(key)
                
            except FileNotFoundError:
                pass
            
            return {
                'success': True,
                'action': 'clear',
                'cleared_items': cleared_items,
                'items_cleared': len(cleared_items),
                'message': f'Cleared {len(cleared_items)} login message items'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clear login messages: {str(e)}'
            }
    
    def _set_login_banner(self, message):
        """Set login banner message"""
        try:
            if not message:
                message = "AUTHORIZED USERS ONLY - This system is monitored"
            
            # Set additional login customizations
            changes_made = []
            
            # Set the main login message
            result = self._set_login_message(message, "SYSTEM BANNER")
            if result.get('success'):
                changes_made.append("Login banner message set")
            
            # Disable login background image for better visibility
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\\Policies\\Microsoft\\Windows\\System")
                winreg.SetValueEx(key, "DisableLogonBackgroundImage", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
                changes_made.append("Login background image disabled")
            except Exception:
                pass
            
            # Force display of last logged on user
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
                winreg.SetValueEx(key, "dontdisplaylastusername", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                changes_made.append("Last username display enabled")
            except Exception:
                pass
            
            return {
                'success': True,
                'action': 'set_banner',
                'message': message,
                'changes_made': changes_made,
                'total_changes': len(changes_made)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Login banner setting failed: {str(e)}'
            }
    
    def _set_shutdown_reason_display(self):
        """Enable/configure shutdown reason display"""
        try:
            changes_made = []
            
            # Enable shutdown reason UI
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\\Policies\\Microsoft\\Windows NT\\Reliability")
                winreg.SetValueEx(key, "ShutdownReasonUI", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ShutdownReasonOn", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
                changes_made.append("Shutdown reason UI enabled")
            except Exception as e:
                changes_made.append(f"Shutdown reason UI failed: {str(e)}")
            
            # Configure additional shutdown settings
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
                
                # Enable shutdown without logon
                winreg.SetValueEx(key, "shutdownwithoutlogon", 0, winreg.REG_DWORD, 1)
                changes_made.append("Shutdown without logon enabled")
                
                # Set verbose status messages
                winreg.SetValueEx(key, "verbosestatus", 0, winreg.REG_DWORD, 1)
                changes_made.append("Verbose status messages enabled")
                
                winreg.CloseKey(key)
                
            except Exception as e:
                changes_made.append(f"Shutdown settings failed: {str(e)}")
            
            return {
                'success': True,
                'action': 'set_shutdown_reason',
                'changes_made': changes_made,
                'total_changes': len(changes_made)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Shutdown reason display setting failed: {str(e)}'
            }
    
    def set_custom_login_screen(self, background_image=None, disable_acrylic=True):
        """Set custom login screen appearance"""
        try:
            changes_made = []
            
            # Disable acrylic blur effect
            if disable_acrylic:
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                         r"SOFTWARE\\Policies\\Microsoft\\Windows\\System")
                    winreg.SetValueEx(key, "DisableAcrylicBackgroundOnLogon", 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key)
                    changes_made.append("Acrylic background disabled")
                except Exception:
                    pass
            
            # Set custom background image
            if background_image and os.path.exists(background_image):
                try:
                    # Copy image to Windows directory
                    import shutil
                    target_path = r"C:\\Windows\\System32\\oobe\\info\\backgrounds\\backgroundDefault.jpg"
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy2(background_image, target_path)
                    changes_made.append(f"Custom background set: {background_image}")
                except Exception as e:
                    changes_made.append(f"Background setting failed: {str(e)}")
            
            # Enable custom logon background
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\\Policies\\Microsoft\\Windows\\System")
                winreg.SetValueEx(key, "DisableLogonBackgroundImage", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                changes_made.append("Custom logon background enabled")
            except Exception:
                pass
            
            return {
                'success': True,
                'action': 'set_custom_login_screen',
                'changes_made': changes_made,
                'total_changes': len(changes_made)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Custom login screen setting failed: {str(e)}'
            }

def elite_logintext(action='set', message=None, title=None, legal_notice=None):
    """Elite logintext command entry point"""
    logintext_cmd = EliteLoginText()
    return logintext_cmd.execute(action, message, title, legal_notice)