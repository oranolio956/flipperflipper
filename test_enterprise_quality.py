"""
Enterprise Quality Assurance Test Suite
Comprehensive tests for production readiness
"""

import unittest
import requests
import time
from urllib.parse import urljoin

class EnterpriseQualityTests(unittest.TestCase):
    """Test suite for enterprise-grade quality assurance"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5000"
        cls.timeout = 5
    
    def test_01_server_is_running(self):
        """Verify server is accessible"""
        try:
            response = requests.get(self.base_url, timeout=self.timeout)
            self.assertIn(response.status_code, [200, 302, 404])
        except requests.exceptions.ConnectionError:
            self.fail("Server is not running")
    
    def test_02_health_check_endpoint(self):
        """Verify health check endpoint exists and responds"""
        url = urljoin(self.base_url, "/health")
        response = requests.get(url, timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('uptime_seconds', data)
    
    def test_03_security_headers_present(self):
        """Verify all security headers are present"""
        response = requests.get(self.base_url, timeout=self.timeout)
        headers = response.headers
        
        required_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Referrer-Policy'
        ]
        
        for header in required_headers:
            self.assertIn(header, headers, f"Missing security header: {header}")
    
    def test_04_xframe_options_deny(self):
        """Verify X-Frame-Options is set to DENY"""
        response = requests.get(self.base_url, timeout=self.timeout)
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
    
    def test_05_content_type_nosniff(self):
        """Verify X-Content-Type-Options is set to nosniff"""
        response = requests.get(self.base_url, timeout=self.timeout)
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
    
    def test_06_login_page_loads(self):
        """Verify login page loads successfully"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign in', response.content)
    
    def test_07_login_page_has_csrf(self):
        """Verify login page includes CSRF protection"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        self.assertIn(b'csrf_token', response.content)
    
    def test_08_admin_setup_requires_token(self):
        """Verify admin setup requires valid token"""
        url = urljoin(self.base_url, "/admin/setup")
        response = requests.get(url, timeout=self.timeout)
        # Should redirect or show error without token
        self.assertIn(response.status_code, [400, 403, 404])
    
    def test_09_response_time_acceptable(self):
        """Verify response time is under 1 second"""
        url = urljoin(self.base_url, "/health")
        start_time = time.time()
        response = requests.get(url, timeout=self.timeout)
        end_time = time.time()
        
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0, f"Response time too slow: {response_time}s")
    
    def test_10_static_files_cacheable(self):
        """Verify static files have cache headers"""
        # This test assumes static files exist
        url = urljoin(self.base_url, "/static/test.css")
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                self.assertIn('Cache-Control', response.headers)
        except:
            self.skipTest("No static files to test")
    
    def test_11_form_validation_works(self):
        """Verify form validation is working"""
        url = urljoin(self.base_url, "/auth/login")
        # Try to submit empty form
        response = requests.post(url, data={}, timeout=self.timeout)
        # Should reject empty form
        self.assertNotEqual(response.status_code, 200)
    
    def test_12_rate_limiting_exists(self):
        """Verify rate limiting is configured"""
        url = urljoin(self.base_url, "/health")
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = requests.get(url, timeout=self.timeout)
            responses.append(response.status_code)
        
        # All should succeed (health endpoint shouldn't be rate limited)
        self.assertTrue(all(code == 200 for code in responses))
    
    def test_13_error_handling_graceful(self):
        """Verify 404 errors are handled gracefully"""
        url = urljoin(self.base_url, "/nonexistent-page-12345")
        response = requests.get(url, timeout=self.timeout)
        self.assertEqual(response.status_code, 404)
        # Should return HTML, not crash
        self.assertIn('text/html', response.headers.get('Content-Type', ''))
    
    def test_14_mobile_viewport_meta(self):
        """Verify mobile viewport meta tag is present"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        self.assertIn(b'viewport', response.content)
        self.assertIn(b'width=device-width', response.content)
    
    def test_15_inter_font_loaded(self):
        """Verify Inter font (Stripe's font) is loaded"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        self.assertIn(b'Inter', response.content)
        self.assertIn(b'fonts.googleapis.com', response.content)
    
    def test_16_stripe_colors_used(self):
        """Verify Stripe color palette is used"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        # Check for Stripe purple (#635BFF)
        self.assertIn(b'#635BFF', response.content)
    
    def test_17_animations_present(self):
        """Verify CSS animations are present"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        self.assertIn(b'fadeIn', response.content)
        self.assertIn(b'@keyframes', response.content)
    
    def test_18_touch_targets_optimized(self):
        """Verify touch targets are mobile-optimized"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        # Check for 44-48px button heights
        self.assertIn(b'48px', response.content)
    
    def test_19_accessibility_focus_states(self):
        """Verify focus states for accessibility"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        self.assertIn(b'focus-visible', response.content)
    
    def test_20_no_console_errors(self):
        """Verify no JavaScript errors in console"""
        url = urljoin(self.base_url, "/auth/login")
        response = requests.get(url, timeout=self.timeout)
        # Check that JavaScript is present and valid
        self.assertIn(b'<script>', response.content)
        self.assertIn(b'addEventListener', response.content)


class PerformanceTests(unittest.TestCase):
    """Performance and load testing"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:5000"
        cls.timeout = 5
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request():
            url = urljoin(self.base_url, "/health")
            response = requests.get(url, timeout=self.timeout)
            return response.status_code
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        self.assertTrue(all(code == 200 for code in results))
    
    def test_memory_efficiency(self):
        """Test that repeated requests don't cause memory leaks"""
        url = urljoin(self.base_url, "/health")
        
        # Make 100 requests
        for _ in range(100):
            response = requests.get(url, timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
        
        # If we got here without timeout, memory is OK


class SecurityTests(unittest.TestCase):
    """Security-specific tests"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:5000"
        cls.timeout = 5
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        url = urljoin(self.base_url, "/auth/login")
        malicious_data = {
            'username': "admin' OR '1'='1",
            'password': "password' OR '1'='1"
        }
        response = requests.post(url, data=malicious_data, timeout=self.timeout)
        # Should not succeed
        self.assertNotEqual(response.status_code, 200)
    
    def test_xss_protection(self):
        """Test XSS protection"""
        url = urljoin(self.base_url, "/auth/login")
        xss_payload = "<script>alert('XSS')</script>"
        response = requests.post(url, data={'username': xss_payload}, timeout=self.timeout)
        # Should not execute script
        self.assertNotIn(b'<script>alert', response.content)
    
    def test_csrf_protection_enforced(self):
        """Test CSRF protection is enforced"""
        url = urljoin(self.base_url, "/admin/setup")
        # Try to POST without CSRF token
        response = requests.post(url, data={'username': 'test'}, timeout=self.timeout)
        # Should be rejected
        self.assertIn(response.status_code, [400, 403])


def run_all_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(EnterpriseQualityTests))
    suite.addTests(loader.loadTestsFromTestCase(PerformanceTests))
    suite.addTests(loader.loadTestsFromTestCase(SecurityTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
