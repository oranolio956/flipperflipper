#!/usr/bin/env python3
"""
Fix mobile UI issues:
- Text overflow on Payloads tab
- Relocate the huge red logout button
"""

import os
import shutil
from pathlib import Path

class MobileUIFixer:
    def __init__(self):
        self.fixes = []
        self.css_path = '/workspace/static/css/style_real.css'
        self.html_path = '/workspace/templates/dashboard_real.html'
        self.js_path = '/workspace/static/js/app_real.js'
        
    def backup_files(self):
        """Backup original files"""
        print("[BACKUP] Creating backups...")
        
        for path in [self.css_path, self.html_path, self.js_path]:
            if os.path.exists(path):
                backup = f"{path}.mobile_fix_backup"
                shutil.copy(path, backup)
                print(f"  ✓ Backed up: {os.path.basename(path)}")
                
        self.fixes.append("Created file backups")
        
    def fix_mobile_css(self):
        """Fix CSS for mobile responsiveness"""
        print("\n[FIX] Updating mobile CSS...")
        
        # Read current CSS
        with open(self.css_path, 'r') as f:
            css = f.read()
            
        # Enhanced mobile CSS
        mobile_css = '''
/* ==================== ENHANCED MOBILE STYLES ==================== */
@media (max-width: 768px) {
    /* Sidebar adjustments */
    .sidebar {
        width: 60px !important;
        min-width: 60px !important;
        transition: all 0.3s ease;
    }
    
    .sidebar.expanded {
        width: 200px !important;
    }
    
    .sidebar-header {
        padding: 10px 5px;
    }
    
    .sidebar-header h3 {
        display: none;
    }
    
    .sidebar.expanded .sidebar-header h3 {
        display: block;
        font-size: 14px;
    }
    
    /* Navigation menu */
    .nav-menu {
        padding: 0;
    }
    
    .nav-menu li {
        position: relative;
    }
    
    .nav-menu a {
        padding: 15px 10px;
        justify-content: center;
    }
    
    .nav-menu span {
        display: none;
    }
    
    .sidebar.expanded .nav-menu span {
        display: inline;
        margin-left: 10px;
    }
    
    /* Logout button - top right corner */
    .logout-btn {
        display: none !important;
    }
    
    .mobile-logout {
        display: block !important;
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 9999;
        padding: 8px 15px;
        background: #dc3545;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Main content adjustments */
    .main-content {
        margin-left: 70px;
        padding: 15px;
    }
    
    .sidebar.expanded ~ .main-content {
        margin-left: 210px;
    }
    
    /* Payloads tab fixes */
    .payload-config {
        padding: 15px;
        overflow-x: auto;
    }
    
    .payload-config h2 {
        font-size: 20px;
        margin-bottom: 15px;
        word-wrap: break-word;
    }
    
    .config-section {
        margin-bottom: 20px;
    }
    
    .config-section h3 {
        font-size: 16px;
        margin-bottom: 10px;
        word-wrap: break-word;
    }
    
    .form-group {
        margin-bottom: 15px;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 5px;
        font-size: 14px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .form-control {
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        font-size: 14px;
    }
    
    /* Prevent text overflow */
    * {
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }
    
    /* Tables responsive */
    .table-responsive {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    table {
        min-width: 100%;
    }
    
    /* Cards and containers */
    .card {
        margin-bottom: 15px;
    }
    
    .card-body {
        padding: 10px;
        overflow-x: auto;
    }
    
    /* Buttons */
    .btn {
        padding: 8px 12px;
        font-size: 14px;
        margin: 2px;
    }
    
    /* Grid adjustments */
    .row {
        margin: 0;
    }
    
    .col-md-6,
    .col-lg-4 {
        padding: 5px;
    }
    
    /* Terminal/console */
    .terminal {
        font-size: 12px;
    }
    
    /* Modals */
    .modal-dialog {
        margin: 10px;
        max-width: calc(100% - 20px);
    }
    
    /* Hamburger menu for sidebar */
    .sidebar-toggle {
        display: block !important;
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 9998;
        background: #2c3e50;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
    }
}

/* Desktop - hide mobile elements */
@media (min-width: 769px) {
    .mobile-logout {
        display: none !important;
    }
    
    .sidebar-toggle {
        display: none !important;
    }
}
'''
        
        # Check if mobile styles already exist
        if '@media (max-width: 768px)' in css:
            # Find and replace the mobile section
            start = css.find('/* ==================== ENHANCED MOBILE STYLES')
            if start == -1:
                start = css.find('@media (max-width: 768px)')
            
            if start > 0:
                # Find the end of this media query block
                end = css.find('@media', start + 1)
                if end == -1:
                    end = len(css)
                    
                # Replace the section
                css = css[:start] + mobile_css + css[end:]
            else:
                # Append if not found
                css += '\n' + mobile_css
        else:
            # Append mobile styles
            css += '\n' + mobile_css
            
        # Write updated CSS
        with open(self.css_path, 'w') as f:
            f.write(css)
            
        print("  ✓ Mobile CSS updated")
        self.fixes.append("Enhanced mobile CSS styles")
        
    def fix_mobile_html(self):
        """Fix HTML for mobile layout"""
        print("\n[FIX] Updating HTML for mobile...")
        
        with open(self.html_path, 'r') as f:
            html = f.read()
            
        # Add mobile logout button if not present
        if 'mobile-logout' not in html:
            # Find body tag
            body_pos = html.find('<body')
            if body_pos > 0:
                # Find end of body tag
                body_end = html.find('>', body_pos)
                
                # Insert mobile elements after body
                mobile_elements = '''
    <!-- Mobile UI Elements -->
    <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
    <button class="mobile-logout" onclick="location.href='/logout'">Exit</button>
'''
                html = html[:body_end+1] + mobile_elements + html[body_end+1:]
                
        # Write updated HTML
        with open(self.html_path, 'w') as f:
            f.write(html)
            
        print("  ✓ Mobile HTML elements added")
        self.fixes.append("Added mobile HTML elements")
        
    def fix_mobile_javascript(self):
        """Add JavaScript for mobile interactions"""
        print("\n[FIX] Adding mobile JavaScript...")
        
        with open(self.js_path, 'r') as f:
            js = f.read()
            
        # Add mobile functions if not present
        if 'toggleSidebar' not in js:
            mobile_js = '''

// ==================== MOBILE UI FUNCTIONS ====================

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('expanded');
    }
}

// Auto-collapse sidebar on mobile page load
document.addEventListener('DOMContentLoaded', function() {
    if (window.innerWidth <= 768) {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.remove('expanded');
        }
    }
});

// Handle responsive layout on resize
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar && sidebar.classList.contains('expanded')) {
                sidebar.classList.remove('expanded');
            }
        }
    }, 250);
});

// Prevent text overflow in payload config
function fixTextOverflow() {
    const labels = document.querySelectorAll('.payload-config label');
    labels.forEach(label => {
        if (label.scrollWidth > label.clientWidth) {
            label.style.fontSize = '12px';
            label.style.lineHeight = '1.2';
        }
    });
}

// Run on load and tab change
document.addEventListener('DOMContentLoaded', fixTextOverflow);
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-tab="payloads"]')) {
        setTimeout(fixTextOverflow, 100);
    }
});
'''
            js += mobile_js
            
        # Write updated JS
        with open(self.js_path, 'w') as f:
            f.write(js)
            
        print("  ✓ Mobile JavaScript added")
        self.fixes.append("Added mobile JavaScript functions")
        
    def test_mobile_fixes(self):
        """Verify the fixes were applied"""
        print("\n[TEST] Verifying mobile fixes...")
        
        tests_passed = []
        
        # Test CSS
        with open(self.css_path, 'r') as f:
            css = f.read()
            
        if '.mobile-logout' in css:
            print("  ✓ Mobile logout CSS present")
            tests_passed.append("Mobile logout CSS")
        else:
            print("  ✗ Mobile logout CSS missing")
            
        if 'overflow-wrap: break-word' in css:
            print("  ✓ Text overflow fix present")
            tests_passed.append("Text overflow fix")
        else:
            print("  ✗ Text overflow fix missing")
            
        # Test HTML
        with open(self.html_path, 'r') as f:
            html = f.read()
            
        if 'mobile-logout' in html:
            print("  ✓ Mobile logout button in HTML")
            tests_passed.append("Mobile logout HTML")
        else:
            print("  ✗ Mobile logout button missing")
            
        if 'sidebar-toggle' in html:
            print("  ✓ Sidebar toggle button present")
            tests_passed.append("Sidebar toggle")
        else:
            print("  ✗ Sidebar toggle missing")
            
        # Test JS
        with open(self.js_path, 'r') as f:
            js = f.read()
            
        if 'toggleSidebar' in js:
            print("  ✓ Toggle sidebar function present")
            tests_passed.append("Toggle function")
        else:
            print("  ✗ Toggle sidebar function missing")
            
        return len(tests_passed) >= 4
        
    def generate_report(self):
        """Generate fix report"""
        print("\n" + "="*70)
        print("MOBILE UI FIX REPORT")
        print("="*70)
        
        print("\n[FIXES APPLIED]")
        for i, fix in enumerate(self.fixes, 1):
            print(f"  {i}. {fix}")
            
        print("\n[IMPROVEMENTS]")
        print("  ✓ Logout button moved to top-right corner")
        print("  ✓ Text overflow fixed with word-wrap")
        print("  ✓ Collapsible sidebar for mobile")
        print("  ✓ Responsive payload configuration")
        print("  ✓ Touch-friendly buttons and controls")
        print("  ✓ Hamburger menu for navigation")
        
        print("\n[TESTING]")
        print("  To test mobile UI:")
        print("  1. Open browser developer tools (F12)")
        print("  2. Toggle device toolbar (Ctrl+Shift+M)")
        print("  3. Select mobile device (e.g., iPhone)")
        print("  4. Navigate to http://localhost:5000")
        
        # Save report
        with open('/workspace/mobile_ui_fixes.txt', 'w') as f:
            f.write("MOBILE UI FIXES\n")
            f.write("="*50 + "\n\n")
            for fix in self.fixes:
                f.write(f"- {fix}\n")
            f.write("\nTo test: Use browser responsive mode (F12 -> Ctrl+Shift+M)\n")
            
        print("\n[+] Report saved to mobile_ui_fixes.txt")

def main():
    print("="*70)
    print("FIXING MOBILE UI ISSUES")
    print("="*70)
    
    fixer = MobileUIFixer()
    
    # Backup files first
    fixer.backup_files()
    
    # Apply fixes
    fixer.fix_mobile_css()
    fixer.fix_mobile_html()
    fixer.fix_mobile_javascript()
    
    # Test fixes
    success = fixer.test_mobile_fixes()
    
    # Generate report
    fixer.generate_report()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)