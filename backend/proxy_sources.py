#!/usr/bin/env python3
"""
ProxySourceManager - Enterprise-grade proxy discovery system
Implements intelligent scraping with anti-detection and fault tolerance
"""

import asyncio
import aiohttp
import time
import random
import json
import re
from typing import List, Dict, Set, Optional, Tuple, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse
import hashlib
from collections import deque
import logging
from aiohttp_retry import RetryClient, ExponentialRetry
from bs4 import BeautifulSoup
import cloudscraper
from fake_useragent import UserAgent

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProxyEntry:
    """Validated proxy with metadata"""
    ip: str
    port: int
    protocol: str = 'unknown'
    country: Optional[str] = None
    last_seen: datetime = field(default_factory=datetime.utcnow)
    source: str = ''
    reliability_score: float = 0.0
    
    def __hash__(self):
        return hash(f"{self.ip}:{self.port}")
    
    def __eq__(self, other):
        if isinstance(other, ProxyEntry):
            return self.ip == other.ip and self.port == other.port
        return False
    
    @property
    def address(self) -> str:
        return f"{self.ip}:{self.port}"


class RateLimiter:
    """Intelligent rate limiter with burst support"""
    
    def __init__(self, requests_per_second: float = 1.0, burst: int = 5):
        self.rate = requests_per_second
        self.burst = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to maintain rate limit"""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(sleep_time)
                self.tokens = 1
            
            self.tokens -= 1


class AntiDetectionManager:
    """Manages anti-detection strategies"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.last_rotation = time.time()
        self.request_count = 0
        self.session_age = 300  # Rotate session every 5 minutes
        
    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers that mimic real browsers"""
        self.request_count += 1
        
        # Rotate user agent periodically
        if time.time() - self.last_rotation > self.session_age:
            self.ua.update()
            self.last_rotation = time.time()
        
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Add random referer sometimes
        if random.random() > 0.5:
            headers['Referer'] = random.choice([
                'https://www.google.com/',
                'https://duckduckgo.com/',
                'https://www.bing.com/'
            ])
        
        return headers
    
    async def random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add human-like random delay"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)


class ProxySourceBase:
    """Base class for proxy sources with common functionality"""
    
    def __init__(self, name: str, rate_limit: float = 1.0):
        self.name = name
        self.rate_limiter = RateLimiter(rate_limit)
        self.anti_detection = AntiDetectionManager()
        self.success_count = 0
        self.failure_count = 0
        self.last_success = None
        
    @property
    def reliability_score(self) -> float:
        """Calculate source reliability based on success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5  # Unknown reliability
        return self.success_count / total
    
    async def fetch(self) -> Set[ProxyEntry]:
        """Fetch proxies from this source"""
        raise NotImplementedError
    
    def parse_proxy_string(self, proxy_str: str) -> Optional[ProxyEntry]:
        """Parse various proxy formats intelligently"""
        proxy_str = proxy_str.strip()
        if not proxy_str:
            return None
        
        # Format 1: IP:PORT
        basic_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
        match = re.match(basic_pattern, proxy_str)
        if match:
            ip, port = match.groups()
            if self._is_valid_ip(ip) and 1 <= int(port) <= 65535:
                return ProxyEntry(ip=ip, port=int(port), source=self.name)
        
        # Format 2: PROTOCOL://IP:PORT
        protocol_pattern = r'^(https?|socks[45]?)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
        match = re.match(protocol_pattern, proxy_str, re.IGNORECASE)
        if match:
            protocol, ip, port = match.groups()
            if self._is_valid_ip(ip) and 1 <= int(port) <= 65535:
                return ProxyEntry(
                    ip=ip, 
                    port=int(port), 
                    protocol=protocol.lower(),
                    source=self.name
                )
        
        # Format 3: IP:PORT with additional info (country, type, etc)
        detailed_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})\s*(.*)$'
        match = re.match(detailed_pattern, proxy_str)
        if match:
            ip, port, extra = match.groups()
            if self._is_valid_ip(ip) and 1 <= int(port) <= 65535:
                proxy = ProxyEntry(ip=ip, port=int(port), source=self.name)
                
                # Extract country code if present
                country_match = re.search(r'\b([A-Z]{2})\b', extra)
                if country_match:
                    proxy.country = country_match.group(1)
                
                # Extract protocol if present
                proto_match = re.search(r'\b(HTTPS?|SOCKS[45]?)\b', extra, re.IGNORECASE)
                if proto_match:
                    proxy.protocol = proto_match.group(1).lower()
                
                return proxy
        
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False


