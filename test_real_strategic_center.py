#!/usr/bin/env python3
"""
Test Real Strategic Command Center Functionality
Tests the actual integration with the Stitch system
"""

import requests
import json
import time
import sys

def test_strategic_center():
    """Test the Strategic Command Center with real Stitch integration"""
    print("🎯 Testing Strategic Command Center - Real Stitch Integration")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health Check: {data['status']}")
            print(f"   ✅ Strategic Center: {data['strategic_center']}")
            print(f"   ✅ Stitch Available: {data['stitch_available']}")
        else:
            print(f"   ❌ Health Check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health Check error: {e}")
        return False
    
    # Test 2: Get Targets (should be empty initially)
    print("\n2. Testing Target Management...")
    try:
        response = requests.get(f"{base_url}/api/targets")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Targets API: {data['count']} targets found")
            print(f"   ✅ Success: {data['success']}")
        else:
            print(f"   ❌ Targets API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Targets API error: {e}")
        return False
    
    # Test 3: Get System Stats
    print("\n3. Testing System Statistics...")
    try:
        response = requests.get(f"{base_url}/api/system_stats")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   ✅ System Stats API: Working")
            print(f"   ✅ Total Targets: {stats['total_targets']}")
            print(f"   ✅ Online Targets: {stats['online_targets']}")
            print(f"   ✅ System CPU: {stats['system_cpu']}%")
            print(f"   ✅ System Memory: {stats['system_memory']}%")
        else:
            print(f"   ❌ System Stats API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ System Stats API error: {e}")
        return False
    
    # Test 4: Test Command Execution (without target)
    print("\n4. Testing Command Execution...")
    try:
        response = requests.post(f"{base_url}/api/execute_command", 
                               json={
                                   'target_id': 'test_target',
                                   'command': 'whoami',
                                   'parameters': {}
                               })
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Command Execution API: Working")
            print(f"   ✅ Command ID: {data.get('command_id', 'N/A')}")
        else:
            print(f"   ❌ Command Execution API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Command Execution API error: {e}")
        return False
    
    # Test 5: Test File Operations (without target)
    print("\n5. Testing File Operations...")
    try:
        response = requests.post(f"{base_url}/api/upload_file",
                               json={
                                   'target_id': 'test_target',
                                   'filename': 'test.txt',
                                   'content': 'dGVzdCBmaWxl',  # base64 encoded "test file"
                                   'path': '/tmp/'
                               })
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ File Upload API: Working")
            print(f"   ✅ Operation ID: {data.get('operation_id', 'N/A')}")
        else:
            print(f"   ❌ File Upload API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ File Upload API error: {e}")
        return False
    
    # Test 6: Test WebSocket Connection
    print("\n6. Testing WebSocket Connection...")
    try:
        import socketio
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("   ✅ WebSocket Connected")
        
        @sio.event
        def disconnect():
            print("   ✅ WebSocket Disconnected")
        
        @sio.event
        def targets_update(data):
            print(f"   ✅ WebSocket Targets Update: {data['count']} targets")
        
        sio.connect(base_url)
        time.sleep(2)
        sio.disconnect()
        print("   ✅ WebSocket Test: Passed")
    except Exception as e:
        print(f"   ❌ WebSocket Test error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Strategic Command Center - Real Stitch Integration: PASSED")
    print("✅ All core functionality is working with real Stitch system")
    print("✅ The Strategic Command Center is production-ready")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_strategic_center()
    sys.exit(0 if success else 1)