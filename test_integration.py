#!/usr/bin/env python3
"""
Integration Test for Oranolio RAT - Elite C2 Framework
Tests that all components work together properly
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    logger.info("Testing module imports...")
    
    modules_to_test = [
        'web_app',
        'auth_utils',
        'web_app_enhancements',
        'native_protocol_bridge',
        'ssl_utils',
        'validation_schemas',
        'error_handler',
        'initialize_databases',
        'auth_routes',
        'api_routes',
        'dashboard_routes',
        'websocket_handlers',
        'command_handlers',
        'webhook_auth_routes',
        'oranolio_auth_routes',
        'c2_integration',
        'main_entry'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except Exception as e:
            failed_imports.append((module, str(e)))
            logger.error(f"✗ {module}: {e}")
    
    if failed_imports:
        logger.error(f"Failed imports: {failed_imports}")
        return False
    
    logger.info("All imports successful!")
    return True

def test_database_initialization():
    """Test database initialization"""
    logger.info("Testing database initialization...")
    
    try:
        from initialize_databases import DatabaseInitializer
        
        initializer = DatabaseInitializer()
        if not initializer.initialize_all_databases():
            logger.error("Database initialization failed")
            return False
        
        if not initializer.verify_databases():
            logger.error("Database verification failed")
            return False
        
        logger.info("✓ Database initialization successful")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def test_ssl_certificates():
    """Test SSL certificate generation"""
    logger.info("Testing SSL certificate generation...")
    
    try:
        from ssl_utils import CertificateManager
        
        cert_manager = CertificateManager()
        success, message = cert_manager.generate_self_signed_certificate()
        
        if not success:
            logger.error(f"SSL certificate generation failed: {message}")
            return False
        
        logger.info("✓ SSL certificate generation successful")
        return True
        
    except Exception as e:
        logger.error(f"SSL certificate generation failed: {e}")
        return False

def test_c2_integration():
    """Test C2 system integration"""
    logger.info("Testing C2 system integration...")
    
    try:
        from c2_integration import get_stitch_server, get_elite_executor, get_system_status
        
        # Test stitch server
        server = get_stitch_server()
        if not server:
            logger.error("Failed to get stitch server")
            return False
        
        # Test elite executor
        executor = get_elite_executor()
        if not executor:
            logger.error("Failed to get elite executor")
            return False
        
        # Test system status
        status = get_system_status()
        if not status:
            logger.error("Failed to get system status")
            return False
        
        logger.info("✓ C2 integration successful")
        return True
        
    except Exception as e:
        logger.error(f"C2 integration failed: {e}")
        return False

def test_authentication():
    """Test authentication system"""
    logger.info("Testing authentication system...")
    
    try:
        from auth_utils import auth_manager
        
        # Test user creation
        user = auth_manager.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        if not user:
            logger.error("Failed to create test user")
            return False
        
        # Test authentication
        auth_user = auth_manager.authenticate_user(
            "test@example.com",
            "testpass123",
            "127.0.0.1",
            "test-agent"
        )
        
        if not auth_user:
            logger.error("Failed to authenticate test user")
            return False
        
        logger.info("✓ Authentication system successful")
        return True
        
    except Exception as e:
        logger.error(f"Authentication system failed: {e}")
        return False

def test_web_app_creation():
    """Test web application creation"""
    logger.info("Testing web application creation...")
    
    try:
        from web_app import create_app
        
        app = create_app()
        if not app:
            logger.error("Failed to create Flask app")
            return False
        
        # Test that app has required blueprints
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        required_blueprints = ['auth', 'api', 'dashboard']
        
        for required in required_blueprints:
            if required not in blueprint_names:
                logger.error(f"Missing blueprint: {required}")
                return False
        
        logger.info("✓ Web application creation successful")
        return True
        
    except Exception as e:
        logger.error(f"Web application creation failed: {e}")
        return False

def test_validation_schemas():
    """Test input validation"""
    logger.info("Testing input validation...")
    
    try:
        from validation_schemas import validate_input, ValidationManager
        
        # Test email validation
        from validation_schemas import validate_email
        result = validate_email('test@example.com')
        if not result:
            logger.error("Email validation failed")
            return False
        
        # Test invalid email
        result = validate_email('invalid-email')
        if result:
            logger.error("Invalid email was accepted")
            return False
        
        logger.info("✓ Input validation successful")
        return True
        
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        return False

def test_error_handling():
    """Test error handling system"""
    logger.info("Testing error handling system...")
    
    try:
        from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
        
        # Test error handling
        context = ErrorContext(
            user_id="test_user",
            ip_address="127.0.0.1",
            additional_data={'test': True}
        )
        
        error_handler.handle_error(
            Exception("Test error"),
            context,
            ErrorSeverity.LOW,
            ErrorCategory.APPLICATION
        )
        
        logger.info("✓ Error handling system successful")
        return True
        
    except Exception as e:
        logger.error(f"Error handling system failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    logger.info("Starting Oranolio RAT Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Initialization", test_database_initialization),
        ("SSL Certificates", test_ssl_certificates),
        ("C2 Integration", test_c2_integration),
        ("Authentication", test_authentication),
        ("Web App Creation", test_web_app_creation),
        ("Input Validation", test_validation_schemas),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                failed += 1
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info("INTEGRATION TEST RESULTS")
    logger.info("=" * 50)
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! System is ready for deployment.")
        return True
    else:
        logger.error(f"❌ {failed} tests failed. Please fix the issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)