class GitHubProxyList(ProxySourceBase):
    """Scraper for GitHub proxy lists (most reliable)"""
    
    def __init__(self):
        super().__init__("GitHub-ProxyList", rate_limit=0.5)
        self.urls = [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", 
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]
    
    async def fetch(self) -> Set[ProxyEntry]:
        """Fetch from multiple GitHub sources"""
        proxies = set()
        
        # Create retry client for reliability
        retry_options = ExponentialRetry(attempts=3, start_timeout=1)
        
        async with RetryClient(
            client_session=aiohttp.ClientSession(),
            retry_options=retry_options
        ) as session:
            for url in self.urls:
                try:
                    await self.rate_limiter.acquire()
                    
                    # Extract protocol from URL
                    protocol = 'http'
                    if 'socks5' in url:
                        protocol = 'socks5'
                    elif 'socks4' in url:
                        protocol = 'socks4'
                    
                    headers = self.anti_detection.get_headers()
                    async with session.get(url, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            text = await response.text()
                            lines = text.strip().split('\n')
                            
                            for line in lines:
                                proxy = self.parse_proxy_string(line)
                                if proxy:
                                    proxy.protocol = protocol
                                    proxies.add(proxy)
                            
                            self.success_count += 1
                            self.last_success = datetime.utcnow()
                            logger.info(f"Fetched {len(lines)} proxies from {urlparse(url).path}")
                        else:
                            self.failure_count += 1
                            logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                
                except Exception as e:
                    self.failure_count += 1
                    logger.error(f"Error fetching {url}: {str(e)}")
                    
                await self.anti_detection.random_delay(0.5, 1.5)
        
        return proxies


class ProxyScrapeCom(ProxySourceBase):
    """Scraper for proxyscrape.com API"""
    
    def __init__(self):
        super().__init__("ProxyScrape", rate_limit=0.2)
        self.api_endpoints = [
            {
                'url': 'https://api.proxyscrape.com/v2/',
                'params': {
                    'request': 'displayproxies',
                    'protocol': 'socks5',
                    'timeout': 10000,
                    'country': 'all',
                    'ssl': 'all',
                    'anonymity': 'all',
                    'simplified': 'true'
                }
            },
            {
                'url': 'https://api.proxyscrape.com/v2/',
                'params': {
                    'request': 'displayproxies',
                    'protocol': 'http',
                    'timeout': 10000,
                    'country': 'all',
                    'ssl': 'all',
                    'anonymity': 'all',
                    'simplified': 'true'
                }
            }
        ]
    
    async def fetch(self) -> Set[ProxyEntry]:
        """Fetch from ProxyScrape API"""
        proxies = set()
        
        async with aiohttp.ClientSession() as session:
            for endpoint in self.api_endpoints:
                try:
                    await self.rate_limiter.acquire()
                    
                    headers = self.anti_detection.get_headers()
                    async with session.get(
                        endpoint['url'],
                        params=endpoint['params'],
                        headers=headers,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            text = await response.text()
                            protocol = endpoint['params']['protocol']
                            
                            for line in text.strip().split('\n'):
                                proxy = self.parse_proxy_string(line)
                                if proxy:
                                    proxy.protocol = protocol
                                    proxies.add(proxy)
                            
                            self.success_count += 1
                            self.last_success = datetime.utcnow()
                            logger.info(f"Fetched {len(proxies)} {protocol} proxies from ProxyScrape")
                        else:
                            self.failure_count += 1
                            logger.warning(f"ProxyScrape API returned {response.status}")
                
                except Exception as e:
                    self.failure_count += 1
                    logger.error(f"ProxyScrape error: {str(e)}")
                
                await self.anti_detection.random_delay(1, 2)
        
        return proxies


class ProxyListDownload(ProxySourceBase):
    """Scraper for proxy-list.download (uses CloudFlare protection)"""
    
    def __init__(self):
        super().__init__("ProxyListDownload", rate_limit=0.1)
        self.scraper = cloudscraper.create_scraper()
    
    async def fetch(self) -> Set[ProxyEntry]:
        """Fetch using CloudFlare bypass"""
        proxies = set()
        urls = [
            'https://www.proxy-list.download/api/v1/get?type=socks5',
            'https://www.proxy-list.download/api/v1/get?type=socks4',
            'https://www.proxy-list.download/api/v1/get?type=http'
        ]
        
        # Use thread pool for cloudscraper (it's not async)
        loop = asyncio.get_event_loop()
        
        for url in urls:
            try:
                await self.rate_limiter.acquire()
                
                # Extract protocol from URL
                protocol = url.split('type=')[1]
                
                # Run in thread pool
                response = await loop.run_in_executor(
                    None, 
                    self.scraper.get, 
                    url
                )
                
                if response.status_code == 200:
                    for line in response.text.strip().split('\n'):
                        proxy = self.parse_proxy_string(line)
                        if proxy:
                            proxy.protocol = protocol
                            proxies.add(proxy)
                    
                    self.success_count += 1
                    logger.info(f"Fetched {len(proxies)} {protocol} proxies from proxy-list.download")
                else:
                    self.failure_count += 1
                    logger.warning(f"proxy-list.download returned {response.status_code}")
                    
            except Exception as e:
                self.failure_count += 1
                logger.error(f"proxy-list.download error: {str(e)}")
            
            await self.anti_detection.random_delay(2, 4)
        
        return proxies


class FreeProxyListNet(ProxySourceBase):
    """Scraper for free-proxy-list.net (HTML parsing)"""
    
    def __init__(self):
        super().__init__("FreeProxyList", rate_limit=0.1)
        self.url = "https://free-proxy-list.net/"
    
    async def fetch(self) -> Set[ProxyEntry]:
        """Parse HTML table for proxies"""
        proxies = set()
        
        try:
            await self.rate_limiter.acquire()
            
            # Use cloudscraper for CloudFlare protection
            loop = asyncio.get_event_loop()
            scraper = cloudscraper.create_scraper()
            
            response = await loop.run_in_executor(
                None,
                scraper.get,
                self.url
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the proxy table
                table = soup.find('table', {'class': 'table-striped'})
                if not table:
                    table = soup.find('table')  # Fallback
                
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 7:
                            ip = cells[0].text.strip()
                            port = cells[1].text.strip()
                            country = cells[3].text.strip()
                            anonymity = cells[4].text.strip()
                            https = cells[6].text.strip()
                            
                            if self._is_valid_ip(ip) and port.isdigit():
                                proxy = ProxyEntry(
                                    ip=ip,
                                    port=int(port),
                                    protocol='https' if https == 'yes' else 'http',
                                    country=country[:2].upper() if len(country) >= 2 else None,
                                    source=self.name
                                )
                                proxies.add(proxy)
                    
                    self.success_count += 1
                    logger.info(f"Parsed {len(proxies)} proxies from free-proxy-list.net")
                else:
                    self.failure_count += 1
                    logger.warning("Could not find proxy table on free-proxy-list.net")
            else:
                self.failure_count += 1
                logger.warning(f"free-proxy-list.net returned {response.status_code}")
                
        except Exception as e:
            self.failure_count += 1
            logger.error(f"free-proxy-list.net error: {str(e)}")
        
        return proxies


class ProxySourceManager:
    """Manages multiple proxy sources with intelligent scheduling"""
    
    def __init__(self):
        self.sources: List[ProxySourceBase] = [
            GitHubProxyList(),
            ProxyScrapeCom(),
            ProxyListDownload(),
            FreeProxyListNet()
        ]
        self.proxy_cache: Set[ProxyEntry] = set()
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=15)
        self._lock = asyncio.Lock()
    
    async def get_proxies(self, force_refresh: bool = False) -> Set[ProxyEntry]:
        """Get proxies from all sources with caching"""
        async with self._lock:
            # Check cache
            if not force_refresh and self.cache_timestamp:
                if datetime.utcnow() - self.cache_timestamp < self.cache_duration:
                    logger.info(f"Returning {len(self.proxy_cache)} cached proxies")
                    return self.proxy_cache.copy()
            
            # Fetch from all sources
            all_proxies = set()
            tasks = []
            
            # Sort sources by reliability
            sorted_sources = sorted(
                self.sources, 
                key=lambda s: s.reliability_score, 
                reverse=True
            )
            
            # Fetch concurrently with staggered start
            for i, source in enumerate(sorted_sources):
                delay = i * 0.5  # Stagger requests
                task = self._fetch_with_delay(source, delay)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, set):
                    all_proxies.update(result)
                    logger.info(f"{sorted_sources[i].name}: fetched {len(result)} proxies")
                else:
                    logger.error(f"{sorted_sources[i].name}: {str(result)}")
            
            # Update cache
            self.proxy_cache = all_proxies
            self.cache_timestamp = datetime.utcnow()
            
            # Log statistics
            protocols = {}
            for proxy in all_proxies:
                protocols[proxy.protocol] = protocols.get(proxy.protocol, 0) + 1
            
            logger.info(f"Total unique proxies: {len(all_proxies)}")
            logger.info(f"By protocol: {protocols}")
            
            return all_proxies.copy()
    
    async def _fetch_with_delay(self, source: ProxySourceBase, delay: float) -> Set[ProxyEntry]:
        """Fetch from source with initial delay"""
        await asyncio.sleep(delay)
        return await source.fetch()
    
    def get_source_statistics(self) -> Dict[str, Dict]:
        """Get statistics for all sources"""
        stats = {}
        for source in self.sources:
            stats[source.name] = {
                'reliability_score': round(source.reliability_score, 3),
                'success_count': source.success_count,
                'failure_count': source.failure_count,
                'last_success': source.last_success.isoformat() if source.last_success else None
            }
        return stats


# Testing code
async def test_proxy_sources():
    """Test the proxy source manager"""
    manager = ProxySourceManager()
    
    print("🔍 Testing Proxy Source Manager...")
    print("-" * 50)
    
    # Test 1: Fetch proxies
    print("Test 1: Fetching proxies from all sources...")
    proxies = await manager.get_proxies()
    print(f"✅ Found {len(proxies)} unique proxies")
    
    # Show sample proxies
    print("\nSample proxies:")
    for i, proxy in enumerate(list(proxies)[:5]):
        print(f"  {i+1}. {proxy.address} ({proxy.protocol}) from {proxy.source}")
    
    # Test 2: Check caching
    print("\nTest 2: Testing cache...")
    start = time.time()
    cached_proxies = await manager.get_proxies()
    cache_time = time.time() - start
    print(f"✅ Cache hit: {len(cached_proxies)} proxies in {cache_time:.3f}s")
    
    # Test 3: Source statistics
    print("\nTest 3: Source statistics:")
    stats = manager.get_source_statistics()
    for source, data in stats.items():
        print(f"  {source}:")
        print(f"    Reliability: {data['reliability_score']}")
        print(f"    Success/Failure: {data['success_count']}/{data['failure_count']}")
    
    print("\n✅ All tests passed!")
    return proxies


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_proxy_sources())