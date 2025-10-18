#!/usr/bin/env python3
"""
Fix all web interface issues:
1. Remove "Disconnected from server" notifications
2. Fix eternal "Loading..." states
3. Fix mobile layout issues
4. Move logout button for mobile
5. Remove login rate limiting (already done)
"""

import os
import re

def fix_disconnect_notifications():
    """Fix the disconnected from server notifications"""
    print("[*] Fixing disconnect notifications...")
    
    # Fix in app_real.js
    js_file = '/workspace/static/js/app_real.js'
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            content = f.read()
        
        # Comment out the disconnect notification but keep the status update
        original = """    socket.on('disconnect', () => {
        document.getElementById('serverStatus').classList.remove('online');
        document.getElementById('statusText').textContent = 'Disconnected';
        showToast('Disconnected from server', 'error');
    });"""
        
        replacement = """    socket.on('disconnect', () => {
        document.getElementById('serverStatus').classList.remove('online');
        document.getElementById('statusText').textContent = 'Reconnecting...';
        // Removed annoying disconnect notification - it will auto-reconnect
        // showToast('Disconnected from server', 'error');
    });"""
        
        if original in content:
            content = content.replace(original, replacement)
            with open(js_file, 'w') as f:
                f.write(content)
            print("  [+] Fixed disconnect notification")
        else:
            print("  [!] Disconnect code not found in expected format")

def fix_loading_states():
    """Fix eternal Loading... states"""
    print("[*] Fixing eternal Loading... states...")
    
    js_file = '/workspace/static/js/app_real.js'
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            content = f.read()
        
        # Add timeout to all fetch operations to prevent eternal loading
        fixes_applied = []
        
        # Fix 1: Add default values and timeouts to loadConnections
        if 'async function loadConnections()' in content:
            # Add timeout wrapper
            timeout_wrapper = """
// Helper function for fetch with timeout
function fetchWithTimeout(url, options = {}, timeout = 10000) {
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), timeout)
        )
    ]);
}

"""
            if 'fetchWithTimeout' not in content:
                # Add before first async function
                content = content.replace('async function loadConnections()', 
                                        timeout_wrapper + 'async function loadConnections()')
                fixes_applied.append("Added fetchWithTimeout helper")
            
            # Replace fetch with fetchWithTimeout in loadConnections
            content = re.sub(
                r"const response = await fetch\('/api/connections'",
                "const response = await fetchWithTimeout('/api/connections'",
                content
            )
            fixes_applied.append("Added timeout to loadConnections")
        
        # Fix 2: Add default empty state handlers
        empty_state_handler = """
        // Show empty state if no connections
        if (!connections || connections.length === 0) {
            document.querySelector('.connections-grid').innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 2rem; color: #888;">
                    <p style="font-size: 1.2rem;">No connections available</p>
                    <p style="margin-top: 1rem;">Waiting for incoming connections...</p>
                </div>
            `;
            document.getElementById('serverListening').textContent = 'Listening';
            document.getElementById('serverPort').textContent = '4040';
            return;
        }
"""
        
        # Insert after connections loaded
        pattern = r"(const connections = await response\.json\(\);)"
        replacement = r"\1" + empty_state_handler
        content = re.sub(pattern, replacement, content, count=1)
        fixes_applied.append("Added empty state handler")
        
        # Fix 3: Add error handlers for all API calls
        error_handler = """
    } catch (error) {
        console.error('Failed to load:', error);
        // Clear loading states on error
        document.querySelectorAll('.loading').forEach(el => {
            el.classList.remove('loading');
            el.textContent = 'Error loading';
        });
        // Set default values
        document.getElementById('serverListening').textContent = 'Unknown';
        document.getElementById('serverPort').textContent = 'Unknown';
"""
        
        # Make sure all try blocks have proper error handlers
        content = re.sub(
            r"(\} catch \(error\) \{[\s]*console\.error[^}]+)\}",
            error_handler + "    }",
            content
        )
        fixes_applied.append("Enhanced error handlers")
        
        with open(js_file, 'w') as f:
            f.write(content)
        
        for fix in fixes_applied:
            print(f"  [+] {fix}")

