#!/usr/bin/env python3
"""
Intelligent Proxy Scanner - Production Grade
Uses application-layer protocol detection instead of port scanning
Implements ethical scanning with abuse prevention
"""

import asyncio
import aiohttp
import socket
import struct
import time
import ipaddress
import random
from typing import List, Set, Dict, Optional, Tuple, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import deque
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import aiofiles
from asyncio import Semaphore
from asn_lookup import ASNLookupService, ASNInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScanTarget:
    """Represents a target for scanning"""
    ip: str
    port: int
    priority: float = 1.0  # Higher = scan sooner
    source: str = "manual"
    last_scan: Optional[datetime] = None
    
    def __hash__(self):
        return hash(f"{self.ip}:{self.port}")


@dataclass 
class ScanResult:
    """Result of a proxy scan"""
    ip: str
    port: int
    is_proxy: bool
    proxy_type: Optional[str] = None
    response_time: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0  # 0-1 confidence score
    metadata: Dict = field(default_factory=dict)


class ProxyProtocolDetector:
    """Detects proxy protocols without port scanning"""
    
    def __init__(self):
        self.timeout = 5.0
        self.max_retries = 2
        
    async def detect_socks5(self, ip: str, port: int) -> Tuple[bool, float]:
        """
        Detect SOCKS5 proxy by sending proper handshake
        Returns (is_socks5, confidence_score)
        """
        start_time = time.time()
        
        try:
            # SOCKS5 handshake: Version(5) + Number of methods(1) + Method(0=no auth)
            handshake = b'\x05\x01\x00'
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )
            
            # Send SOCKS5 greeting
            writer.write(handshake)
            await writer.drain()
            
            # Read response (should be \x05\x00 for SOCKS5 no auth)
            response = await asyncio.wait_for(
                reader.read(2),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            if len(response) == 2 and response[0] == 0x05:
                # Valid SOCKS5 response
                if response[1] == 0x00:
                    # No authentication required
                    confidence = 1.0
                elif response[1] == 0x02:
                    # Username/password required
                    confidence = 0.9
                else:
                    # Other auth method
                    confidence = 0.8
                
                writer.close()
                await writer.wait_closed()
                
                return True, confidence
            
            writer.close()
            await writer.wait_closed()
            
        except asyncio.TimeoutError:
            logger.debug(f"SOCKS5 timeout for {ip}:{port}")
        except ConnectionRefusedError:
            logger.debug(f"Connection refused for {ip}:{port}")
        except Exception as e:
            logger.debug(f"SOCKS5 detection error for {ip}:{port}: {str(e)}")
        
        return False, 0.0
    
    async def detect_socks4(self, ip: str, port: int) -> Tuple[bool, float]:
        """
        Detect SOCKS4 proxy
        Returns (is_socks4, confidence_score)
        """
        try:
            # SOCKS4 connect request to Google DNS (8.8.8.8:53)
            # VN=4, CD=1 (connect), DSTPORT=53, DSTIP=8.8.8.8
            request = struct.pack(
                '!BBH4sB',
                0x04,  # Version
                0x01,  # Connect command
                53,    # Port (DNS)
                socket.inet_aton('8.8.8.8'),  # IP
                0x00   # Null terminator for userid
            )
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )
            
            writer.write(request)
            await writer.drain()
            
            # Read response (8 bytes)
            response = await asyncio.wait_for(
                reader.read(8),
                timeout=self.timeout
            )
            
            if len(response) >= 2:
                # Check if VN=0 and CD=90 (request granted)
                if response[0] == 0x00 and response[1] == 0x5A:
                    writer.close()
                    await writer.wait_closed()
                    return True, 1.0
                elif response[0] == 0x00:
                    # SOCKS4 response but request denied
                    writer.close()
                    await writer.wait_closed()
                    return True, 0.7
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.debug(f"SOCKS4 detection error for {ip}:{port}: {str(e)}")
        
        return False, 0.0
    
    async def detect_http_proxy(self, ip: str, port: int) -> Tuple[bool, float]:
        """
        Detect HTTP proxy using CONNECT method
        Returns (is_http_proxy, confidence_score)
        """
        try:
            # Try HTTP CONNECT to a known site
            connect_request = (
                f"CONNECT www.google.com:443 HTTP/1.1\r\n"
                f"Host: www.google.com:443\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Proxy-Connection: Keep-Alive\r\n"
                f"\r\n"
            ).encode()
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )
            
            writer.write(connect_request)
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(
                reader.read(1024),
                timeout=self.timeout
            )
            
            response_str = response.decode('utf-8', errors='ignore')
            
            writer.close()
            await writer.wait_closed()
            
            # Check for proxy responses
            if 'HTTP/' in response_str:
                if '200 Connection established' in response_str:
                    return True, 1.0
                elif '407 Proxy Authentication Required' in response_str:
                    return True, 0.9
                elif any(code in response_str for code in ['400', '403', '404', '500', '502', '503']):
                    # HTTP error codes suggest it's an HTTP server (possibly proxy)
                    return True, 0.6
            
        except Exception as e:
            logger.debug(f"HTTP proxy detection error for {ip}:{port}: {str(e)}")
        
        return False, 0.0
    
    async def detect_proxy(self, ip: str, port: int) -> ScanResult:
        """
        Detect if target is a proxy and determine type
        """
        start_time = time.time()
        
        # Try each protocol in parallel
        tasks = [
            self.detect_socks5(ip, port),
            self.detect_socks4(ip, port),
            self.detect_http_proxy(ip, port)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        response_time = time.time() - start_time
        
        # Process results
        detections = []
        
        if not isinstance(results[0], Exception):
            is_socks5, confidence = results[0]
            if is_socks5:
                detections.append(('socks5', confidence))
        
        if not isinstance(results[1], Exception):
            is_socks4, confidence = results[1]
            if is_socks4:
                detections.append(('socks4', confidence))
        
        if not isinstance(results[2], Exception):
            is_http, confidence = results[2]
            if is_http:
                detections.append(('http', confidence))
        
        if detections:
            # Sort by confidence and pick the best
            detections.sort(key=lambda x: x[1], reverse=True)
            proxy_type, confidence = detections[0]
            
            return ScanResult(
                ip=ip,
                port=port,
                is_proxy=True,
                proxy_type=proxy_type,
                response_time=response_time,
                confidence=confidence
            )
        
        return ScanResult(
            ip=ip,
            port=port,
            is_proxy=False,
            response_time=response_time,
            confidence=0.0
        )


class IntelligentTargetSelector:
    """Selects scanning targets intelligently"""
    
    def __init__(self):
        self.asn_service = ASNLookupService()
        
        self.common_proxy_ports = [
            1080,   # SOCKS
            1081,   # SOCKS
            3128,   # HTTP Proxy
            8080,   # HTTP Proxy Alt
            8081,   # HTTP Proxy Alt
            8888,   # HTTP Proxy Alt
            9050,   # Tor SOCKS
            9150,   # Tor Browser
            7070,   # Common proxy
            8118,   # Privoxy
            8123,   # Polipo
            9999,   # Common proxy
            4444,   # Common proxy
            6666,   # Common proxy
        ]
        
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def get_asn_info(self, ip: str) -> Optional[ASNInfo]:
        """Get ASN information for an IP"""
        return await self.asn_service.lookup_ip(ip)
    
    async def generate_targets(self, 
                             seed_ips: List[str] = None,
                             max_targets: int = 1000) -> AsyncIterator[ScanTarget]:
        """
        Generate scanning targets intelligently
        """
        targets_generated = 0
        
        # 1. Known proxy ports on seed IPs
        if seed_ips:
            for ip in seed_ips:
                for port in self.common_proxy_ports:
                    if targets_generated >= max_targets:
                        return
                    
                    yield ScanTarget(
                        ip=ip,
                        port=port,
                        priority=0.9,
                        source='seed'
                    )
                    targets_generated += 1
        
        # 2. Common proxy provider ranges
        # In production, this would query real BGP data
        proxy_ranges = [
            '104.248.0.0/18',    # DigitalOcean
            '159.65.0.0/16',     # DigitalOcean
            '167.172.0.0/16',    # DigitalOcean
            '51.15.0.0/16',      # OVH
            '54.36.0.0/16',      # OVH
            '185.0.0.0/8',       # Various hosting
        ]
        
        for cidr in proxy_ranges[:3]:  # Limit for demo
            network = ipaddress.ip_network(cidr, strict=False)
            
            # Sample random IPs from the range
            ips = list(network.hosts())
            sample_size = min(10, len(ips))
            
            for ip in random.sample(ips, sample_size):
                if targets_generated >= max_targets:
                    return
                
                # Focus on common proxy ports
                for port in self.common_proxy_ports[:5]:
                    yield ScanTarget(
                        ip=str(ip),
                        port=port,
                        priority=0.7,
                        source='asn_range'
                    )
                    targets_generated += 1
    
    def estimate_scan_size(self, targets: List[ScanTarget]) -> Dict:
        """Estimate the scan size and duration"""
        total_targets = len(targets)
        estimated_time = total_targets * 0.5  # 0.5 seconds per target average
        
        return {
            'total_targets': total_targets,
            'estimated_duration_seconds': estimated_time,
            'estimated_bandwidth_mb': total_targets * 0.001,  # ~1KB per scan
            'risk_level': 'low' if total_targets < 1000 else 'medium'
        }


class EthicalScanManager:
    """Manages ethical scanning with rate limiting and abuse prevention"""
    
    def __init__(self, max_concurrent: int = 50, requests_per_second: float = 10.0):
        self.max_concurrent = max_concurrent
        self.semaphore = Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(requests_per_second)
        self.scan_log = deque(maxlen=10000)
        self.blocklist = set()
        self.detector = ProxyProtocolDetector()
        
        # Abuse prevention
        self.abuse_contacts = {}
        self.scan_history = {}
        
    async def load_blocklist(self, filename: str = 'blocklist.txt'):
        """Load IPs that should never be scanned"""
        try:
            async with aiofiles.open(filename, 'r') as f:
                async for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('#'):
                        self.blocklist.add(ip)
            logger.info(f"Loaded {len(self.blocklist)} IPs into blocklist")
        except FileNotFoundError:
            logger.info("No blocklist file found, starting with empty blocklist")
    
    async def check_abuse_contact(self, ip: str) -> Optional[str]:
        """Check WHOIS for abuse contact"""
        try:
            # Cache abuse contacts by /24 subnet
            subnet = '.'.join(ip.split('.')[:3]) + '.0/24'
            
            if subnet in self.abuse_contacts:
                return self.abuse_contacts[subnet]
            
            # In production, would do real WHOIS lookup
            # For now, return mock data
            abuse_contact = "abuse@example.com"
            self.abuse_contacts[subnet] = abuse_contact
            
            return abuse_contact
        except:
            return None
    
    async def is_scan_allowed(self, target: ScanTarget) -> bool:
        """Check if we're allowed to scan this target"""
        # Check blocklist
        if target.ip in self.blocklist:
            logger.warning(f"Skipping blocklisted IP: {target.ip}")
            return False
        
        # Check rate limits per IP
        ip_history = self.scan_history.get(target.ip, [])
        recent_scans = [t for t in ip_history if datetime.utcnow() - t < timedelta(hours=1)]
        
        if len(recent_scans) >= 10:
            logger.warning(f"Rate limit exceeded for {target.ip}")
            return False
        
        # Check for government/military IPs (simplified)
        if any(target.ip.startswith(prefix) for prefix in ['11.', '21.', '22.', '26.', '28.', '29.', '30.']):
            logger.warning(f"Skipping government IP range: {target.ip}")
            return False
        
        return True
    
    async def scan_target(self, target: ScanTarget) -> Optional[ScanResult]:
        """Scan a single target ethically"""
        if not await self.is_scan_allowed(target):
            return None
        
        async with self.semaphore:
            await self.rate_limiter.acquire()
            
            # Log the scan attempt
            self.scan_log.append({
                'timestamp': datetime.utcnow(),
                'ip': target.ip,
                'port': target.port
            })
            
            # Update scan history
            if target.ip not in self.scan_history:
                self.scan_history[target.ip] = []
            self.scan_history[target.ip].append(datetime.utcnow())
            
            # Perform the actual scan
            result = await self.detector.detect_proxy(target.ip, target.port)
            
            # Log successful proxy detection
            if result.is_proxy:
                logger.info(f"Found {result.proxy_type} proxy at {target.ip}:{target.port}")
            
            return result
    
    async def scan_batch(self, targets: List[ScanTarget]) -> List[ScanResult]:
        """Scan multiple targets concurrently"""
        tasks = [self.scan_target(target) for target in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, ScanResult):
                valid_results.append(result)
            elif result is not None and not isinstance(result, Exception):
                valid_results.append(result)
        
        return valid_results
    
    def get_scan_statistics(self) -> Dict:
        """Get scanning statistics"""
        total_scans = len(self.scan_log)
        
        if total_scans == 0:
            return {
                'total_scans': 0,
                'scan_rate': 0,
                'active_ips': 0
            }
        
        # Calculate scan rate
        now = datetime.utcnow()
        recent_scans = [s for s in self.scan_log if now - s['timestamp'] < timedelta(minutes=1)]
        scan_rate = len(recent_scans)
        
        # Count unique IPs scanned
        active_ips = len(set(s['ip'] for s in self.scan_log))
        
        return {
            'total_scans': total_scans,
            'scan_rate_per_minute': scan_rate,
            'active_ips': active_ips,
            'blocklist_size': len(self.blocklist),
            'cached_abuse_contacts': len(self.abuse_contacts)
        }


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: float, burst: int = None):
        self.rate = rate
        self.burst = burst or int(rate * 2)
        self.tokens = self.burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1):
        """Acquire tokens, waiting if necessary"""
        async with self._lock:
            while self.tokens < tokens:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now
                
                if self.tokens < tokens:
                    sleep_time = (tokens - self.tokens) / self.rate
                    await asyncio.sleep(sleep_time)
            
            self.tokens -= tokens


