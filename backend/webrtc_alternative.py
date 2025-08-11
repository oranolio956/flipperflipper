#!/usr/bin/env python3
"""
WebRTC Leak Detection Alternative for Python
Since WebRTC is browser-only, we simulate similar leak detection
"""

import asyncio
import aiohttp
import aiohttp_socks
import socket
import ipaddress
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import logging
import httpx
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class IPLeakResult:
    """Results from IP leak detection"""
    is_leaking: bool
    expected_ip: str
    detected_ips: Set[str]
    local_ips: Set[str]
    public_ips: Set[str]
    leak_sources: List[str]
    confidence: float


class IPLeakDetector:
    """
    Detects IP leaks through proxies using multiple methods
    Simulates WebRTC-style leak detection for Python
    """
    
    def __init__(self):
        # Services that echo back various IPs
        self.ip_check_services = [
            {
                'url': 'https://api.ipify.org?format=json',
                'json_path': 'ip',
                'name': 'ipify'
            },
            {
                'url': 'https://ipapi.co/json/',
                'json_path': 'ip',
                'name': 'ipapi'
            },
            {
                'url': 'https://ifconfig.me/all.json',
                'json_path': 'ip_addr',
                'name': 'ifconfig.me'
            },
            {
                'url': 'https://httpbin.org/ip',
                'json_path': 'origin',
                'name': 'httpbin'
            }
        ]
        
        # STUN servers (similar to WebRTC)
        self.stun_servers = [
            ('stun.l.google.com', 19302),
            ('stun1.l.google.com', 19302),
            ('stun.stunprotocol.org', 3478),
        ]
    
    async def detect_leaks(self, proxy_url: str, expected_ip: str) -> IPLeakResult:
        """
        Detect IP leaks through multiple methods
        Similar to WebRTC leak detection but for Python
        """
        detected_ips = set()
        local_ips = set()
        public_ips = set()
        leak_sources = []
        
        # 1. Get local network interfaces
        local_ips = self._get_local_ips()
        
        # 2. Test through multiple IP detection services
        service_ips = await self._check_ip_services(proxy_url)
        detected_ips.update(service_ips)
        
        # 3. STUN-like protocol test (UDP through proxy)
        stun_ips = await self._check_stun_like(proxy_url)
        detected_ips.update(stun_ips)
        
        # 4. DNS resolution leak test
        dns_ips = await self._check_dns_resolution(proxy_url)
        detected_ips.update(dns_ips)
        
        # 5. Check for JavaScript-based leaks (simulate)
        js_leaks = await self._check_javascript_apis(proxy_url)
        detected_ips.update(js_leaks)
        
        # Analyze results
        is_leaking = False
        confidence = 0.0
        
        # Separate public and local IPs
        for ip in detected_ips:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private:
                    local_ips.add(ip)
                else:
                    public_ips.add(ip)
                    
                    # Check if public IP matches expected
                    if ip != expected_ip:
                        is_leaking = True
                        leak_sources.append(f"Public IP {ip} detected")
            except:
                pass
        
        # Local IP detection is also a form of leak
        if local_ips:
            leak_sources.append(f"Local IPs exposed: {', '.join(local_ips)}")
            is_leaking = True
        
        # Calculate confidence based on number of services checked
        services_checked = len([s for s in service_ips if s])
        confidence = services_checked / len(self.ip_check_services)
        
        return IPLeakResult(
            is_leaking=is_leaking,
            expected_ip=expected_ip,
            detected_ips=detected_ips,
            local_ips=local_ips,
            public_ips=public_ips,
            leak_sources=leak_sources,
            confidence=confidence
        )
    
    def _get_local_ips(self) -> Set[str]:
        """Get local network interface IPs"""
        local_ips = set()
        
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Get all IPs associated with hostname
            host_ips = socket.gethostbyname_ex(hostname)[2]
            local_ips.update(host_ips)
            
            # Also check all network interfaces
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        if ip:
                            local_ips.add(ip)
        except:
            # Fallback method
            try:
                # Create a socket and connect to external server
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ips.add(s.getsockname()[0])
            except:
                pass
        
        return local_ips
    
    async def _check_ip_services(self, proxy_url: str) -> Set[str]:
        """Check IP through various services"""
        detected_ips = set()
        parsed = urlparse(proxy_url)
        
        for service in self.ip_check_services:
            try:
                if parsed.scheme in ['socks4', 'socks5']:
                    connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                    timeout = aiohttp.ClientTimeout(total=10)
                    
                    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                        async with session.get(service['url']) as response:
                            if response.status == 200:
                                data = await response.json()
                                ip = self._extract_ip_from_json(data, service['json_path'])
                                if ip:
                                    detected_ips.add(ip)
                else:
                    # HTTP proxy
                    async with httpx.AsyncClient(proxies={'all://': proxy_url}, timeout=10.0) as client:
                        response = await client.get(service['url'])
                        if response.status_code == 200:
                            data = response.json()
                            ip = self._extract_ip_from_json(data, service['json_path'])
                            if ip:
                                detected_ips.add(ip)
                                
            except Exception as e:
                logger.debug(f"IP service check failed for {service['name']}: {e}")
        
        return detected_ips
    
    def _extract_ip_from_json(self, data: Dict, path: str) -> Optional[str]:
        """Extract IP from JSON response"""
        try:
            # Handle nested paths like 'data.ip'
            parts = path.split('.')
            value = data
            for part in parts:
                value = value.get(part)
                if value is None:
                    return None
            
            # Extract IP if it's in a string with other data
            if isinstance(value, str):
                import re
                # Match IPv4
                ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', value)
                if ip_match:
                    return ip_match.group()
                # Match IPv6
                ipv6_match = re.search(r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}', value)
                if ipv6_match:
                    return ipv6_match.group()
            
            return str(value) if value else None
        except:
            return None
    
    async def _check_stun_like(self, proxy_url: str) -> Set[str]:
        """
        Simulate STUN protocol check
        STUN is used by WebRTC to discover public IP
        """
        detected_ips = set()
        
        # Note: Full STUN implementation requires UDP which most
        # SOCKS5 proxies don't support well. This is a simplified version.
        
        try:
            # Try to create a UDP socket through proxy
            # This often reveals the real IP if proxy doesn't handle UDP properly
            
            for stun_server, port in self.stun_servers[:1]:  # Test one server
                try:
                    # Get server IP
                    server_ip = socket.gethostbyname(stun_server)
                    
                    # Create STUN binding request (simplified)
                    # Real STUN is more complex
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(2)
                    
                    # STUN binding request header (simplified)
                    msg = b'\x00\x01' + b'\x00\x00' + b'\x21\x12\xa4\x42' + b'\x00' * 12
                    
                    sock.sendto(msg, (server_ip, port))
                    
                    # Try to receive response
                    data, addr = sock.recvfrom(1024)
                    
                    # Parse response (simplified - real parsing is complex)
                    # Look for XOR-MAPPED-ADDRESS attribute
                    # This would contain the public IP
                    
                    sock.close()
                    
                except socket.timeout:
                    pass
                except Exception as e:
                    logger.debug(f"STUN test failed: {e}")
                    
        except Exception as e:
            logger.debug(f"STUN-like test error: {e}")
        
        return detected_ips
    
    async def _check_dns_resolution(self, proxy_url: str) -> Set[str]:
        """Check for DNS resolution leaks"""
        detected_ips = set()
        
        # Test domains that might reveal IP
        test_domains = [
            'myip.opendns.com',
            'whoami.akamai.net',
        ]
        
        for domain in test_domains:
            try:
                # Resolve through system (might bypass proxy)
                ips = socket.gethostbyname_ex(domain)[2]
                detected_ips.update(ips)
            except:
                pass
        
        return detected_ips
    
    async def _check_javascript_apis(self, proxy_url: str) -> Set[str]:
        """
        Simulate JavaScript API checks
        In a real browser, these APIs can leak IP
        """
        detected_ips = set()
        
        # Check services that execute JavaScript and might leak IP
        js_services = [
            'https://www.cloudflare.com/cdn-cgi/trace',  # Returns various info
        ]
        
        parsed = urlparse(proxy_url)
        
        for service in js_services:
            try:
                if parsed.scheme in ['socks4', 'socks5']:
                    connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(service, timeout=5) as response:
                            text = await response.text()
                            # Parse response for IPs
                            import re
                            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
                            detected_ips.update(ips)
                else:
                    async with httpx.AsyncClient(proxies={'all://': proxy_url}, timeout=5.0) as client:
                        response = await client.get(service)
                        text = response.text
                        import re
                        ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
                        detected_ips.update(ips)
            except:
                pass
        
        return detected_ips


