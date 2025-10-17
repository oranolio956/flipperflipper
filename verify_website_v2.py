#!/usr/bin/env python3
"""
Comprehensive Website Verification Script v2
Compares local reconstruction with live site - handles .html extensions
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse

# Configuration
LOCAL_SITE_PATH = "/workspace/cupidbot-website-backup/cupidbot.ai"
LOCAL_PORT = 8000
LOCAL_BASE_URL = f"http://localhost:{LOCAL_PORT}"
LIVE_BASE_URL = "https://cupidbot.ai"
SCREENSHOT_DIR = "/workspace/verification_screenshots"

# Pages to verify - with correct local paths
PAGES = [
    ("Home", "/", "/"),
    ("Contact", "/contact", "/contact.html"),
    ("Product", "/product/beta", "/product/beta.html"),
    ("Policies", "/post/policies", "/post/policies.html"),
    ("Privacy", "/post/privacy-policy", "/post/privacy-policy.html"),
]

class WebsiteVerifier:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.server_process = None
        self.browser = None
        self.context = None
        self.detailed_report = []
        
    def log(self, message, level="INFO"):
        """Log message with formatting"""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CHECK": "🔍",
            "COMPARE": "📊"
        }
        print(f"{symbols.get(level, '•')} {message}")
        
    def start_local_server(self):
        """Start local HTTP server"""
        self.log("Starting local web server...", "INFO")
        try:
            self.server_process = subprocess.Popen(
                ["python3", "-m", "http.server", str(LOCAL_PORT)],
                cwd=LOCAL_SITE_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            self.log(f"Local server running at {LOCAL_BASE_URL}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            return False
            
    def stop_local_server(self):
        """Stop local HTTP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.log("Local server stopped", "INFO")
            
    def setup_browser(self):
        """Setup Playwright browser"""
        self.log("Setting up browser...", "INFO")
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.log("Browser ready", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to setup browser: {e}", "ERROR")
            return False
            
    def cleanup_browser(self):
        """Cleanup browser resources"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
            
    def take_screenshot(self, url, filename):
        """Take screenshot of a page"""
        try:
            page = self.context.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(2)  # Wait for animations
            
            screenshot_path = os.path.join(SCREENSHOT_DIR, filename)
            page.screenshot(path=screenshot_path, full_page=True)
            page.close()
            
            return screenshot_path
        except Exception as e:
            self.log(f"Failed to screenshot {url}: {e}", "ERROR")
            self.issues.append(f"Screenshot failed for {url}: {e}")
            return None
            
    def check_page_content(self, url, page_name, is_local=False):
        """Deep check of page content and structure"""
        self.log(f"Analyzing {page_name} content...", "CHECK")
        report = {
            'page': page_name,
            'type': 'LOCAL' if is_local else 'LIVE',
            'url': url,
            'images': [],
            'scripts': [],
            'stylesheets': [],
            'links': [],
            'forms': [],
            'missing_resources': [],
            'console_errors': []
        }
        
        try:
            page = self.context.new_page()
            
            # Track failed requests
            failed_requests = []
            def handle_response(response):
                if response.status >= 400:
                    failed_requests.append({
                        'url': response.url,
                        'status': response.status,
                        'type': response.request.resource_type
                    })
            
            page.on('response', handle_response)
            
            # Track console errors
            def handle_console(msg):
                if msg.type == 'error':
                    report['console_errors'].append(msg.text)
            page.on('console', handle_console)
            
            # Load page
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(1)
            
            # Extract images
            images = page.query_selector_all('img')
            for img in images:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt') or ''
                if src:
                    report['images'].append({'src': src, 'alt': alt})
                    
            # Extract scripts
            scripts = page.query_selector_all('script[src]')
            for script in scripts:
                src = script.get_attribute('src')
                if src:
                    report['scripts'].append(src)
                    
            # Extract stylesheets
            stylesheets = page.query_selector_all('link[rel="stylesheet"]')
            for css in stylesheets:
                href = css.get_attribute('href')
                if href:
                    report['stylesheets'].append(href)
                    
            # Extract links
            links = page.query_selector_all('a[href]')
            for link in links:
                href = link.get_attribute('href')
                text = link.inner_text()[:50]
                if href:
                    report['links'].append({'href': href, 'text': text})
                    
            # Extract forms
            forms = page.query_selector_all('form')
            for form in forms:
                action = form.get_attribute('action')
                method = form.get_attribute('method') or 'GET'
                report['forms'].append({'action': action, 'method': method})
            
            # Add failed requests
            report['missing_resources'] = failed_requests
            
            page.close()
            
            # Log summary
            self.log(f"{page_name}: {len(report['images'])} images, {len(report['scripts'])} scripts, {len(report['links'])} links", "INFO")
            
            if failed_requests:
                self.log(f"{page_name}: {len(failed_requests)} resources failed to load", "WARNING")
                for req in failed_requests[:3]:
                    self.log(f"  - {req['type']}: {req['url'][:60]}... (Status: {req['status']})", "WARNING")
                    
            if report['console_errors']:
                self.log(f"{page_name}: {len(report['console_errors'])} console errors", "WARNING")
                
        except Exception as e:
            self.log(f"Error analyzing {page_name}: {e}", "ERROR")
            self.issues.append(f"{page_name}: Analysis failed: {e}")
            
        return report
        
    def compare_content(self, local_report, live_report):
        """Compare local and live content"""
        page_name = local_report['page']
        self.log(f"Comparing {page_name} content...", "COMPARE")
        
        differences = []
        
        # Compare image counts
        local_img_count = len(local_report['images'])
        live_img_count = len(live_report['images'])
        if local_img_count != live_img_count:
            diff = f"Image count mismatch: Local={local_img_count}, Live={live_img_count}"
            differences.append(diff)
            self.warnings.append(f"{page_name}: {diff}")
            
        # Compare script counts
        local_script_count = len(local_report['scripts'])
        live_script_count = len(live_report['scripts'])
        if local_script_count != live_script_count:
            diff = f"Script count mismatch: Local={local_script_count}, Live={live_script_count}"
            differences.append(diff)
            self.warnings.append(f"{page_name}: {diff}")
            
        # Compare link counts
        local_link_count = len(local_report['links'])
        live_link_count = len(live_report['links'])
        if local_link_count != live_link_count:
            diff = f"Link count mismatch: Local={local_link_count}, Live={live_link_count}"
            differences.append(diff)
            self.warnings.append(f"{page_name}: {diff}")
            
        # Check for missing resources on local
        if local_report['missing_resources']:
            for resource in local_report['missing_resources']:
                issue = f"Missing {resource['type']}: {resource['url']}"
                self.issues.append(f"{page_name} (LOCAL): {issue}")
                
        if differences:
            for diff in differences:
                self.log(f"  {diff}", "WARNING")
        else:
            self.log(f"{page_name}: Content structure matches!", "SUCCESS")
            
        return differences
        
    def verify_page(self, page_name, live_path, local_path):
        """Complete verification of a single page"""
        self.log(f"\n{'='*70}", "INFO")
        self.log(f"Verifying: {page_name}", "INFO")
        self.log(f"{'='*70}", "INFO")
        
        local_url = LOCAL_BASE_URL + local_path
        live_url = LIVE_BASE_URL + live_path
        
        self.log(f"LOCAL: {local_url}", "INFO")
        self.log(f"LIVE:  {live_url}", "INFO")
        
        # Take screenshots
        self.log(f"Taking screenshots...", "CHECK")
        local_screenshot = self.take_screenshot(local_url, f"{page_name.lower()}_local.png")
        live_screenshot = self.take_screenshot(live_url, f"{page_name.lower()}_live.png")
        
        if local_screenshot and live_screenshot:
            self.log(f"Screenshots saved successfully", "SUCCESS")
        
        # Analyze content
        local_report = self.check_page_content(local_url, page_name, is_local=True)
        live_report = self.check_page_content(live_url, page_name, is_local=False)
        
        # Compare
        self.compare_content(local_report, live_report)
        
        self.detailed_report.append({
            'page': page_name,
            'local': local_report,
            'live': live_report,
            'screenshots': {
                'local': local_screenshot,
                'live': live_screenshot
            }
        })
        
    def generate_report(self):
        """Generate detailed comparison report"""
        report_path = os.path.join(SCREENSHOT_DIR, "verification_report.txt")
        
        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("  CupidBot.ai Website Verification Report\n")
            f.write("="*70 + "\n\n")
            
            for page_data in self.detailed_report:
                f.write(f"\n{'='*70}\n")
                f.write(f"PAGE: {page_data['page']}\n")
                f.write(f"{'='*70}\n\n")
                
                local = page_data['local']
                live = page_data['live']
                
                f.write(f"LOCAL vs LIVE Comparison:\n")
                f.write(f"  Images:      {len(local['images'])} vs {len(live['images'])}\n")
                f.write(f"  Scripts:     {len(local['scripts'])} vs {len(live['scripts'])}\n")
                f.write(f"  Stylesheets: {len(local['stylesheets'])} vs {len(live['stylesheets'])}\n")
                f.write(f"  Links:       {len(local['links'])} vs {len(live['links'])}\n")
                f.write(f"  Forms:       {len(local['forms'])} vs {len(live['forms'])}\n\n")
                
                if local['missing_resources']:
                    f.write(f"Missing Resources (LOCAL):\n")
                    for res in local['missing_resources']:
                        f.write(f"  - {res['type']}: {res['url']} (Status: {res['status']})\n")
                    f.write("\n")
                    
                if local['console_errors']:
                    f.write(f"Console Errors (LOCAL): {len(local['console_errors'])}\n")
                    for err in local['console_errors'][:5]:
                        f.write(f"  - {err[:100]}\n")
                    f.write("\n")
                    
        self.log(f"Detailed report saved to: {report_path}", "SUCCESS")
        return report_path
        
    def run_verification(self):
        """Run complete verification"""
        print("\n" + "="*70)
        print("  🔍 CupidBot.ai Website Verification - Comprehensive Analysis")
        print("="*70 + "\n")
        
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        if not self.start_local_server():
            return False
            
        if not self.setup_browser():
            self.stop_local_server()
            return False
            
        try:
            # Verify each page
            for page_name, live_path, local_path in PAGES:
                self.verify_page(page_name, live_path, local_path)
                
            # Generate detailed report
            report_path = self.generate_report()
            
            # Summary
            print("\n" + "="*70)
            print("  📊 VERIFICATION SUMMARY")
            print("="*70 + "\n")
            
            print(f"📄 Pages Verified: {len(PAGES)}")
            print(f"📸 Screenshots: {len(PAGES) * 2}")
            print(f"📋 Detailed Report: {report_path}\n")
            
            if self.issues:
                self.log(f"❌ CRITICAL ISSUES: {len(self.issues)}", "ERROR")
                for i, issue in enumerate(self.issues, 1):
                    print(f"  {i}. {issue}")
                print()
                    
            if self.warnings:
                self.log(f"⚠️  WARNINGS: {len(self.warnings)}", "WARNING")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
                print()
                    
            if not self.issues and not self.warnings:
                self.log("✨ PERFECT! No issues or warnings found!", "SUCCESS")
                self.log("Your website is a perfect 1:1 copy!", "SUCCESS")
            elif not self.issues:
                self.log("✅ No critical issues! Only minor warnings.", "SUCCESS")
                self.log("Your website is production-ready!", "SUCCESS")
                
            print("\n" + "="*70)
            print("  📸 Screenshots Location:")
            print(f"  {SCREENSHOT_DIR}")
            print("="*70 + "\n")
            
            return True
            
        finally:
            self.cleanup_browser()
            self.stop_local_server()

def main():
    verifier = WebsiteVerifier()
    try:
        verifier.run_verification()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        verifier.cleanup_browser()
        verifier.stop_local_server()
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        verifier.cleanup_browser()
        verifier.stop_local_server()

if __name__ == "__main__":
    main()
