#!/usr/bin/env python3
"""
Production Proxy Testing Backend
Real proxy validation with SOCKS5/HTTP support
"""

import asyncio
import aiohttp
import aiohttp_socks
import socket
import struct
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import aiodns
import geoip2.database
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import httpx
from concurrent.futures import ThreadPoolExecutor
import psutil
import hashlib

# Import our proxy discovery module
from proxy_sources import ProxySourceManager, ProxyEntry as DiscoveredProxy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProxyResult:
    """Proxy test result with all metadata"""
    ip: str
    port: int
    protocol: str
    working: bool
    anonymity_level: str  # Elite, Anonymous, Transparent
    response_time: int
    country: str
    city: str
    isp: str
    asn: str
    is_mobile: bool
    is_datacenter: bool
    fraud_score: int
    last_checked: datetime
    error: Optional[str] = None
    
    # Advanced features
    supports_https: bool = False
    supports_cookies: bool = False
    supports_referer: bool = False
    supports_user_agent: bool = False
    ssl_fingerprint: Optional[str] = None
    exit_ip: Optional[str] = None
    dns_leak: bool = False
    webrtc_leak: bool = False
    timezone: Optional[str] = None
    
    # Performance metrics
    download_speed: Optional[float] = None  # MB/s
    upload_speed: Optional[float] = None    # MB/s
    latency_stability: Optional[float] = None  # Standard deviation
    
    # Rotation detection
    is_rotating: bool = False
    rotation_interval: Optional[int] = None
    ip_pool_size: Optional[int] = None

