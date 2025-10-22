#!/usr/bin/env python3
"""
Test Automated System
Test the complete automated email system
"""

import time
import requests
from automated_email_service import automated_email_service
from code_display_server import add_verification_code

def test_email_service():
    """Test the automated email service"""
    print("🧪 Testing Automated Email Service...")
    
    test_cases = [
        ("test1@example.com", "123456", "127.0.0.1"),
        ("test2@example.com", "789012", "192.168.1.1"),
        ("admin@test.com", "555555", "10.0.0.1")
    ]
    
    success_count = 0
    
    for email, code, ip in test_cases:
        print(f"📧 Sending code {code} to {email}...")
        
        success = automated_email_service.send_verification_email(email, code, ip)
        
        if success:
            print(f"✅ Success: {email}")
            success_count += 1
            
            # Add to code display
            add_verification_code(email, code, ip, "automated_test")
        else:
            print(f"❌ Failed: {email}")
        
        time.sleep(1)  # Small delay between tests
    
    print(f"\n📊 Results: {success_count}/{len(test_cases)} successful")
    return success_count == len(test_cases)

def test_webhook_data():
    """Test webhook data retrieval"""
    print("\n🔍 Checking webhook data...")
    
    try:
        data = automated_email_service.check_webhook_data()
        if data:
            print(f"✅ Webhook data retrieved: {len(data.get('data', []))} requests")
            return True
        else:
            print("⚠️ No webhook data available")
            return False
    except Exception as e:
        print(f"❌ Webhook data check failed: {e}")
        return False

def test_code_display_server():
    """Test the code display server"""
    print("\n📱 Testing code display server...")
    
    try:
        # Test if server is running
        response = requests.get('http://localhost:5001', timeout=5)
        if response.status_code == 200:
            print("✅ Code display server is running")
            return True
        else:
            print(f"❌ Code display server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Code display server is not running")
        return False
    except Exception as e:
        print(f"❌ Code display server test failed: {e}")
        return False

def test_main_application():
    """Test the main application"""
    print("\n🌐 Testing main application...")
    
    try:
        # Test if app is running
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Main application is running")
            return True
        else:
            print(f"❌ Main application returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Main application is not running")
        return False
    except Exception as e:
        print(f"❌ Main application test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AUTOMATED SYSTEM TEST SUITE")
    print("=" * 40)
    
    tests = [
        ("Email Service", test_email_service),
        ("Webhook Data", test_webhook_data),
        ("Code Display Server", test_code_display_server),
        ("Main Application", test_main_application)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print(f"\n📱 Webhook URL: {automated_email_service.get_webhook_url()}")
    print("📱 Code Display: http://localhost:5001")
    print("🌐 Main App: http://localhost:5000")

if __name__ == "__main__":
    main()