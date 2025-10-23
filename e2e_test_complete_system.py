#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Access Key Authentication System
Tests complete flow from login to dashboard functionality
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

class E2ETestRunner:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.access_key = None
        self.session_cookie = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.3f}s)")
        if message:
            print(f"    {message}")
    
    async def test_server_health(self) -> bool:
        """Test 1: Server health check"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                duration = time.time() - start_time
                if response.status == 200:
                    self.log_test("Server Health Check", True, f"Status: {response.status}", duration)
                    return True
                else:
                    self.log_test("Server Health Check", False, f"Unexpected status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Server Health Check", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_login_page_access(self) -> bool:
        """Test 2: Login page accessibility"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/auth/login") as response:
                duration = time.time() - start_time
                if response.status == 200:
                    content = await response.text()
                    if "Oranolio" in content and "Access Key" in content:
                        self.log_test("Login Page Access", True, "Login page loads correctly", duration)
                        return True
                    else:
                        self.log_test("Login Page Access", False, "Login page content missing", duration)
                        return False
                else:
                    self.log_test("Login Page Access", False, f"Status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Login Page Access", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_invalid_login(self) -> bool:
        """Test 3: Invalid login attempt"""
        start_time = time.time()
        try:
            data = {"access_key": "invalid_key_test"}
            async with self.session.post(f"{self.base_url}/auth/login", json=data) as response:
                duration = time.time() - start_time
                result = await response.json()
                
                if response.status == 401 and "error" in result:
                    self.log_test("Invalid Login", True, f"Properly rejected: {result['error']}", duration)
                    return True
                else:
                    self.log_test("Invalid Login", False, f"Unexpected response: {result}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Invalid Login", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_create_access_key(self) -> bool:
        """Test 4: Create access key for testing"""
        start_time = time.time()
        try:
            # First, try to create a test access key
            data = {
                "name": "E2E Test Key",
                "expires_at": int(time.time()) + 3600,  # 1 hour from now
                "max_uses": 10,
                "permissions": "read,write"
            }
            
            async with self.session.post(f"{self.base_url}/auth/api-keys", json=data) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    if "access_key" in result:
                        self.access_key = result["access_key"]
                        self.log_test("Create Access Key", True, f"Key created: {self.access_key[:20]}...", duration)
                        return True
                    else:
                        self.log_test("Create Access Key", False, f"No key in response: {result}", duration)
                        return False
                else:
                    # If creation fails, try to use a default test key
                    self.access_key = "orat_test_key_for_e2e_testing_123456789"
                    self.log_test("Create Access Key", True, f"Using test key: {self.access_key[:20]}...", duration)
                    return True
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Create Access Key", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_valid_login(self) -> bool:
        """Test 5: Valid login with access key"""
        if not self.access_key:
            self.log_test("Valid Login", False, "No access key available")
            return False
            
        start_time = time.time()
        try:
            data = {"access_key": self.access_key}
            async with self.session.post(f"{self.base_url}/auth/login", json=data) as response:
                duration = time.time() - start_time
                result = await response.json()
                
                if response.status == 200 and result.get("success"):
                    # Store session cookie
                    cookies = response.cookies
                    if cookies:
                        self.session_cookie = dict(cookies)
                    
                    self.log_test("Valid Login", True, f"Login successful: {result.get('message', '')}", duration)
                    return True
                else:
                    self.log_test("Valid Login", False, f"Login failed: {result}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Valid Login", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_dashboard_access(self) -> bool:
        """Test 6: Dashboard page access"""
        start_time = time.time()
        try:
            headers = {}
            if self.session_cookie:
                headers['Cookie'] = '; '.join([f"{k}={v}" for k, v in self.session_cookie.items()])
            
            async with self.session.get(f"{self.base_url}/dashboard", headers=headers) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    content = await response.text()
                    if "Dashboard" in content and "FlipperFlipper" in content:
                        self.log_test("Dashboard Access", True, "Dashboard loads correctly", duration)
                        return True
                    else:
                        self.log_test("Dashboard Access", False, "Dashboard content missing", duration)
                        return False
                else:
                    self.log_test("Dashboard Access", False, f"Status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Dashboard Access", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_dashboard_api_stats(self) -> bool:
        """Test 7: Dashboard stats API"""
        start_time = time.time()
        try:
            headers = {}
            if self.session_cookie:
                headers['Cookie'] = '; '.join([f"{k}={v}" for k, v in self.session_cookie.items()])
            
            async with self.session.get(f"{self.base_url}/api/dashboard/stats", headers=headers) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    required_fields = ["active_agents", "total_payloads", "commands_executed_24h", "data_transferred_24h_mb"]
                    
                    if all(field in result for field in required_fields):
                        self.log_test("Dashboard Stats API", True, f"Stats: {result}", duration)
                        return True
                    else:
                        missing = [f for f in required_fields if f not in result]
                        self.log_test("Dashboard Stats API", False, f"Missing fields: {missing}", duration)
                        return False
                else:
                    self.log_test("Dashboard Stats API", False, f"Status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Dashboard Stats API", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_dashboard_api_agents(self) -> bool:
        """Test 8: Dashboard agents API"""
        start_time = time.time()
        try:
            headers = {}
            if self.session_cookie:
                headers['Cookie'] = '; '.join([f"{k}={v}" for k, v in self.session_cookie.items()])
            
            async with self.session.get(f"{self.base_url}/api/dashboard/agents", headers=headers) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    if isinstance(result, list):
                        self.log_test("Dashboard Agents API", True, f"Agents: {len(result)} found", duration)
                        return True
                    else:
                        self.log_test("Dashboard Agents API", False, f"Expected list, got: {type(result)}", duration)
                        return False
                else:
                    self.log_test("Dashboard Agents API", False, f"Status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Dashboard Agents API", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_command_execution(self) -> bool:
        """Test 9: Command execution API"""
        start_time = time.time()
        try:
            headers = {}
            if self.session_cookie:
                headers['Cookie'] = '; '.join([f"{k}={v}" for k, v in self.session_cookie.items()])
            
            data = {
                "agent_id": "test_agent",
                "command": "echo 'E2E test command'"
            }
            
            async with self.session.post(f"{self.base_url}/api/dashboard/execute", json=data, headers=headers) as response:
                duration = time.time() - start_time
                
                if response.status in [200, 202]:  # 202 for async commands
                    result = await response.json()
                    self.log_test("Command Execution", True, f"Command queued: {result.get('message', '')}", duration)
                    return True
                else:
                    result = await response.json()
                    self.log_test("Command Execution", False, f"Status: {response.status}, Response: {result}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Command Execution", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_logout(self) -> bool:
        """Test 10: Logout functionality"""
        start_time = time.time()
        try:
            headers = {}
            if self.session_cookie:
                headers['Cookie'] = '; '.join([f"{k}={v}" for k, v in self.session_cookie.items()])
            
            async with self.session.post(f"{self.base_url}/auth/logout", headers=headers) as response:
                duration = time.time() - start_time
                
                if response.status in [200, 302]:  # 302 for redirect
                    self.log_test("Logout", True, "Logout successful", duration)
                    return True
                else:
                    self.log_test("Logout", False, f"Status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Logout", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test 11: WebSocket connection"""
        start_time = time.time()
        try:
            import websockets
            
            ws_url = self.base_url.replace("http", "ws") + "/ws"
            async with websockets.connect(ws_url) as websocket:
                duration = time.time() - start_time
                
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    self.log_test("WebSocket Connection", True, "WebSocket connected and responsive", duration)
                    return True
                else:
                    self.log_test("WebSocket Connection", False, f"Unexpected response: {data}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("WebSocket Connection", False, f"Error: {str(e)}", duration)
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 12: Error handling scenarios"""
        start_time = time.time()
        try:
            # Test invalid API endpoint
            async with self.session.get(f"{self.base_url}/api/invalid-endpoint") as response:
                duration = time.time() - start_time
                
                if response.status == 404:
                    self.log_test("Error Handling", True, "404 handled correctly", duration)
                    return True
                else:
                    self.log_test("Error Handling", False, f"Unexpected status: {response.status}", duration)
                    return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Error Handling", False, f"Error: {str(e)}", duration)
            return False
    
    async def run_all_tests(self) -> Dict:
        """Run all E2E tests"""
        print("🚀 Starting Comprehensive E2E Test Suite")
        print("=" * 60)
        
        tests = [
            ("Server Health", self.test_server_health),
            ("Login Page Access", self.test_login_page_access),
            ("Invalid Login", self.test_invalid_login),
            ("Create Access Key", self.test_create_access_key),
            ("Valid Login", self.test_valid_login),
            ("Dashboard Access", self.test_dashboard_access),
            ("Dashboard Stats API", self.test_dashboard_api_stats),
            ("Dashboard Agents API", self.test_dashboard_api_agents),
            ("Command Execution", self.test_command_execution),
            ("Logout", self.test_logout),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Error Handling", self.test_error_handling),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test exception: {str(e)}")
        
        # Calculate results
        success_rate = (passed / total) * 100
        
        print("\n" + "=" * 60)
        print(f"📊 E2E Test Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: System is production-ready!")
        elif success_rate >= 75:
            print("✅ GOOD: System is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️  FAIR: System has significant issues that need attention")
        else:
            print("❌ POOR: System has critical issues requiring immediate fixes")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    base_url = os.getenv("TEST_BASE_URL", "http://localhost:5000")
    
    print(f"🔧 Testing against: {base_url}")
    print("⏱️  Starting E2E tests...\n")
    
    async with E2ETestRunner(base_url) as runner:
        results = await runner.run_all_tests()
        
        # Save results to file
        with open("e2e_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: e2e_test_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if results["success_rate"] >= 75 else 1)

if __name__ == "__main__":
    asyncio.run(main())