class ProxyTester:
    """Production-grade proxy tester with advanced features"""
    
    def __init__(self):
        self.app = FastAPI()
        self.setup_cors()
        self.setup_routes()
        
        # Redis for caching and pub/sub
        self.redis = None
        
        # Proxy discovery manager
        self.proxy_source_manager = ProxySourceManager()
        
        # GeoIP database (you'll need to download this)
        try:
            self.geoip = geoip2.database.Reader('/workspace/backend/GeoLite2-City.mmdb')
        except:
            self.geoip = None
            logger.warning("GeoIP database not found - location features disabled")
        
        # Thread pool for CPU-intensive tasks
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Judge servers for anonymity testing
        self.judge_servers = [
            "http://azenv.net/",
            "http://www.proxy-listen.de/azenv.php",
            "http://proxyjudge.us/",
            "https://httpbin.org/headers",
            "http://mojeip.net.pl/asdfa/azenv.php"
        ]
        
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Mobile carrier detection patterns
        self.mobile_carriers = {
            'verizon': ['verizon', 'vzw', 'cellco'],
            'att': ['at&t', 'att-', 'cingular', 'at&t mobility'],
            'tmobile': ['t-mobile', 'tmobile', 'metropcs'],
            'sprint': ['sprint', 'boost'],
            'vodafone': ['vodafone'],
            'orange': ['orange'],
            'china_mobile': ['china mobile', 'cmcc'],
            'airtel': ['airtel', 'bharti'],
            'telefonica': ['telefonica', 'movistar', 'o2'],
            'mtn': ['mtn'],
            'telkom': ['telkom'],
            'etisalat': ['etisalat'],
            'zain': ['zain'],
            'rogers': ['rogers'],
            'telus': ['telus'],
            'bell': ['bell mobility']
        }
    
    def setup_cors(self):
        """Configure CORS for production"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure your domains in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.on_event("startup")
        async def startup():
            self.redis = await redis.create_redis_pool('redis://localhost')
        
        @self.app.on_event("shutdown")
        async def shutdown():
            if self.redis:
                self.redis.close()
                await self.redis.wait_closed()
        
        @self.app.get("/")
        async def root():
            return {"message": "Proxy Testing API v2.0", "status": "operational"}
        
        @self.app.post("/test/single")
        async def test_single_proxy(ip: str, port: int, protocol: str = "socks5"):
            """Test a single proxy"""
            result = await self.test_proxy(ip, port, protocol)
            return asdict(result)
        
        @self.app.post("/test/batch")
        async def test_batch_proxies(proxies: List[Dict[str, any]]):
            """Test multiple proxies concurrently"""
            tasks = []
            for proxy in proxies:
                task = self.test_proxy(
                    proxy['ip'], 
                    proxy['port'], 
                    proxy.get('protocol', 'socks5')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [asdict(r) if isinstance(r, ProxyResult) else str(r) for r in results]
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle incoming messages if needed
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
        
        @self.app.get("/discover")
        async def discover_proxies(force_refresh: bool = False):
            """Discover proxies from multiple sources"""
            try:
                discovered = await self.proxy_source_manager.get_proxies(force_refresh)
                
                # Convert to list and add discovery metadata
                proxy_list = []
                for proxy in discovered:
                    proxy_dict = {
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'protocol': proxy.protocol,
                        'country': proxy.country,
                        'source': proxy.source,
                        'last_seen': proxy.last_seen.isoformat()
                    }
                    proxy_list.append(proxy_dict)
                
                # Sort by protocol and source
                proxy_list.sort(key=lambda x: (x['protocol'], x['source']))
                
                return {
                    'status': 'success',
                    'count': len(proxy_list),
                    'proxies': proxy_list,
                    'sources': self.proxy_source_manager.get_source_statistics()
                }
            except Exception as e:
                logger.error(f"Discovery error: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e)
                }
        
        @self.app.post("/discover/test-all")
        async def discover_and_test():
            """Discover proxies and test them all"""
            try:
                # First discover
                discovered = await self.proxy_source_manager.get_proxies()
                
                # Convert to test format
                proxies_to_test = []
                for proxy in discovered:
                    proxies_to_test.append({
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'protocol': proxy.protocol or 'unknown'
                    })
                
                # Broadcast discovery complete
                await self._broadcast_discovery_status(len(proxies_to_test))
                
                # Test in batches
                batch_size = 50
                all_results = []
                
                for i in range(0, len(proxies_to_test), batch_size):
                    batch = proxies_to_test[i:i + batch_size]
                    
                    # Test batch
                    tasks = []
                    for proxy in batch:
                        task = self.test_proxy(
                            proxy['ip'],
                            proxy['port'],
                            proxy['protocol']
                        )
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for result in results:
                        if isinstance(result, ProxyResult):
                            all_results.append(asdict(result))
                        else:
                            logger.error(f"Test error: {str(result)}")
                    
                    # Small delay between batches
                    await asyncio.sleep(0.5)
                
                # Filter working proxies
                working = [r for r in all_results if r['working']]
                
                return {
                    'status': 'success',
                    'discovered': len(proxies_to_test),
                    'tested': len(all_results),
                    'working': len(working),
                    'results': all_results
                }
                
            except Exception as e:
                logger.error(f"Discover and test error: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e)
                }
    
    async def test_proxy(self, ip: str, port: int, protocol: str) -> ProxyResult:
        """Comprehensively test a proxy"""
        start_time = time.time()
        
        # Initialize result
        result = ProxyResult(
            ip=ip,
            port=port,
            protocol=protocol,
            working=False,
            anonymity_level="Unknown",
            response_time=0,
            country="Unknown",
            city="Unknown",
            isp="Unknown",
            asn="Unknown",
            is_mobile=False,
            is_datacenter=False,
            fraud_score=0,
            last_checked=datetime.utcnow()
        )
        
        try:
            # 1. Test basic connectivity
            if protocol.lower() in ['socks5', 'socks4']:
                is_working = await self._test_socks_proxy(ip, port, protocol)
            else:
                is_working = await self._test_http_proxy(ip, port)
            
            if not is_working:
                result.working = False
                result.error = "Connection failed"
                return result
            
            result.working = True
            result.response_time = int((time.time() - start_time) * 1000)
            
            # 2. Test anonymity level
            anonymity_data = await self._test_anonymity(ip, port, protocol)
            result.anonymity_level = anonymity_data['level']
            result.exit_ip = anonymity_data.get('exit_ip')
            
            # 3. Get geolocation and ISP info
            geo_data = await self._get_geo_info(result.exit_ip or ip)
            result.country = geo_data.get('country', 'Unknown')
            result.city = geo_data.get('city', 'Unknown')
            result.isp = geo_data.get('isp', 'Unknown')
            result.asn = geo_data.get('asn', 'Unknown')
            result.timezone = geo_data.get('timezone')
            
            # 4. Detect mobile carrier
            result.is_mobile = self._is_mobile_carrier(result.isp)
            
            # 5. Detect datacenter
            result.is_datacenter = self._is_datacenter(result.isp, result.asn)
            
            # 6. Calculate fraud score
            result.fraud_score = self._calculate_fraud_score(result)
            
            # 7. Advanced tests (if proxy is working)
            if result.working:
                # Test HTTPS support
                result.supports_https = await self._test_https_support(ip, port, protocol)
                
                # Test header support
                header_support = await self._test_header_support(ip, port, protocol)
                result.supports_cookies = header_support.get('cookies', False)
                result.supports_referer = header_support.get('referer', False)
                result.supports_user_agent = header_support.get('user_agent', False)
                
                # Test for leaks
                leak_data = await self._test_leaks(ip, port, protocol)
                result.dns_leak = leak_data.get('dns_leak', False)
                result.webrtc_leak = leak_data.get('webrtc_leak', False)
                
                # Test speed (optional - takes time)
                # speed_data = await self._test_speed(ip, port, protocol)
                # result.download_speed = speed_data.get('download')
                # result.upload_speed = speed_data.get('upload')
                
                # Check for rotation
                rotation_data = await self._check_rotation(ip, port, protocol)
                result.is_rotating = rotation_data.get('is_rotating', False)
                result.rotation_interval = rotation_data.get('interval')
                result.ip_pool_size = rotation_data.get('pool_size')
            
            # 8. Cache result
            await self._cache_result(result)
            
            # 9. Broadcast to WebSocket clients
            await self._broadcast_result(result)
            
        except Exception as e:
            logger.error(f"Error testing proxy {ip}:{port} - {str(e)}")
            result.error = str(e)
        
        return result
    
    async def _test_socks_proxy(self, ip: str, port: int, protocol: str) -> bool:
        """Test SOCKS4/5 proxy connectivity"""
        proxy_url = f"{protocol}://{ip}:{port}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get('http://httpbin.org/ip') as response:
                    if response.status == 200:
                        data = await response.json()
                        return 'origin' in data
            return False
        except:
            return False
    
    async def _test_http_proxy(self, ip: str, port: int) -> bool:
        """Test HTTP/HTTPS proxy connectivity"""
        proxy_url = f"http://{ip}:{port}"
        
        try:
            async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=10.0) as client:
                response = await client.get("http://httpbin.org/ip")
                return response.status_code == 200
        except:
            return False
    
    async def _test_anonymity(self, ip: str, port: int, protocol: str) -> Dict:
        """Test proxy anonymity level"""
        headers_found = {
            'real_ip_headers': [],
            'proxy_headers': [],
            'exit_ip': None
        }
        
        proxy_url = f"{protocol}://{ip}:{port}"
        
        for judge in self.judge_servers:
            try:
                if protocol in ['socks4', 'socks5']:
                    connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(judge, timeout=10) as response:
                            text = await response.text()
                            headers_found = self._parse_judge_response(text)
                            break
                else:
                    async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=10.0) as client:
                        response = await client.get(judge)
                        headers_found = self._parse_judge_response(response.text)
                        break
            except:
                continue
        
        # Determine anonymity level
        if not headers_found['real_ip_headers'] and not headers_found['proxy_headers']:
            level = "Elite"
        elif not headers_found['real_ip_headers'] and headers_found['proxy_headers']:
            level = "Anonymous"
        else:
            level = "Transparent"
        
        return {
            'level': level,
            'exit_ip': headers_found.get('exit_ip'),
            'headers': headers_found
        }
    
    def _parse_judge_response(self, response_text: str) -> Dict:
        """Parse judge server response for headers"""
        headers_found = {
            'real_ip_headers': [],
            'proxy_headers': [],
            'exit_ip': None
        }
        
        # Look for common header patterns
        real_ip_headers = [
            'X-Real-IP', 'X-Forwarded-For', 'Client-IP', 
            'X-Client-IP', 'X-Originating-IP', 'CF-Connecting-IP'
        ]
        
        proxy_headers = [
            'Via', 'X-Proxy-ID', 'X-Forwarded-Server',
            'X-Forwarded-Host', 'Proxy-Connection'
        ]
        
        lines = response_text.lower().split('\n')
        for line in lines:
            for header in real_ip_headers:
                if header.lower() in line:
                    headers_found['real_ip_headers'].append(header)
            
            for header in proxy_headers:
                if header.lower() in line:
                    headers_found['proxy_headers'].append(header)
            
            # Try to extract exit IP
            if 'remote_addr' in line or 'your ip' in line:
                import re
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                if ip_match:
                    headers_found['exit_ip'] = ip_match.group(1)
        
        return headers_found
    
    async def _get_geo_info(self, ip: str) -> Dict:
        """Get geolocation and ISP information"""
        geo_data = {}
        
        # Try local GeoIP database first
        if self.geoip:
            try:
                response = self.geoip.city(ip)
                geo_data = {
                    'country': response.country.name,
                    'city': response.city.name,
                    'timezone': response.location.time_zone,
                    'latitude': response.location.latitude,
                    'longitude': response.location.longitude
                }
            except:
                pass
        
        # Fallback to API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={'fields': 'status,country,city,isp,org,as,mobile,proxy,hosting,timezone,lat,lon'}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        geo_data.update({
                            'country': data.get('country', 'Unknown'),
                            'city': data.get('city', 'Unknown'),
                            'isp': data.get('isp', 'Unknown'),
                            'asn': data.get('as', 'Unknown'),
                            'timezone': data.get('timezone'),
                            'is_mobile': data.get('mobile', False),
                            'is_proxy': data.get('proxy', False),
                            'is_hosting': data.get('hosting', False)
                        })
        except:
            pass
        
        return geo_data
    
    def _is_mobile_carrier(self, isp: str) -> bool:
        """Detect if ISP is a mobile carrier"""
        if not isp:
            return False
        
        isp_lower = isp.lower()
        
        # Check known carriers
        for carrier, patterns in self.mobile_carriers.items():
            if any(pattern in isp_lower for pattern in patterns):
                return True
        
        # Check generic mobile keywords
        mobile_keywords = [
            'mobile', 'cellular', 'wireless', '4g', '5g', 'lte',
            'gsm', 'umts', 'telecom', 'telco'
        ]
        
        return any(keyword in isp_lower for keyword in mobile_keywords)
    
    def _is_datacenter(self, isp: str, asn: str) -> bool:
        """Detect if proxy is from a datacenter"""
        text = f"{isp} {asn}".lower()
        
        datacenter_keywords = [
            'hosting', 'cloud', 'server', 'vps', 'dedicated',
            'colocation', 'data center', 'datacenter',
            'amazon', 'aws', 'google', 'azure', 'digitalocean',
            'linode', 'vultr', 'ovh', 'hetzner', 'alibaba'
        ]
        
        return any(keyword in text for keyword in datacenter_keywords)
    
    def _calculate_fraud_score(self, result: ProxyResult) -> int:
        """Calculate fraud risk score (0-100)"""
        score = 0
        
        # Base scores
        if result.anonymity_level == "Transparent":
            score += 30
        elif result.anonymity_level == "Anonymous":
            score += 15
        
        # Datacenter penalty
        if result.is_datacenter:
            score += 25
        
        # Mobile carrier (can be good or bad)
        if result.is_mobile:
            # Known good carriers get lower score
            good_carriers = ['verizon', 'at&t', 't-mobile', 'vodafone', 'orange']
            if any(carrier in result.isp.lower() for carrier in good_carriers):
                score += 10
            else:
                score += 20
        
        # High-risk countries
        high_risk_countries = [
            'China', 'Russia', 'Vietnam', 'India', 'Brazil',
            'Nigeria', 'Pakistan', 'Indonesia', 'Thailand', 'Ukraine'
        ]
        if result.country in high_risk_countries:
            score += 20
        
        # Residential bonus
        residential_keywords = ['broadband', 'cable', 'dsl', 'fiber', 'residential']
        if any(keyword in result.isp.lower() for keyword in residential_keywords):
            score -= 15
        
        # DNS/WebRTC leaks
        if result.dns_leak:
            score += 15
        if result.webrtc_leak:
            score += 15
        
        # Ensure score is within bounds
        return max(0, min(100, score))
    
    async def _test_https_support(self, ip: str, port: int, protocol: str) -> bool:
        """Test if proxy supports HTTPS"""
        proxy_url = f"{protocol}://{ip}:{port}"
        
        try:
            if protocol in ['socks4', 'socks5']:
                connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get('https://httpbin.org/ip', timeout=10) as response:
                        return response.status == 200
            else:
                async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=10.0) as client:
                    response = await client.get("https://httpbin.org/ip")
                    return response.status_code == 200
        except:
            return False
    
    async def _test_header_support(self, ip: str, port: int, protocol: str) -> Dict:
        """Test which headers the proxy forwards"""
        results = {
            'cookies': False,
            'referer': False,
            'user_agent': False
        }
        
        test_headers = {
            'Cookie': 'test=value',
            'Referer': 'https://example.com',
            'User-Agent': 'ProxyTester/1.0'
        }
        
        proxy_url = f"{protocol}://{ip}:{port}"
        
        try:
            if protocol in ['socks4', 'socks5']:
                connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        'https://httpbin.org/headers',
                        headers=test_headers,
                        timeout=10
                    ) as response:
                        data = await response.json()
                        headers = data.get('headers', {})
                        
                        results['cookies'] = 'Cookie' in headers
                        results['referer'] = 'Referer' in headers
                        results['user_agent'] = 'User-Agent' in headers
            else:
                async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=10.0) as client:
                    response = await client.get(
                        "https://httpbin.org/headers",
                        headers=test_headers
                    )
                    data = response.json()
                    headers = data.get('headers', {})
                    
                    results['cookies'] = 'Cookie' in headers
                    results['referer'] = 'Referer' in headers
                    results['user_agent'] = 'User-Agent' in headers
        except:
            pass
        
        return results
    
    async def _test_leaks(self, ip: str, port: int, protocol: str) -> Dict:
        """Test for DNS and WebRTC leaks"""
        results = {
            'dns_leak': False,
            'webrtc_leak': False
        }
        
        # DNS leak test would require more complex implementation
        # This is a simplified version
        
        proxy_url = f"{protocol}://{ip}:{port}"
        
        try:
            # Test DNS resolution through proxy
            if protocol in ['socks4', 'socks5']:
                connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                async with aiohttp.ClientSession(connector=connector) as session:
                    # Try to resolve a domain that returns the resolver's IP
                    async with session.get('http://whoami.akamai.net/', timeout=10) as response:
                        resolver_ip = await response.text()
                        # If resolver IP matches our real IP, we have a DNS leak
                        # This would need to be compared with actual client IP
                        results['dns_leak'] = False  # Simplified
        except:
            pass
        
        return results
    
    async def _check_rotation(self, ip: str, port: int, protocol: str) -> Dict:
        """Check if proxy rotates IPs"""
        results = {
            'is_rotating': False,
            'interval': None,
            'pool_size': None
        }
        
        exit_ips = set()
        proxy_url = f"{protocol}://{ip}:{port}"
        
        # Check exit IP multiple times
        for i in range(5):
            try:
                if protocol in ['socks4', 'socks5']:
                    connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get('http://httpbin.org/ip', timeout=5) as response:
                            data = await response.json()
                            exit_ips.add(data.get('origin', ''))
                else:
                    async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=5.0) as client:
                        response = await client.get("http://httpbin.org/ip")
                        data = response.json()
                        exit_ips.add(data.get('origin', ''))
                
                await asyncio.sleep(2)  # Wait between checks
            except:
                break
        
        if len(exit_ips) > 1:
            results['is_rotating'] = True
            results['pool_size'] = len(exit_ips)
        
        return results
    
    async def _cache_result(self, result: ProxyResult):
        """Cache proxy test result in Redis"""
        if not self.redis:
            return
        
        key = f"proxy:{result.ip}:{result.port}"
        value = json.dumps(asdict(result), default=str)
        
        # Cache for 1 hour
        await self.redis.setex(key, 3600, value)
    
    async def _broadcast_result(self, result: ProxyResult):
        """Broadcast result to all WebSocket clients"""
        if not self.active_connections:
            return
        
        message = json.dumps({
            'type': 'proxy_tested',
            'data': asdict(result)
        }, default=str)
        
        # Send to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)
    
    async def _broadcast_discovery_status(self, count: int):
        """Broadcast discovery status"""
        if not self.active_connections:
            return
        
        message = json.dumps({
            'type': 'discovery_complete',
            'data': {
                'count': count,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

# Additional features to implement:

class ProxyPoolManager:
    """Manage a pool of working proxies with rotation"""
    
    def __init__(self, tester: ProxyTester):
        self.tester = tester
        self.working_proxies = []
        self.last_used_index = 0
        
    async def add_proxy(self, ip: str, port: int, protocol: str):
        """Add and test a proxy"""
        result = await self.tester.test_proxy(ip, port, protocol)
        if result.working and result.fraud_score < 50:
            self.working_proxies.append(result)
            return True
        return False
    
    def get_next_proxy(self) -> Optional[ProxyResult]:
        """Get next proxy in rotation"""
        if not self.working_proxies:
            return None
        
        proxy = self.working_proxies[self.last_used_index]
        self.last_used_index = (self.last_used_index + 1) % len(self.working_proxies)
        return proxy
    
    async def refresh_pool(self):
        """Re-test all proxies in pool"""
        new_pool = []
        for proxy in self.working_proxies:
            result = await self.tester.test_proxy(
                proxy.ip, proxy.port, proxy.protocol
            )
            if result.working:
                new_pool.append(result)
        
        self.working_proxies = new_pool

class ProxyMonitor:
    """Monitor proxy health and performance over time"""
    
    def __init__(self, tester: ProxyTester):
        self.tester = tester
        self.monitoring_tasks = {}
    
    async def start_monitoring(self, ip: str, port: int, protocol: str, interval: int = 300):
        """Start monitoring a proxy"""
        key = f"{ip}:{port}"
        
        if key in self.monitoring_tasks:
            return
        
        async def monitor():
            while key in self.monitoring_tasks:
                result = await self.tester.test_proxy(ip, port, protocol)
                # Store result in time-series database
                # Send alerts if proxy goes down
                await asyncio.sleep(interval)
        
        task = asyncio.create_task(monitor())
        self.monitoring_tasks[key] = task
    
    def stop_monitoring(self, ip: str, port: int):
        """Stop monitoring a proxy"""
        key = f"{ip}:{port}"
        if key in self.monitoring_tasks:
            self.monitoring_tasks[key].cancel()
            del self.monitoring_tasks[key]

if __name__ == "__main__":
    # Create and run the application
    tester = ProxyTester()
    
    # Run with uvicorn
    uvicorn.run(
        tester.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )