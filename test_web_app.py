#!/usr/bin/env python3
"""
Test Web Application Loading
"""

import sys
import os

def test_web_app_loading():
    """Test if web app loads without errors"""
    print("🌐 Testing Web Application Loading")
    print("=" * 40)
    
    try:
        # Test importing the web app
        print("📦 Importing web_app_real...")
        
        # Set required environment variables to avoid warnings
        os.environ['STITCH_ADMIN_USER'] = 'admin'
        os.environ['STITCH_ADMIN_PASSWORD'] = 'password123'
        
        import web_app_real
        print("✅ Web app imported successfully")
        
        # Check MFA status
        if hasattr(web_app_real, 'MFA_ENABLED'):
            print(f"✅ MFA_ENABLED: {web_app_real.MFA_ENABLED}")
        else:
            print("❌ MFA_ENABLED not found")
            return False
        
        # Check if Flask app exists
        if hasattr(web_app_real, 'app'):
            print("✅ Flask app instance found")
        else:
            print("❌ Flask app instance not found")
            return False
        
        # Check routes
        routes = []
        for rule in web_app_real.app.url_map.iter_rules():
            routes.append(rule.rule)
        
        required_routes = ['/login', '/email-login', '/verify-email', '/mfa/setup', '/mfa/verify', '/mfa/backup-codes']
        
        for route in required_routes:
            if route in routes:
                print(f"✅ Route {route} exists")
            else:
                print(f"❌ Route {route} missing")
                return False
        
        print("✅ Web application loaded successfully with all routes")
        return True
        
    except Exception as e:
        print(f"❌ Web app loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_web_app_loading()
    if success:
        print("\n🏆 Web application test passed!")
    else:
        print("\n💥 Web application test failed!")
        sys.exit(1)