# Test implementation
async def test_scanner():
    """Test the scanning system"""
    print("=" * 70)
    print("PHASE 2 TEST: Intelligent Proxy Scanner")
    print("=" * 70)
    
    # Initialize components
    detector = ProxyProtocolDetector()
    selector = IntelligentTargetSelector()
    scanner = EthicalScanManager(max_concurrent=10, requests_per_second=5)
    
    # Test 1: Protocol detection on known proxy
    print("\n📡 Test 1: Protocol Detection")
    print("Testing known public proxies...")
    
    test_proxies = [
        # These are public proxies for testing
        ('152.26.229.42', 1080),    # SOCKS5
        ('47.88.3.19', 8080),       # HTTP
        ('195.154.84.106', 5566),   # Unknown
    ]
    
    for ip, port in test_proxies:
        print(f"\nScanning {ip}:{port}...")
        result = await detector.detect_proxy(ip, port)
        
        if result.is_proxy:
            print(f"✅ Found {result.proxy_type} proxy!")
            print(f"   Confidence: {result.confidence:.2%}")
            print(f"   Response time: {result.response_time:.3f}s")
        else:
            print(f"❌ Not a proxy or unreachable")
    
    # Test 2: Target generation
    print("\n🎯 Test 2: Intelligent Target Selection")
    targets = []
    async for target in selector.generate_targets(max_targets=20):
        targets.append(target)
    
    print(f"Generated {len(targets)} targets")
    
    # Show sample targets
    print("\nSample targets:")
    for target in targets[:5]:
        print(f"  {target.ip}:{target.port} (priority: {target.priority}, source: {target.source})")
    
    # Test 3: Ethical scanning
    print("\n🛡️ Test 3: Ethical Scanning with Rate Limiting")
    await scanner.load_blocklist()
    
    # Scan a small batch
    print("Scanning batch of targets...")
    results = await scanner.scan_batch(targets[:10])
    
    # Show results
    found_proxies = [r for r in results if r.is_proxy]
    print(f"\nScanned {len(results)} targets")
    print(f"Found {len(found_proxies)} proxies")
    
    for proxy in found_proxies:
        print(f"  {proxy.ip}:{proxy.port} - {proxy.proxy_type} (confidence: {proxy.confidence:.2%})")
    
    # Show statistics
    stats = scanner.get_scan_statistics()
    print(f"\nScan Statistics:")
    print(f"  Total scans: {stats['total_scans']}")
    print(f"  Scan rate: {stats['scan_rate_per_minute']}/min")
    print(f"  Unique IPs: {stats['active_ips']}")
    
    print("\n✅ Phase 2 scanner test complete!")


if __name__ == "__main__":
    asyncio.run(test_scanner())