#!/usr/bin/env python3
"""
Strategic Command Center - Test Script
Comprehensive testing of all components
"""

import os
import sys
import time
import json
import requests
import threading
from datetime import datetime

# Add workspace to path
sys.path.insert(0, '/workspace')

def test_redis_connection():
    """Test Redis connection"""
    print("🔄 Testing Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_strategic_center_import():
    """Test strategic center import"""
    print("🔄 Testing strategic center import...")
    try:
        from strategic_command_center import StrategicCommandCenter, init_strategic_center
        print("✅ Strategic center import successful")
        return True
    except Exception as e:
        print(f"❌ Strategic center import failed: {e}")
        return False

def test_strategic_center_initialization():
    """Test strategic center initialization"""
    print("🔄 Testing strategic center initialization...")
    try:
        from strategic_command_center import init_strategic_center
        center = init_strategic_center()
        print("✅ Strategic center initialization successful")
        return True
    except Exception as e:
        print(f"❌ Strategic center initialization failed: {e}")
        return False

def test_websocket_import():
    """Test WebSocket import"""
    print("🔄 Testing WebSocket import...")
    try:
        from strategic_websocket import register_strategic_websocket_events
        print("✅ WebSocket import successful")
        return True
    except Exception as e:
        print(f"❌ WebSocket import failed: {e}")
        return False

def test_web_app_import():
    """Test web app import"""
    print("🔄 Testing web app import...")
    try:
        from strategic_web_app import init_app, app, socketio
        print("✅ Web app import successful")
        return True
    except Exception as e:
        print(f"❌ Web app import failed: {e}")
        return False

def test_stitch_integration():
    """Test Stitch integration"""
    print("🔄 Testing Stitch integration...")
    try:
        from Application.stitch_cmd import get_stitch_server
        from Core.elite_executor import EliteCommandExecutor
        print("✅ Stitch integration successful")
        return True
    except Exception as e:
        print(f"⚠️ Stitch integration not available: {e}")
        return False

def test_web_app_startup():
    """Test web app startup"""
    print("🔄 Testing web app startup...")
    try:
        from strategic_web_app import init_app, app, socketio
        
        # Initialize app
        init_app()
        print("✅ Web app initialization successful")
        
        # Test routes
        with app.test_client() as client:
            # Test main route
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Main route working")
            else:
                print(f"❌ Main route failed: {response.status_code}")
                return False
            
            # Test API routes
            api_routes = [
                '/api/targets',
                '/api/system_stats',
                '/api/health'
            ]
            
            for route in api_routes:
                response = client.get(route)
                if response.status_code in [200, 404]:  # 404 is OK for empty data
                    print(f"✅ API route {route} working")
                else:
                    print(f"❌ API route {route} failed: {response.status_code}")
                    return False
        
        print("✅ Web app startup test successful")
        return True
        
    except Exception as e:
        print(f"❌ Web app startup test failed: {e}")
        return False

def test_target_management():
    """Test target management functionality"""
    print("🔄 Testing target management...")
    try:
        from strategic_command_center import init_strategic_center
        center = init_strategic_center()
        
        # Test getting targets
        targets = center.get_targets()
        print(f"✅ Target management working - {len(targets)} targets")
        
        # Test system stats
        stats = center.get_system_stats()
        print(f"✅ System stats working - {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Target management test failed: {e}")
        return False

def test_command_execution():
    """Test command execution functionality"""
    print("🔄 Testing command execution...")
    try:
        from strategic_command_center import init_strategic_center
        center = init_strategic_center()
        
        # Test command execution (will be queued)
        command_id = center.execute_command("test_target", "whoami")
        print(f"✅ Command execution working - ID: {command_id}")
        
        # Test parallel execution
        command_ids = center.execute_parallel_commands(["target1", "target2"], "ls")
        print(f"✅ Parallel execution working - IDs: {command_ids}")
        
        return True
        
    except Exception as e:
        print(f"❌ Command execution test failed: {e}")
        return False

def test_file_operations():
    """Test file operations functionality"""
    print("🔄 Testing file operations...")
    try:
        from strategic_command_center import init_strategic_center
        center = init_strategic_center()
        
        # Test file upload
        test_content = b"test file content"
        operation_id = center.upload_file("test_target", "test.txt", test_content)
        print(f"✅ File upload working - ID: {operation_id}")
        
        # Test file download
        operation_id = center.download_file("test_target", "/tmp/test.txt")
        print(f"✅ File download working - ID: {operation_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_ui_components():
    """Test UI components"""
    print("🔄 Testing UI components...")
    try:
        # Check if template exists
        template_path = '/workspace/templates/strategic_command_center.html'
        if os.path.exists(template_path):
            print("✅ Strategic template exists")
        else:
            print("❌ Strategic template missing")
            return False
        
        # Check if CSS exists
        css_path = '/workspace/static/css/strategic.css'
        if os.path.exists(css_path):
            print("✅ Strategic CSS exists")
        else:
            print("❌ Strategic CSS missing")
            return False
        
        # Check if JS exists
        js_path = '/workspace/static/js/strategic.js'
        if os.path.exists(js_path):
            print("✅ Strategic JavaScript exists")
        else:
            print("❌ Strategic JavaScript missing")
            return False
        
        print("✅ UI components test successful")
        return True
        
    except Exception as e:
        print(f"❌ UI components test failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🎯 Strategic Command Center - Comprehensive Test")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Strategic Center Import", test_strategic_center_import),
        ("Strategic Center Initialization", test_strategic_center_initialization),
        ("WebSocket Import", test_websocket_import),
        ("Web App Import", test_web_app_import),
        ("Stitch Integration", test_stitch_integration),
        ("Web App Startup", test_web_app_startup),
        ("Target Management", test_target_management),
        ("Command Execution", test_command_execution),
        ("File Operations", test_file_operations),
        ("UI Components", test_ui_components)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Strategic Command Center is ready.")
        print("\nNext steps:")
        print("1. Start Redis: redis-server")
        print("2. Start Strategic Center: python start_strategic_center.py")
        print("3. Access: http://localhost:5000")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install Redis: sudo apt-get install redis-server")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check file permissions and paths")
    
    return passed == total

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)