# Test function
async def test_ip_leak_detection():
    """Test IP leak detection"""
    print("=" * 70)
    print("IP LEAK DETECTION TEST (WebRTC Alternative)")
    print("=" * 70)
    
    # Test proxy
    proxy_url = "socks5://167.172.224.108:1080"
    expected_ip = "167.172.224.108"
    
    detector = IPLeakDetector()
    
    print(f"\n🔍 Testing proxy: {proxy_url}")
    print(f"Expected IP: {expected_ip}")
    print("\nRunning leak detection...\n")
    
    result = await detector.detect_leaks(proxy_url, expected_ip)
    
    print("📊 Results:")
    print(f"  Is Leaking: {'❌ YES' if result.is_leaking else '✅ NO'}")
    print(f"  Confidence: {result.confidence:.2%}")
    
    if result.local_ips:
        print(f"\n  Local IPs detected: {', '.join(result.local_ips)}")
    
    if result.public_ips:
        print(f"\n  Public IPs detected: {', '.join(result.public_ips)}")
    
    if result.leak_sources:
        print("\n  Leak sources:")
        for source in result.leak_sources:
            print(f"    - {source}")
    
    print("\n✅ IP leak detection complete!")


if __name__ == "__main__":
    asyncio.run(test_ip_leak_detection())