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
        key_id, key = self.manager.generate_access_key(
            name="Test Key",
            created_by="test_user",
            permissions=['read', 'write']
        )
        
        self.assertTrue(key.startswith('orat_'))
        self.assertGreater(len(key), 10)
        self.assertIsNotNone(key_id)
    
    def test_authenticate_valid_key(self):
        """Test authentication with valid key"""
        key_id, key = self.manager.generate_access_key(
            name="Test Key",
            created_by="test_user",
            permissions=['read', 'write']
        )
        
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        
        self.assertTrue(result.success)
        self.assertEqual(result.key_id, key_id)
        self.assertEqual(result.permissions, ['read', 'write'])
    
    def test_authenticate_invalid_key(self):
        """Test authentication with invalid key"""
        result = self.manager.authenticate('orat_invalid_key_12345', ip_address='127.0.0.1')
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.KEY_NOT_FOUND)
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Generate key
        key_id, key = self.manager.generate_access_key(
            name="Test Key",
            created_by="test_user"
        )
        
        # Try to authenticate 6 times (limit is 5)
        for i in range(6):
            result = self.manager.authenticate('orat_wrong_key', ip_address='127.0.0.1')
        
        # 6th attempt should be rate limited
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.RATE_LIMITED)
    
    def test_ip_whitelist(self):
        """Test IP whitelisting"""
        key_id, key = self.manager.generate_access_key(
            name="Test Key",
            created_by="test_user",
            ip_whitelist=['192.168.1.0/24']
        )
        
        # Valid IP
        result = self.manager.authenticate(key, ip_address='192.168.1.100')
        self.assertTrue(result.success)
        
        # Invalid IP
        result = self.manager.authenticate(key, ip_address='10.0.0.1')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.IP_DENIED)
    
    def test_key_expiration(self):
        """Test key expiration"""
        # Create expired key (expires in -1 days = already expired)
        key_id, key = self.manager.generate_access_key(
            name="Expired Key",
            created_by="test_user",
            expires_in_days=-1
        )
        
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.KEY_EXPIRED)
    
    def test_usage_limit(self):
        """Test usage limit"""
        key_id, key = self.manager.generate_access_key(
            name="Limited Key",
            created_by="test_user",
            max_uses=2
        )
        
        # First use - should succeed
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        self.assertTrue(result.success)
        
        # Second use - should succeed
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        self.assertTrue(result.success)
        
        # Third use - should fail
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.USAGE_LIMIT)
    
    def test_revoke_key(self):
        """Test key revocation"""
        key_id, key = self.manager.generate_access_key(
            name="Test Key",
            created_by="test_user"
        )
        
        # Authenticate before revocation
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        self.assertTrue(result.success)
        
        # Revoke key
        success = self.manager.revoke_key(key_id)
        self.assertTrue(success)
        
        # Authenticate after revocation
        result = self.manager.authenticate(key, ip_address='127.0.0.1')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, AuthErrorCode.KEY_REVOKED)
    
    def test_list_keys(self):
        """Test listing keys"""
        # Create multiple keys
        self.manager.generate_access_key(name="Key 1", created_by="test_user")
        self.manager.generate_access_key(name="Key 2", created_by="test_user")
        self.manager.generate_access_key(name="Key 3", created_by="test_user")
        
        keys = self.manager.list_keys()
        self.assertEqual(len(keys), 3)
    



class TestDashboardDataProvider(unittest.TestCase):
    """Test dashboard data provider"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = 'test_stitch.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Create provider with test database
        from pathlib import Path
        self.provider = DashboardDataProvider()
        self.provider.db_path = Path(self.test_db)
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
    
    def test_get_agent_by_id(self):
        """Test getting agent by ID"""
        # Add a test agent first
        import sqlite3
        conn = sqlite3.connect(str(self.provider.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agents (id, hostname, status, first_seen, last_seen)
            VALUES ('test-agent-1', 'TEST-HOST', 'active', ?, ?)
        """, (datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Get agent
        agent = self.provider.get_agent_by_id('test-agent-1')
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.id, 'test-agent-1')
        self.assertEqual(agent.hostname, 'TEST-HOST')
    
    def test_get_recent_commands(self):
        """Test getting recent commands list"""
        commands = self.provider.get_recent_commands(limit=10)
        
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
        
        from pathlib import Path
        self.auth_manager = AccessKeyManager(db_path=self.test_auth_db)
        self.data_provider = DashboardDataProvider()
        self.data_provider.db_path = Path(self.test_data_db)
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
        admin_key_id, admin_key = self.auth_manager.generate_access_key(
            name="Admin Key",
            created_by="admin",
            permissions=['read', 'write', 'admin']
        )
        
        # 2. Authenticate with admin key
        result = self.auth_manager.authenticate(admin_key, ip_address='127.0.0.1')
        self.assertTrue(result.success)
        self.assertIn('admin', result.permissions)
        
        # 3. Create regular user key (as admin)
        user_key_id, user_key = self.auth_manager.generate_access_key(
            name="User Key",
            created_by="admin",
            permissions=['read']
        )
        
        # 4. Authenticate with user key
        result = self.auth_manager.authenticate(user_key, ip_address='127.0.0.1')
        self.assertTrue(result.success)
        self.assertEqual(result.permissions, ['read'])
        
        # 5. Revoke user key (as admin)
        success = self.auth_manager.revoke_key(user_key_id)
        self.assertTrue(success)
        
        # 6. Verify user key is revoked
        result = self.auth_manager.authenticate(user_key, ip_address='127.0.0.1')
        self.assertFalse(result.success)
    
    def test_dashboard_with_authentication(self):
        """Test dashboard access with authentication"""
        # 1. Create key with read permissions
        key_id, key = self.auth_manager.generate_access_key(
            name="Dashboard Key",
            created_by="admin",
            permissions=['read']
        )
        
        # 2. Authenticate
        result = self.auth_manager.authenticate(key, ip_address='127.0.0.1')
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
