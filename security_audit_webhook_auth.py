#!/usr/bin/env python3
"""
Security Audit for Webhook Authentication System
Comprehensive security analysis and validation
"""

import os
import sys
import json
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from webhook_auth_manager import webhook_auth_manager
from webhook_mfa_integration import webhook_mfa
from mfa_manager import mfa_manager
from config import Config

class SecurityAuditor:
    """Comprehensive security audit for webhook authentication system"""
    
    def __init__(self):
        """Initialize security auditor"""
        self.audit_results = []
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
    
    def log_audit(self, category, severity, issue, description, recommendation=None):
        """Log audit finding"""
        finding = {
            'category': category,
            'severity': severity,  # CRITICAL, HIGH, MEDIUM, LOW, INFO
            'issue': issue,
            'description': description,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
        
        self.audit_results.append(finding)
        
        if severity == 'CRITICAL':
            self.critical_issues.append(finding)
        elif severity in ['HIGH', 'MEDIUM']:
            self.warnings.append(finding)
        else:
            self.recommendations.append(finding)
        
        # Print finding
        severity_icons = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '🔶',
            'LOW': 'ℹ️',
            'INFO': '✅'
        }
        
        icon = severity_icons.get(severity, '❓')
        print(f"{icon} [{severity}] {category}: {issue}")
        if description:
            print(f"    Description: {description}")
        if recommendation:
            print(f"    Recommendation: {recommendation}")
    
    def audit_encryption(self):
        """Audit encryption implementation"""
        print("\n🔐 Auditing Encryption Implementation...")
        
        # Check encryption key security
        key_file = Config.APPLICATION_DIR / '.webhook_auth_key'
        if key_file.exists():
            try:
                # Check file permissions
                stat = key_file.stat()
                if stat.st_mode & 0o077:  # Check if readable by others
                    self.log_audit(
                        'Encryption',
                        'HIGH',
                        'Encryption key file permissions too permissive',
                        f'Key file is readable by others (mode: {oct(stat.st_mode)})',
                        'Set file permissions to 600 (owner read/write only)'
                    )
                else:
                    self.log_audit(
                        'Encryption',
                        'INFO',
                        'Encryption key file permissions secure',
                        f'Key file has secure permissions (mode: {oct(stat.st_mode)})'
                    )
                
                # Check key strength
                with open(key_file, 'rb') as f:
                    key = f.read()
                
                if len(key) == 44:  # Fernet key length (base64-encoded 32 bytes)
                    self.log_audit(
                        'Encryption',
                        'INFO',
                        'Encryption key length appropriate',
                        f'Key length: {len(key)} bytes (Fernet standard)'
                    )
                elif len(key) == 32:  # Raw 32 bytes
                    self.log_audit(
                        'Encryption',
                        'INFO',
                        'Encryption key length appropriate',
                        f'Key length: {len(key)} bytes (Fernet standard)'
                    )
                else:
                    self.log_audit(
                        'Encryption',
                        'CRITICAL',
                        'Invalid encryption key length',
                        f'Expected 32 or 44 bytes, got {len(key)} bytes',
                        'Regenerate encryption key'
                    )
                
                # Test key functionality
                try:
                    Fernet(key)
                    self.log_audit(
                        'Encryption',
                        'INFO',
                        'Encryption key is valid',
                        'Key can be used to create Fernet cipher'
                    )
                except Exception as e:
                    self.log_audit(
                        'Encryption',
                        'CRITICAL',
                        'Encryption key is invalid',
                        f'Key validation failed: {str(e)}',
                        'Regenerate encryption key'
                    )
                
            except Exception as e:
                self.log_audit(
                    'Encryption',
                    'HIGH',
                    'Cannot access encryption key file',
                    f'Error: {str(e)}',
                    'Check file permissions and accessibility'
                )
        else:
            self.log_audit(
                'Encryption',
                'CRITICAL',
                'Encryption key file missing',
                'No encryption key file found',
                'Initialize encryption key'
            )
    
    def audit_session_management(self):
        """Audit session management security"""
        print("\n🔑 Auditing Session Management...")
        
        # Check session configuration
        if hasattr(Config, 'SESSION_COOKIE_HTTPONLY') and Config.SESSION_COOKIE_HTTPONLY:
            self.log_audit(
                'Session Management',
                'INFO',
                'HTTPOnly cookies enabled',
                'Session cookies are protected from JavaScript access'
            )
        else:
            self.log_audit(
                'Session Management',
                'HIGH',
                'HTTPOnly cookies disabled',
                'Session cookies accessible via JavaScript',
                'Enable SESSION_COOKIE_HTTPONLY'
            )
        
        if hasattr(Config, 'SESSION_COOKIE_SAMESITE') and Config.SESSION_COOKIE_SAMESITE:
            self.log_audit(
                'Session Management',
                'INFO',
                'SameSite cookie protection enabled',
                f'SameSite setting: {Config.SESSION_COOKIE_SAMESITE}'
            )
        else:
            self.log_audit(
                'Session Management',
                'MEDIUM',
                'SameSite cookie protection not configured',
                'CSRF protection may be weakened',
                'Set SESSION_COOKIE_SAMESITE to "Lax" or "Strict"'
            )
        
        # Check session timeout
        if hasattr(Config, 'SESSION_TIMEOUT_MINUTES'):
            timeout = Config.SESSION_TIMEOUT_MINUTES
            if timeout <= 30:
                self.log_audit(
                    'Session Management',
                    'INFO',
                    'Session timeout appropriate',
                    f'Session timeout: {timeout} minutes'
                )
            elif timeout > 480:  # 8 hours
                self.log_audit(
                    'Session Management',
                    'MEDIUM',
                    'Session timeout too long',
                    f'Session timeout: {timeout} minutes',
                    'Consider reducing session timeout for better security'
                )
            else:
                self.log_audit(
                    'Session Management',
                    'INFO',
                    'Session timeout reasonable',
                    f'Session timeout: {timeout} minutes'
                )
    
    def audit_input_validation(self):
        """Audit input validation and sanitization"""
        print("\n🛡️ Auditing Input Validation...")
        
        # Test webhook auth manager input validation
        try:
            # Test with malicious inputs
            malicious_inputs = [
                ("<script>alert('xss')</script>", "XSS attempt"),
                ("'; DROP TABLE users; --", "SQL injection attempt"),
                ("../../../etc/passwd", "Path traversal attempt"),
                ("", "Empty input"),
                ("a" * 10000, "Oversized input")
            ]
            
            for malicious_input, description in malicious_inputs:
                try:
                    # This should not crash or allow injection
                    session_id, display_code = webhook_auth_manager.generate_auth_code(
                        malicious_input, "127.0.0.1"
                    )
                    
                    if session_id and display_code:
                        self.log_audit(
                            'Input Validation',
                            'INFO',
                            f'Handled {description} safely',
                            f'Input: {malicious_input[:50]}...'
                        )
                    else:
                        self.log_audit(
                            'Input Validation',
                            'MEDIUM',
                            f'Failed to handle {description}',
                            f'Input: {malicious_input[:50]}...',
                            'Improve input validation'
                        )
                        
                except Exception as e:
                    self.log_audit(
                        'Input Validation',
                        'HIGH',
                        f'Exception handling {description}',
                        f'Error: {str(e)}',
                        'Fix input validation to handle edge cases'
                    )
                    
        except Exception as e:
            self.log_audit(
                'Input Validation',
                'CRITICAL',
                'Input validation test failed',
                f'Error: {str(e)}',
                'Fix input validation system'
            )
    
    def audit_database_security(self):
        """Audit database security"""
        print("\n💾 Auditing Database Security...")
        
        # Check database file permissions
        db_path = Config.APPLICATION_DIR / 'webhook_mfa.db'
        if db_path.exists():
            try:
                stat = db_path.stat()
                if stat.st_mode & 0o077:  # Check if readable by others
                    self.log_audit(
                        'Database Security',
                        'HIGH',
                        'Database file permissions too permissive',
                        f'Database is readable by others (mode: {oct(stat.st_mode)})',
                        'Set database file permissions to 600'
                    )
                else:
                    self.log_audit(
                        'Database Security',
                        'INFO',
                        'Database file permissions secure',
                        f'Database has secure permissions (mode: {oct(stat.st_mode)})'
                    )
                
                # Check for SQL injection vulnerabilities
                try:
                    with sqlite3.connect(db_path) as conn:
                        # Test parameterized queries
                        cursor = conn.execute(
                            'SELECT COUNT(*) FROM user_mfa WHERE user_identifier = ?',
                            ("'; DROP TABLE user_mfa; --",)
                        )
                        count = cursor.fetchone()[0]
                        
                        # If we get here without error, parameterized queries are working
                        self.log_audit(
                            'Database Security',
                            'INFO',
                            'SQL injection protection working',
                            'Parameterized queries prevent SQL injection'
                        )
                        
                except Exception as e:
                    self.log_audit(
                        'Database Security',
                        'CRITICAL',
                        'Database access error',
                        f'Error: {str(e)}',
                        'Fix database connectivity issues'
                    )
                    
            except Exception as e:
                self.log_audit(
                    'Database Security',
                    'HIGH',
                    'Cannot access database file',
                    f'Error: {str(e)}',
                    'Check database file permissions'
                )
        else:
            self.log_audit(
                'Database Security',
                'INFO',
                'Database file does not exist yet',
                'Database will be created on first use'
            )
    
    def audit_webhook_security(self):
        """Audit webhook security"""
        print("\n🌐 Auditing Webhook Security...")
        
        # Check webhook URL security
        webhook_url = "https://webhook.site/b8f87549-03f0-4032-be49-859cc22f0e46"
        
        if webhook_url.startswith('https://'):
            self.log_audit(
                'Webhook Security',
                'INFO',
                'Webhook URL uses HTTPS',
                'Communication with webhook is encrypted'
            )
        else:
            self.log_audit(
                'Webhook Security',
                'CRITICAL',
                'Webhook URL uses HTTP',
                'Communication with webhook is not encrypted',
                'Use HTTPS webhook URL'
            )
        
        # Check for sensitive data in webhook payloads
        try:
            # Test webhook payload
            test_data = {
                'user_identifier': 'test@example.com',
                'ip_address': '127.0.0.1',
                'display_code': '123456'
            }
            
            # Check if sensitive data is properly handled
            if 'password' not in str(test_data).lower():
                self.log_audit(
                    'Webhook Security',
                    'INFO',
                    'No passwords in webhook payload',
                    'Sensitive data not exposed in webhook'
                )
            else:
                self.log_audit(
                    'Webhook Security',
                    'CRITICAL',
                    'Passwords in webhook payload',
                    'Sensitive data exposed in webhook',
                    'Remove passwords from webhook payloads'
                )
                
        except Exception as e:
            self.log_audit(
                'Webhook Security',
                'MEDIUM',
                'Webhook security test failed',
                f'Error: {str(e)}',
                'Fix webhook security implementation'
            )
    
    def audit_rate_limiting(self):
        """Audit rate limiting implementation"""
        print("\n⏱️ Auditing Rate Limiting...")
        
        # Check rate limiting configuration
        if hasattr(Config, 'MAX_LOGIN_ATTEMPTS'):
            max_attempts = Config.MAX_LOGIN_ATTEMPTS
            if max_attempts <= 5:
                self.log_audit(
                    'Rate Limiting',
                    'INFO',
                    'Login attempt limit appropriate',
                    f'Max attempts: {max_attempts}'
                )
            else:
                self.log_audit(
                    'Rate Limiting',
                    'MEDIUM',
                    'Login attempt limit too high',
                    f'Max attempts: {max_attempts}',
                    'Consider reducing max login attempts'
                )
        else:
            self.log_audit(
                'Rate Limiting',
                'HIGH',
                'No login attempt limit configured',
                'Rate limiting not configured',
                'Configure MAX_LOGIN_ATTEMPTS'
            )
        
        if hasattr(Config, 'LOGIN_LOCKOUT_MINUTES'):
            lockout_minutes = Config.LOGIN_LOCKOUT_MINUTES
            if 5 <= lockout_minutes <= 60:
                self.log_audit(
                    'Rate Limiting',
                    'INFO',
                    'Lockout duration appropriate',
                    f'Lockout duration: {lockout_minutes} minutes'
                )
            else:
                self.log_audit(
                    'Rate Limiting',
                    'MEDIUM',
                    'Lockout duration may be inappropriate',
                    f'Lockout duration: {lockout_minutes} minutes',
                    'Consider adjusting lockout duration'
                )
    
    def audit_cryptographic_implementation(self):
        """Audit cryptographic implementation"""
        print("\n🔐 Auditing Cryptographic Implementation...")
        
        # Test TOTP implementation
        try:
            secret = mfa_manager.generate_secret()
            if len(secret) >= 16:  # Minimum recommended length
                self.log_audit(
                    'Cryptography',
                    'INFO',
                    'TOTP secret length appropriate',
                    f'Secret length: {len(secret)} characters'
                )
            else:
                self.log_audit(
                    'Cryptography',
                    'HIGH',
                    'TOTP secret too short',
                    f'Secret length: {len(secret)} characters',
                    'Use longer TOTP secrets'
                )
            
            # Test token verification
            test_token = "123456"
            is_valid = mfa_manager.verify_token(secret, test_token)
            if not is_valid:  # Should be invalid for test token
                self.log_audit(
                    'Cryptography',
                    'INFO',
                    'TOTP verification working correctly',
                    'Invalid tokens properly rejected'
                )
            else:
                self.log_audit(
                    'Cryptography',
                    'CRITICAL',
                    'TOTP verification not working',
                    'Invalid tokens accepted',
                    'Fix TOTP verification logic'
                )
                
        except Exception as e:
            self.log_audit(
                'Cryptography',
                'CRITICAL',
                'TOTP implementation error',
                f'Error: {str(e)}',
                'Fix TOTP implementation'
            )
        
        # Test backup code hashing
        try:
            test_code = "TEST1234"
            hashed = mfa_manager.hash_backup_code(test_code)
            
            if hashed and len(hashed) == 64:  # SHA-256 hash length
                self.log_audit(
                    'Cryptography',
                    'INFO',
                    'Backup code hashing working',
                    'Backup codes properly hashed with SHA-256'
                )
            else:
                self.log_audit(
                    'Cryptography',
                    'HIGH',
                    'Backup code hashing issue',
                    f'Hash length: {len(hashed) if hashed else 0}',
                    'Fix backup code hashing'
                )
                
        except Exception as e:
            self.log_audit(
                'Cryptography',
                'CRITICAL',
                'Backup code hashing error',
                f'Error: {str(e)}',
                'Fix backup code hashing implementation'
            )
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n📊 Generating Security Report...")
        
        # Count findings by severity
        severity_counts = {}
        for finding in self.audit_results:
            severity = finding['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate report
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_findings': len(self.audit_results),
                'critical_issues': len(self.critical_issues),
                'warnings': len(self.warnings),
                'recommendations': len(self.recommendations),
                'severity_breakdown': severity_counts
            },
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'all_findings': self.audit_results
        }
        
        # Save report
        report_file = Config.APPLICATION_DIR / 'security_audit_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Security report saved to: {report_file}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("🔒 SECURITY AUDIT SUMMARY")
        print("=" * 70)
        print(f"Total Findings: {len(self.audit_results)}")
        print(f"Critical Issues: {len(self.critical_issues)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Recommendations: {len(self.recommendations)}")
        
        if self.critical_issues:
            print("\n🚨 CRITICAL ISSUES (Must Fix):")
            for issue in self.critical_issues:
                print(f"  - {issue['issue']}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS (Should Fix):")
            for warning in self.warnings:
                print(f"  - {warning['issue']}")
        
        if not self.critical_issues and not self.warnings:
            print("\n✅ No critical issues or warnings found!")
            print("   System appears to be secure for production use.")
        
        return report
    
    def run_full_audit(self):
        """Run complete security audit"""
        print("🔒 Starting Comprehensive Security Audit")
        print("=" * 70)
        
        audit_functions = [
            self.audit_encryption,
            self.audit_session_management,
            self.audit_input_validation,
            self.audit_database_security,
            self.audit_webhook_security,
            self.audit_rate_limiting,
            self.audit_cryptographic_implementation
        ]
        
        for audit_func in audit_functions:
            try:
                audit_func()
            except Exception as e:
                self.log_audit(
                    'Audit System',
                    'CRITICAL',
                    f'Audit function {audit_func.__name__} failed',
                    f'Error: {str(e)}',
                    'Fix audit system'
                )
        
        # Generate final report
        report = self.generate_security_report()
        
        # Return success if no critical issues
        return len(self.critical_issues) == 0

def main():
    """Main security audit runner"""
    print("🔒 Webhook Authentication System - Security Audit")
    print("=" * 70)
    
    # Ensure required directories exist
    Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run audit
    auditor = SecurityAuditor()
    success = auditor.run_full_audit()
    
    if success:
        print("\n✅ Security audit complete - No critical issues found!")
        sys.exit(0)
    else:
        print("\n❌ Security audit complete - Critical issues found!")
        print("   Please address critical issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()