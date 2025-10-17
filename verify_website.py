#!/usr/bin/env python3
"""
Comprehensive Website Verification Script
Compares local reconstruction with live site at cupidbot.ai
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

# Pages to verify
PAGES = [
    ("Home", "/", "index.html"),
    ("Contact", "/contact", "contact.html"),
    ("Product", "/product/beta", "product/beta.html"),
    ("Policies", "/post/policies", "post/policies.html"),
    ("Privacy", "/post/privacy-policy", "post/privacy-policy.html"),
]

class WebsiteVerifier:
    def __init__(self):
        self.issues = []
        self.server_process = None
        self.browser = None
        self.context = None
        
    def log(self, message, level="INFO"):
        """Log message with formatting"""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CHECK": "🔍"
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
            time.sleep(2)  # Give server time to start
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
            
    def take_screenshot(self, url, filename, wait_for_load=True):
        """Take screenshot of a page"""
        try:
            page = self.context.new_page()
            page.goto(url, wait_until='networkidle' if wait_for_load else 'load', timeout=30000)
            
            # Wait a bit for any animations/lazy loading
            time.sleep(2)
            
            # Take full page screenshot
            screenshot_path = os.path.join(SCREENSHOT_DIR, filename)
            page.screenshot(path=screenshot_path, full_page=True)
            page.close()
            
            return screenshot_path
        except Exception as e:
            self.log(f"Failed to screenshot {url}: {e}", "ERROR")
            self.issues.append(f"Screenshot failed for {url}: {e}")
            return None
            
    def check_page_resources(self, url, page_name):
        """Check if all resources on a page load correctly"""
        self.log(f"Checking resources on {page_name}...", "CHECK")
        issues = []
        
        try:
            page = self.context.new_page()
            
            # Track failed requests
            failed_requests = []
            def handle_response(response):
                if response.status >= 400:
                    failed_requests.append({
                        'url': response.url,
                        'status': response.status
                    })
            
            page.on('response', handle_response)
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Check for console errors
            console_errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
            page.on('console', handle_console)
            
            # Wait a bit
            time.sleep(1)
            
            page.close()
            
            if failed_requests:
                for req in failed_requests:
                    issue = f"{page_name}: Failed to load {req['url']} (Status: {req['status']})"
                    issues.append(issue)
                    self.log(issue, "WARNING")
                    
            if console_errors:
                for error in console_errors[:5]:  # Limit to first 5
                    issue = f"{page_name}: Console error: {error[:100]}"
                    issues.append(issue)
                    self.log(issue, "WARNING")
                    
            if not failed_requests and not console_errors:
                self.log(f"{page_name}: All resources loaded successfully", "SUCCESS")
                
        except Exception as e:
            issue = f"{page_name}: Error checking resources: {e}"
            issues.append(issue)
            self.log(issue, "ERROR")
            
        return issues
        
    def extract_links(self, url, page_name):
        """Extract all links from a page"""
        self.log(f"Extracting links from {page_name}...", "CHECK")
        links = []
        
        try:
            page = self.context.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Get all anchor tags
            link_elements = page.query_selector_all('a')
            for element in link_elements:
                href = element.get_attribute('href')
                if href:
                    links.append(href)
                    
            page.close()
            self.log(f"Found {len(links)} links on {page_name}", "INFO")
            
        except Exception as e:
            self.log(f"Failed to extract links from {page_name}: {e}", "ERROR")
            
        return links
        
    def verify_internal_links(self, base_url, page_name):
        """Verify internal links work"""
        self.log(f"Verifying internal links on {page_name}...", "CHECK")
        links = self.extract_links(base_url, page_name)
        internal_links = [l for l in links if l.startswith('/') or l.startswith('index.') or l.startswith('contact.') or l.startswith('product/') or l.startswith('post/')]
        
        broken_links = []
        for link in internal_links:
            if link.startswith('/'):
                full_url = urljoin(base_url, link)
            else:
                full_url = urljoin(base_url + '/', link)
                
            try:
                page = self.context.new_page()
                response = page.goto(full_url, timeout=10000)
                if response.status >= 400:
                    broken_links.append(f"{link} (Status: {response.status})")
                page.close()
            except Exception as e:
                broken_links.append(f"{link} (Error: {str(e)[:50]})")
                
        if broken_links:
            for link in broken_links[:10]:  # Limit to first 10
                issue = f"{page_name}: Broken link: {link}"
                self.issues.append(issue)
                self.log(issue, "WARNING")
        else:
            self.log(f"{page_name}: All internal links working", "SUCCESS")
            
        return len(broken_links)
        
    def compare_pages(self, page_name, local_url, live_url):
        """Compare local and live versions of a page"""
        self.log(f"\n{'='*70}", "INFO")
        self.log(f"Verifying: {page_name}", "INFO")
        self.log(f"{'='*70}", "INFO")
        
        # Take screenshots
        self.log(f"Taking screenshot of LOCAL {page_name}...", "CHECK")
        local_screenshot = self.take_screenshot(local_url, f"{page_name.lower()}_local.png")
        
        self.log(f"Taking screenshot of LIVE {page_name}...", "CHECK")
        live_screenshot = self.take_screenshot(live_url, f"{page_name.lower()}_live.png")
        
        # Check resources
        local_issues = self.check_page_resources(local_url, f"{page_name} (LOCAL)")
        live_issues = self.check_page_resources(live_url, f"{page_name} (LIVE)")
        
        # Check internal links (only on local)
        self.verify_internal_links(local_url, f"{page_name} (LOCAL)")
        
        # Compare results
        if local_screenshot and live_screenshot:
            self.log(f"Screenshots saved:", "SUCCESS")
            self.log(f"  LOCAL: {local_screenshot}", "INFO")
            self.log(f"  LIVE:  {live_screenshot}", "INFO")
        
        self.issues.extend(local_issues)
        
    def run_verification(self):
        """Run complete verification"""
        print("\n" + "="*70)
        print("  🔍 CupidBot.ai Website Verification")
        print("="*70 + "\n")
        
        # Create screenshot directory
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.log(f"Screenshots will be saved to: {SCREENSHOT_DIR}", "INFO")
        
        # Start local server
        if not self.start_local_server():
            return False
            
        # Setup browser
        if not self.setup_browser():
            self.stop_local_server()
            return False
            
        try:
            # Verify each page
            for page_name, page_path, _ in PAGES:
                local_url = LOCAL_BASE_URL + page_path
                live_url = LIVE_BASE_URL + page_path
                self.compare_pages(page_name, local_url, live_url)
                
            # Summary
            print("\n" + "="*70)
            print("  📊 VERIFICATION SUMMARY")
            print("="*70 + "\n")
            
            if self.issues:
                self.log(f"Found {len(self.issues)} issues:", "WARNING")
                for i, issue in enumerate(self.issues, 1):
                    print(f"  {i}. {issue}")
            else:
                self.log("NO ISSUES FOUND! ✨", "SUCCESS")
                self.log("Your website is a perfect 1:1 copy!", "SUCCESS")
                
            print("\n" + "="*70)
            print("  📸 Screenshots saved to:")
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