def fix_mobile_layout():
    """Fix mobile layout issues and logout button"""
    print("[*] Fixing mobile layout issues...")
    
    # Fix CSS for mobile
    css_file = '/workspace/static/css/style_real.css'
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
        
        # Add/update mobile styles
        mobile_fixes = """
/* Mobile Layout Fixes */
@media (max-width: 768px) {
    /* Hide text, show only icons in sidebar */
    .sidebar {
        width: 60px;
        min-width: 60px;
    }
    
    .sidebar-header h2 {
        font-size: 1.2rem;
        text-align: center;
    }
    
    .sidebar-header .version {
        display: none;
    }
    
    .nav-menu li a span {
        font-size: 1.5rem;
    }
    
    .nav-menu li a {
        padding: 1rem;
        justify-content: center;
    }
    
    .nav-menu li a::after {
        display: none;
    }
    
    /* Move logout button to top-right corner */
    .logout-btn {
        position: fixed;
        top: 10px;
        right: 10px;
        background: #dc3545;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-size: 0.9rem;
        z-index: 1000;
        width: auto;
        margin: 0;
    }
    
    .sidebar-footer {
        display: none;
    }
    
    /* Fix main content */
    .main-content {
        margin-left: 60px;
        padding: 1rem;
    }
    
    /* Fix payload tab text overflow */
    .payload-config label {
        font-size: 0.9rem;
    }
    
    .payload-config input,
    .payload-config select {
        width: 100%;
        font-size: 0.9rem;
        padding: 0.4rem;
    }
    
    .btn {
        font-size: 0.9rem;
        padding: 0.6rem 1rem;
    }
    
    /* Fix grid layouts for mobile */
    .connections-grid {
        grid-template-columns: 1fr;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    /* Fix table overflow */
    .table-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    table {
        min-width: 600px;
    }
    
    /* Fix modals for mobile */
    .modal-content {
        width: 95%;
        margin: 10px;
        max-height: 90vh;
        overflow-y: auto;
    }
}

/* Tablet adjustments */
@media (min-width: 769px) and (max-width: 1024px) {
    .sidebar {
        width: 200px;
    }
    
    .logout-btn {
        width: 100%;
        margin-top: 1rem;
        background: #dc3545;
    }
}
"""
        
        # Append mobile fixes to CSS
        if "@media (max-width: 768px)" not in css_content:
            css_content += "\n\n" + mobile_fixes
            with open(css_file, 'w') as f:
                f.write(css_content)
            print("  [+] Added mobile CSS fixes")
        else:
            print("  [!] Mobile styles already present, updating...")
            # Replace existing mobile styles
            css_content = re.sub(
                r'@media \(max-width: 768px\) \{[^}]*\}',
                mobile_fixes,
                css_content,
                flags=re.DOTALL
            )
            with open(css_file, 'w') as f:
                f.write(css_content)
            print("  [+] Updated mobile CSS")
    
    # Fix HTML structure for mobile logout button
    html_file = '/workspace/templates/dashboard_real.html'
    if os.path.exists(html_file):
        with open(html_file, 'r') as f:
            html_content = f.read()
        
        # Move logout button for mobile (add duplicate that shows only on mobile)
        mobile_logout = """
    <!-- Mobile Logout Button -->
    <a href="{{ url_for('logout') }}" class="logout-btn mobile-only" style="display: none;">
        <span style="font-size: 0.8rem;">Exit</span>
    </a>
"""
        
        # Add after body tag
        if 'mobile-only' not in html_content:
            html_content = html_content.replace('<body>', '<body>\n' + mobile_logout)
            with open(html_file, 'w') as f:
                f.write(html_content)
            print("  [+] Added mobile logout button")
    
    # Add JavaScript to handle mobile detection
    js_file = '/workspace/static/js/app_real.js'
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            js_content = f.read()
        
        mobile_js = """
// Mobile detection and UI adjustments
function adjustForMobile() {
    const isMobile = window.innerWidth <= 768;
    const mobileLogout = document.querySelector('.logout-btn.mobile-only');
    const sidebarLogout = document.querySelector('.sidebar-footer .logout-btn');
    
    if (mobileLogout) {
        mobileLogout.style.display = isMobile ? 'block' : 'none';
    }
    if (sidebarLogout && isMobile) {
        sidebarLogout.style.display = 'none';
    }
}

// Run on load and resize
window.addEventListener('resize', adjustForMobile);
document.addEventListener('DOMContentLoaded', adjustForMobile);
"""
        
        if 'adjustForMobile' not in js_content:
            js_content += "\n\n" + mobile_js
            with open(js_file, 'w') as f:
                f.write(js_content)
            print("  [+] Added mobile JavaScript handlers")

def verify_fixes():
    """Verify all fixes were applied"""
    print("\n[*] Verifying fixes...")
    
    checks = {
        "Login rate limiting removed": False,
        "Disconnect notification fixed": False,
        "Loading states fixed": False,
        "Mobile CSS added": False,
        "Mobile logout button added": False
    }
    
    # Check login rate limiting
    with open('/workspace/web_app_real.py', 'r') as f:
        if '# Rate limiting removed for easier testing' in f.read():
            checks["Login rate limiting removed"] = True
    
    # Check disconnect notification
    with open('/workspace/static/js/app_real.js', 'r') as f:
        content = f.read()
        if '// Removed annoying disconnect notification' in content:
            checks["Disconnect notification fixed"] = True
        if 'fetchWithTimeout' in content:
            checks["Loading states fixed"] = True
    
    # Check mobile CSS
    with open('/workspace/static/css/style_real.css', 'r') as f:
        if 'Mobile Layout Fixes' in f.read():
            checks["Mobile CSS added"] = True
    
    # Check mobile logout
    with open('/workspace/templates/dashboard_real.html', 'r') as f:
        if 'mobile-only' in f.read():
            checks["Mobile logout button added"] = True
    
    print("\nVerification Results:")
    all_good = True
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
        if not passed:
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("="*60)
    print("FIXING WEB INTERFACE ISSUES")
    print("="*60)
    
    fix_disconnect_notifications()
    fix_loading_states()
    fix_mobile_layout()
    
    if verify_fixes():
        print("\n[+] All fixes applied successfully!")
    else:
        print("\n[!] Some fixes may have failed, check manually")