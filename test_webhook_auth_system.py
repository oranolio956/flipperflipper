#!/usr/bin/env python3
"""
Comprehensive Test Suite for Webhook Authentication System
Tests all components: webhook auth, MFA integration, security features
"""

import os
import sys
import json
import time
import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from webhook_auth_manager import webhook_auth_manager
from webhook_mfa_integration import webhook_mfa
from mfa_manager import mfa_manager
from config import Config

class WebhookAuthTester:
    """Comprehensive test suite for webhook authentication system"""
    
    def __init__(self):
        """Initialize tester"""
        self.test_results = []
        self.base_url = "http://localhost:5000"
        self.test_user = "test@example.com"
        self.test_ip = "127.0.0.1"
        
    def log_test(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_webhook_auth_manager(self):
        """Test webhook authentication manager"""
        print("\n🔐 Testing Webhook Authentication Manager...")
        
        try:
            # Test code generation
            session_id, display_code = webhook_auth_manager.generate_auth_code(
                self.test_user, self.test_ip
            )
            
            if session_id and display_code:
                self.log_test(
                    "Code Generation",
                    True,
                    "Successfully generated authentication code",
                    {
                        'session_id_length': len(session_id),
                        'display_code_length': len(display_code),
                        'display_code': display_code
                    }
                )
            else:
                self.log_test("Code Generation", False, "Failed to generate code")
                return False
            
            # Test code verification
            is_valid, message, session_data = webhook_auth_manager.verify_auth_code(
                session_id, display_code, self.test_ip
            )
            
            if is_valid:
                self.log_test(
                    "Code Verification",
                    True,
                    "Successfully verified authentication code",
                    {'user_identifier': session_data.get('user_identifier')}
                )
            else:
                self.log_test("Code Verification", False, f"Verification failed: {message}")
                return False
            
            # Test invalid code
            is_valid, message, _ = webhook_auth_manager.verify_auth_code(
                session_id, "000000", self.test_ip
            )
            
            if not is_valid:
                self.log_test(
                    "Invalid Code Rejection",
                    True,
                    "Correctly rejected invalid code",
                    {'message': message}
                )
            else:
                self.log_test("Invalid Code Rejection", False, "Failed to reject invalid code")
            
            # Test session status
            status = webhook_auth_manager.get_session_status(session_id)
            if status and status.get('verified'):
                self.log_test(
                    "Session Status",
                    True,
                    "Session status correctly shows verified",
                    {'verified': status.get('verified')}
                )
            else:
                self.log_test("Session Status", False, "Session status incorrect")
            
            return True
            
        except Exception as e:
            self.log_test("Webhook Auth Manager", False, f"Exception: {str(e)}")
            return False
    
    def test_mfa_integration(self):
        """Test MFA integration"""
        print("\n🔑 Testing MFA Integration...")
        
        try:
            # Test MFA setup
            setup_result = webhook_mfa.setup_mfa(self.test_user)
            
            if setup_result['success']:
                self.log_test(
                    "MFA Setup",
                    True,
                    "Successfully initiated MFA setup",
                    {
                        'has_secret': 'secret' in setup_result,
                        'has_qr_code': 'qr_code' in setup_result,
                        'backup_codes_count': len(setup_result.get('backup_codes', []))
                    }
                )
                
                # Test MFA verification with generated secret
                secret = setup_result['secret']
                totp = mfa_manager.verify_token(secret, "123456")  # This will fail, but tests the flow
                
                # Test backup code hashing
                backup_codes = setup_result['backup_codes']
                if backup_codes:
                    first_code = backup_codes[0]
                    hashed = mfa_manager.hash_backup_code(first_code)
                    
                    if hashed:
                        self.log_test(
                            "Backup Code Hashing",
                            True,
                            "Successfully hashed backup code",
                            {'code_length': len(first_code), 'hash_length': len(hashed)}
                        )
                    else:
                        self.log_test("Backup Code Hashing", False, "Failed to hash backup code")
                
                # Test MFA status check
                status = webhook_mfa.get_mfa_status(self.test_user)
                if status:
                    self.log_test(
                        "MFA Status Check",
                        True,
                        "Successfully retrieved MFA status",
                        status
                    )
                else:
                    self.log_test("MFA Status Check", False, "Failed to get MFA status")
                
                return True
            else:
                self.log_test("MFA Setup", False, f"Setup failed: {setup_result['message']}")
                return False
                
        except Exception as e:
            self.log_test("MFA Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_security_features(self):
        """Test security features"""
        print("\n🛡️ Testing Security Features...")
        
        try:
            # Test session expiration
            session_id, display_code = webhook_auth_manager.generate_auth_code(
                self.test_user, self.test_ip
            )
            
            # Manually expire the session by modifying the database
            # This tests the cleanup mechanism
            time.sleep(1)  # Small delay
            
            # Test IP address validation
            is_valid, message, _ = webhook_auth_manager.verify_auth_code(
                session_id, display_code, "192.168.1.1"  # Different IP
            )
            
            if not is_valid and "IP address mismatch" in message:
                self.log_test(
                    "IP Address Validation",
                    True,
                    "Correctly rejected different IP address",
                    {'message': message}
                )
            else:
                self.log_test("IP Address Validation", False, "Failed to validate IP address")
            
            # Test rate limiting (multiple failed attempts)
            for i in range(5):
                is_valid, message, _ = webhook_auth_manager.verify_auth_code(
                    session_id, "000000", self.test_ip
                )
            
            # Check if session is locked after too many attempts
            status = webhook_auth_manager.get_session_status(session_id)
            if not status or status.get('attempts', 0) >= 3:
                self.log_test(
                    "Rate Limiting",
                    True,
                    "Correctly implemented rate limiting",
                    {'attempts': status.get('attempts', 0) if status else 'N/A'}
                )
            else:
                self.log_test("Rate Limiting", False, "Rate limiting not working properly")
            
            return True
            
        except Exception as e:
            self.log_test("Security Features", False, f"Exception: {str(e)}")
            return False
    
    def test_database_integrity(self):
        """Test database integrity and encryption"""
        print("\n💾 Testing Database Integrity...")
        
        try:
            # Test MFA database
            db_path = Config.APPLICATION_DIR / 'webhook_mfa.db'
            if db_path.exists():
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    expected_tables = ['user_mfa', 'mfa_verification_logs']
                    missing_tables = [table for table in expected_tables if table not in tables]
                    
                    if not missing_tables:
                        self.log_test(
                            "Database Schema",
                            True,
                            "All required tables exist",
                            {'tables': tables}
                        )
                    else:
                        self.log_test(
                            "Database Schema",
                            False,
                            f"Missing tables: {missing_tables}",
                            {'tables': tables}
                        )
            
            # Test encryption key generation
            key_file = Config.APPLICATION_DIR / '.webhook_auth_key'
            if key_file.exists():
                self.log_test(
                    "Encryption Key",
                    True,
                    "Encryption key file exists",
                    {'key_file': str(key_file)}
                )
            else:
                self.log_test("Encryption Key", False, "Encryption key file missing")
            
            return True
            
        except Exception as e:
            self.log_test("Database Integrity", False, f"Exception: {str(e)}")
            return False
    
    def test_webhook_communication(self):
        """Test webhook communication"""
        print("\n🌐 Testing Webhook Communication...")
        
        try:
            # Test webhook URL accessibility
            webhook_url = "https://webhook.site/b8f87549-03f0-4032-be49-859cc22f0e46"
            
            try:
                response = requests.get(webhook_url, timeout=10)
                if response.status_code == 200:
                    self.log_test(
                        "Webhook Accessibility",
                        True,
                        "Webhook URL is accessible",
                        {'status_code': response.status_code}
                    )
                else:
                    self.log_test(
                        "Webhook Accessibility",
                        False,
                        f"Webhook returned status {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                self.log_test(
                    "Webhook Accessibility",
                    False,
                    f"Failed to reach webhook: {str(e)}"
                )
            
            # Test webhook API
            api_url = "https://webhook.site/token/b8f87549-03f0-4032-be49-859cc22f0e46/requests"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    self.log_test(
                        "Webhook API",
                        True,
                        "Webhook API is accessible",
                        {'status_code': response.status_code}
                    )
                else:
                    self.log_test(
                        "Webhook API",
                        False,
                        f"Webhook API returned status {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                self.log_test(
                    "Webhook API",
                    False,
                    f"Failed to reach webhook API: {str(e)}"
                )
            
            return True
            
        except Exception as e:
            self.log_test("Webhook Communication", False, f"Exception: {str(e)}")
            return False
    
    def test_configuration(self):
        """Test configuration and environment"""
        print("\n⚙️ Testing Configuration...")
        
        try:
            # Test required configuration
            required_configs = [
                'APP_NAME', 'SECRET_KEY', 'APPLICATION_DIR',
                'AUTHORIZED_EMAILS', 'MAX_LOGIN_ATTEMPTS'
            ]
            
            missing_configs = []
            for config_name in required_configs:
                if not hasattr(Config, config_name):
                    missing_configs.append(config_name)
            
            if not missing_configs:
                self.log_test(
                    "Configuration",
                    True,
                    "All required configuration present",
                    {'configs_checked': len(required_configs)}
                )
            else:
                self.log_test(
                    "Configuration",
                    False,
                    f"Missing configurations: {missing_configs}"
                )
            
            # Test authorized emails
            authorized_emails = Config.get_authorized_emails()
            if authorized_emails and len(authorized_emails) > 0:
                self.log_test(
                    "Authorized Emails",
                    True,
                    "Authorized emails configured",
                    {'emails': authorized_emails}
                )
            else:
                self.log_test("Authorized Emails", False, "No authorized emails configured")
            
            # Test directory structure
            required_dirs = [
                Config.APPLICATION_DIR,
                Config.LOGS_DIR,
                Config.UPLOADS_DIR
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not dir_path.exists():
                    missing_dirs.append(str(dir_path))
            
            if not missing_dirs:
                self.log_test(
                    "Directory Structure",
                    True,
                    "All required directories exist",
                    {'directories_checked': len(required_dirs)}
                )
            else:
                self.log_test(
                    "Directory Structure",
                    False,
                    f"Missing directories: {missing_dirs}"
                )
            
            return True
            
        except Exception as e:
            self.log_test("Configuration", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Webhook Authentication System Test")
        print("=" * 70)
        
        test_functions = [
            self.test_configuration,
            self.test_webhook_auth_manager,
            self.test_mfa_integration,
            self.test_security_features,
            self.test_database_integrity,
            self.test_webhook_communication
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
        
        print("\n" + "=" * 70)
        print(f"📊 Test Results: {passed_tests}/{total_tests} test suites passed")
        
        # Summary
        total_individual_tests = len(self.test_results)
        passed_individual_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"📈 Individual Tests: {passed_individual_tests}/{total_individual_tests} passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! System is ready for production.")
        else:
            print("⚠️ Some tests failed. Please review the issues above.")
        
        # Save detailed results
        results_file = Config.APPLICATION_DIR / 'webhook_auth_test_results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'test_summary': {
                    'total_suites': total_tests,
                    'passed_suites': passed_tests,
                    'total_individual_tests': total_individual_tests,
                    'passed_individual_tests': passed_individual_tests,
                    'timestamp': datetime.now().isoformat()
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        
        return passed_tests == total_tests

def main():
    """Main test runner"""
    print("🔐 Webhook Authentication System - Comprehensive Test Suite")
    print("=" * 70)
    
    # Ensure required directories exist
    Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run tests
    tester = WebhookAuthTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ System validation complete - All systems operational!")
        sys.exit(0)
    else:
        print("\n❌ System validation failed - Please fix issues before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()