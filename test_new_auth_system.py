#!/usr/bin/env python3
"""
Comprehensive Test Suite for New Authentication System
Tests access key authentication, dashboard, and admin functionality
"""

import os
import sys
import unittest
import json
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from access_key_manager import AccessKeyManager, AuthResult, AuthErrorCode
from dashboard_data_provider import DashboardDataProvider


class TestAccessKeyManager(unittest.TestCase):
    """Test access key manager functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = 'test_access_keys.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.manager = AccessKeyManager(db_path=self.test_db)
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_generate_key(self):
        """Test key generation"""
        key, key_id = self.manager.generate_key(
            name="Test Key",
            permissions=['read', 'write']
        )
        
        self.assertTrue(key.startswith('orat_'))
        self.assertEqual(len(key), 69)  # orat_ + 64 hex chars
        self.assertIsNotNone(key_id)
    
    def test_authenticate_valid_key(self):
        """Test authentication with valid key"""
        key, key_id = self.manager.generate_key(
            name="Test Key",
            permissions=['read', 'write']
        )
        
        result = self.manager.authenticate(key)
        
        self.assertTrue(result.success)
        self.assertEqual(result.key_id, key_id)
        self.assertEqual(result.permissions, ['read', 'write'])
    
    def test_authenticate_invalid_key(self):
        """Test authentication with invalid key"""
        result = self.manager.authenticate('orat_invalid_key_12345')
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.INVALID_KEY)
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Generate key
        key, key_id = self.manager.generate_key(name="Test Key")
        
        # Try to authenticate 6 times (limit is 5)
        for i in range(6):
            result = self.manager.authenticate('orat_wrong_key')
        
        # 6th attempt should be rate limited
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.RATE_LIMITED)
    
    def test_ip_whitelist(self):
        """Test IP whitelisting"""
        key, key_id = self.manager.generate_key(
            name="Test Key",
            ip_whitelist=['192.168.1.0/24']
        )
        
        # Valid IP
        result = self.manager.authenticate(key, ip_address='192.168.1.100')
        self.assertTrue(result.success)
        
        # Invalid IP
        result = self.manager.authenticate(key, ip_address='10.0.0.1')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.IP_NOT_WHITELISTED)
    
    def test_key_expiration(self):
        """Test key expiration"""
        # Create expired key
        expired_time = datetime.now() - timedelta(hours=1)
        key, key_id = self.manager.generate_key(
            name="Expired Key",
            expires_at=expired_time
        )
        
        result = self.manager.authenticate(key)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.KEY_EXPIRED)
    
    def test_usage_limit(self):
        """Test usage limit"""
        key, key_id = self.manager.generate_key(
            name="Limited Key",
            usage_limit=2
        )
        
        # First use - should succeed
        result = self.manager.authenticate(key)
        self.assertTrue(result.success)
        
        # Second use - should succeed
        result = self.manager.authenticate(key)
        self.assertTrue(result.success)
        
        # Third use - should fail
        result = self.manager.authenticate(key)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.USAGE_LIMIT_EXCEEDED)
    
    def test_revoke_key(self):
        """Test key revocation"""
        key, key_id = self.manager.generate_key(name="Test Key")
        
        # Authenticate before revocation
        result = self.manager.authenticate(key)
        self.assertTrue(result.success)
        
        # Revoke key
        success = self.manager.revoke_key(key_id)
        self.assertTrue(success)
        
        # Authenticate after revocation
        result = self.manager.authenticate(key)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.KEY_REVOKED)
    
    def test_list_keys(self):
        """Test listing keys"""
        # Create multiple keys
        self.manager.generate_key(name="Key 1")
        self.manager.generate_key(name="Key 2")
        self.manager.generate_key(name="Key 3")
        
        keys = self.manager.list_keys()
        self.assertEqual(len(keys), 3)
    
    def test_access_link_generation(self):
        """Test access link generation"""
        link = self.manager.generate_access_link(
            expires_in=3600,
            permissions=['read']
        )
        
        self.assertIn('/auth/link?token=', link)
    
    def test_access_link_verification(self):
        """Test access link verification"""
        link = self.manager.generate_access_link(
            expires_in=3600,
            permissions=['read']
        )
        
        # Extract token from link
        token = link.split('token=')[1]
        
        # Verify token
        result = self.manager.verify_access_link(token)
        self.assertTrue(result.success)
        self.assertEqual(result.permissions, ['read'])


class TestDashboardDataProvider(unittest.TestCase):
    """Test dashboard data provider"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = 'test_stitch.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Create provider with test database
        from config import Config
        original_db = Config.APPLICATION_DIR / 'stitch.db'
        Config.APPLICATION_DIR = os.path.dirname(__file__)
        
        self.provider = DashboardDataProvider()
        self.provider.db_path = self.test_db
        self.provider._ensure_database()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        stats = self.provider.get_dashboard_stats()
        
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.total_agents, 0)
        self.assertGreaterEqual(stats.active_agents, 0)
        self.assertGreaterEqual(stats.total_commands, 0)
    
    def test_get_agents(self):
        """Test getting agents list"""
        agents = self.provider.get_agents()
        
        self.assertIsInstance(agents, list)
    
    def test_queue_command(self):
        """Test queuing a command"""
        # Add a test agent first
        import sqlite3
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agents (id, hostname, status, first_seen, last_seen)
            VALUES ('test-agent-1', 'TEST-HOST', 'active', ?, ?)
        """, (datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Queue command
        command_id = self.provider.queue_command('test-agent-1', 'whoami')
        
        self.assertIsNotNone(command_id)
        self.assertGreater(command_id, 0)
    
    def test_get_commands(self):
        """Test getting commands list"""
        commands = self.provider.get_commands(limit=10)
        
        self.assertIsInstance(commands, list)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_auth_db = 'test_access_keys_integration.db'
        self.test_data_db = 'test_stitch_integration.db'
        
        if os.path.exists(self.test_auth_db):
            os.remove(self.test_auth_db)
        if os.path.exists(self.test_data_db):
            os.remove(self.test_data_db)
        
        self.auth_manager = AccessKeyManager(db_path=self.test_auth_db)
        self.data_provider = DashboardDataProvider()
        self.data_provider.db_path = self.test_data_db
        self.data_provider._ensure_database()
    
    def tearDown(self):
        """Clean up test databases"""
        if os.path.exists(self.test_auth_db):
            os.remove(self.test_auth_db)
        if os.path.exists(self.test_data_db):
            os.remove(self.test_data_db)
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow"""
        # 1. Generate admin key
        admin_key, admin_key_id = self.auth_manager.generate_key(
            name="Admin Key",
            permissions=['read', 'write', 'admin']
        )
        
        # 2. Authenticate with admin key
        result = self.auth_manager.authenticate(admin_key)
        self.assertTrue(result.success)
        self.assertIn('admin', result.permissions)
        
        # 3. Create regular user key (as admin)
        user_key, user_key_id = self.auth_manager.generate_key(
            name="User Key",
            permissions=['read']
        )
        
        # 4. Authenticate with user key
        result = self.auth_manager.authenticate(user_key)
        self.assertTrue(result.success)
        self.assertEqual(result.permissions, ['read'])
        
        # 5. Revoke user key (as admin)
        success = self.auth_manager.revoke_key(user_key_id)
        self.assertTrue(success)
        
        # 6. Verify user key is revoked
        result = self.auth_manager.authenticate(user_key)
        self.assertFalse(result.success)
    
    def test_dashboard_with_authentication(self):
        """Test dashboard access with authentication"""
        # 1. Create key with read permissions
        key, key_id = self.auth_manager.generate_key(
            name="Dashboard Key",
            permissions=['read']
        )
        
        # 2. Authenticate
        result = self.auth_manager.authenticate(key)
        self.assertTrue(result.success)
        
        # 3. Access dashboard data
        stats = self.data_provider.get_dashboard_stats()
        self.assertIsNotNone(stats)
        
        agents = self.data_provider.get_agents()
        self.assertIsInstance(agents, list)


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Comprehensive Test Suite")
    print("=" * 60)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAccessKeyManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardDataProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
