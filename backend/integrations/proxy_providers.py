#!/usr/bin/env python3
"""
Proxy Provider Integration Module
Supports Bright Data, Oxylabs, IPRoyal, and more
"""

import asyncio
import hashlib
import hmac
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import logging
from decimal import Decimal

import httpx
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class ProxyType(str, Enum):
    """Proxy types offered by providers"""
    DATACENTER = "datacenter"
    RESIDENTIAL = "residential"
    MOBILE = "mobile"
    ISP = "isp"
    STATIC_RESIDENTIAL = "static_residential"


class AuthMethod(str, Enum):
    """Authentication methods"""
    USERNAME_PASSWORD = "userpass"
    IP_WHITELIST = "ip_whitelist"
    TOKEN = "token"
    COMBINED = "combined"


@dataclass
class ProxyPackage:
    """Proxy package details"""
    id: str
    name: str
    type: ProxyType
    price_per_gb: Decimal
    price_per_ip: Optional[Decimal] = None
    min_purchase: Decimal = Decimal("1.0")
    bandwidth_gb: Optional[float] = None
    ip_count: Optional[int] = None
    locations: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    auth_methods: List[AuthMethod] = field(default_factory=list)
    rotation_type: str = "rotating"  # rotating, sticky, static
    pool_size: Optional[int] = None
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total package price"""
        if self.bandwidth_gb:
            return self.price_per_gb * Decimal(str(self.bandwidth_gb))
        elif self.ip_count and self.price_per_ip:
            return self.price_per_ip * self.ip_count
        return Decimal("0")


@dataclass
class ProxyCredentials:
    """Proxy access credentials"""
    provider: str
    username: Optional[str] = None
    password: Optional[str] = None
    endpoint: Optional[str] = None
    port: Optional[int] = None
    token: Optional[str] = None
    whitelisted_ips: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageStats:
    """Proxy usage statistics"""
    bandwidth_used_gb: float = 0.0
    bandwidth_limit_gb: Optional[float] = None
    requests_made: int = 0
    requests_limit: Optional[int] = None
    unique_ips_used: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def bandwidth_remaining_gb(self) -> Optional[float]:
        if self.bandwidth_limit_gb:
            return max(0, self.bandwidth_limit_gb - self.bandwidth_used_gb)
        return None
    
    @property
    def is_quota_exceeded(self) -> bool:
        if self.bandwidth_limit_gb and self.bandwidth_used_gb >= self.bandwidth_limit_gb:
            return True
        if self.requests_limit and self.requests_made >= self.requests_limit:
            return True
        return False


class ProxyProvider(ABC):
    """Base class for proxy provider integrations"""
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = ""
        self.name = ""
        self._client: Optional[httpx.AsyncClient] = None
        
        # Encryption for storing sensitive data
        self._cipher = Fernet(Fernet.generate_key())
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @abstractmethod
    async def get_packages(self) -> List[ProxyPackage]:
        """Get available proxy packages"""
        pass
    
    @abstractmethod
    async def purchase_package(self, package_id: str, **kwargs) -> ProxyCredentials:
        """Purchase a proxy package"""
        pass
    
    @abstractmethod
    async def get_usage_stats(self) -> UsageStats:
        """Get current usage statistics"""
        pass
    
    @abstractmethod
    async def rotate_credentials(self) -> ProxyCredentials:
        """Rotate proxy credentials"""
        pass
    
    @abstractmethod
    async def add_ip_whitelist(self, ips: List[str]) -> bool:
        """Add IPs to whitelist"""
        pass
    
    def _sign_request(self, method: str, path: str, body: str = "") -> str:
        """Sign API request"""
        if not self.api_secret:
            return ""
        
        timestamp = str(int(time.time()))
        message = f"{method}\n{path}\n{timestamp}\n{body}"
        
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}:{signature}"
    
    def _encrypt_credentials(self, creds: Dict[str, Any]) -> str:
        """Encrypt sensitive credentials"""
        json_str = json.dumps(creds)
        return self._cipher.encrypt(json_str.encode()).decode()
    
    def _decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """Decrypt credentials"""
        decrypted = self._cipher.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())


class BrightDataProvider(ProxyProvider):
    """Bright Data (formerly Luminati) integration"""
    
    def __init__(self, customer_id: str, api_token: str):
        super().__init__(api_token)
        self.customer_id = customer_id
        self.base_url = "https://api.brightdata.com"
        self.name = "Bright Data"
    
    async def get_packages(self) -> List[ProxyPackage]:
        """Get Bright Data packages"""
        packages = []
        
        # Datacenter proxies
        packages.append(ProxyPackage(
            id="bd_datacenter_rotating",
            name="Datacenter Rotating IPs",
            type=ProxyType.DATACENTER,
            price_per_gb=Decimal("0.50"),
            min_purchase=Decimal("100"),
            locations=["US", "UK", "DE", "FR", "CA", "AU", "JP", "SG"],
            features=["Unlimited bandwidth", "99.9% uptime", "Fast rotation"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD, AuthMethod.IP_WHITELIST],
            rotation_type="rotating",
            pool_size=100000
        ))
        
        # Residential proxies
        packages.append(ProxyPackage(
            id="bd_residential_premium",
            name="Premium Residential",
            type=ProxyType.RESIDENTIAL,
            price_per_gb=Decimal("15.00"),
            min_purchase=Decimal("10"),
            locations=["Global", "US", "UK", "DE", "FR", "IT", "ES", "BR", "IN", "JP"],
            features=["Real residential IPs", "City targeting", "ASN targeting", "Sticky sessions"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD],
            rotation_type="rotating",
            pool_size=72000000
        ))
        
        # Mobile proxies
        packages.append(ProxyPackage(
            id="bd_mobile_premium",
            name="Mobile IPs",
            type=ProxyType.MOBILE,
            price_per_gb=Decimal("30.00"),
            min_purchase=Decimal("5"),
            locations=["US", "UK", "DE", "FR", "IT", "ES", "BR", "IN"],
            features=["Real mobile carriers", "3G/4G/5G", "Carrier targeting"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD],
            rotation_type="rotating",
            pool_size=7000000
        ))
        
        # ISP proxies (static residential)
        packages.append(ProxyPackage(
            id="bd_isp_static",
            name="ISP Proxies",
            type=ProxyType.ISP,
            price_per_ip=Decimal("20.00"),
            ip_count=1,
            locations=["US", "UK", "CA"],
            features=["Static IPs", "Residential ISPs", "Unlimited bandwidth", "High speed"],
            auth_methods=[AuthMethod.IP_WHITELIST],
            rotation_type="static"
        ))
        
        return packages
    
    async def purchase_package(self, package_id: str, **kwargs) -> ProxyCredentials:
        """Purchase Bright Data package"""
        # Implementation would call actual API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Customer-ID": self.customer_id
        }
        
        # API call would go here
        # response = await self._client.post(...)
        
        # Return credentials
        return ProxyCredentials(
            provider=self.name,
            username=f"customer-{self.customer_id}-{package_id}",
            password=hashlib.sha256(f"{self.api_key}{package_id}".encode()).hexdigest()[:16],
            endpoint="zproxy.lum-superproxy.io",
            port=22225,
            expires_at=datetime.utcnow() + timedelta(days=30),
            metadata={
                "package_id": package_id,
                "zone": kwargs.get("zone", "default")
            }
        )
    
    async def get_usage_stats(self) -> UsageStats:
        """Get Bright Data usage statistics"""
        # Would call actual API
        return UsageStats(
            bandwidth_used_gb=45.7,
            bandwidth_limit_gb=100.0,
            requests_made=1250000,
            unique_ips_used=8500,
            success_rate=0.965,
            avg_response_time_ms=450
        )
    
    async def rotate_credentials(self) -> ProxyCredentials:
        """Rotate credentials"""
        # Implementation
        pass
    
    async def add_ip_whitelist(self, ips: List[str]) -> bool:
        """Add IPs to whitelist"""
        # Implementation
        return True


class OxylabsProvider(ProxyProvider):
    """Oxylabs integration"""
    
    def __init__(self, username: str, password: str):
        super().__init__(username, password)
        self.base_url = "https://api.oxylabs.io/v1"
        self.name = "Oxylabs"
    
    async def get_packages(self) -> List[ProxyPackage]:
        """Get Oxylabs packages"""
        packages = []
        
        # Datacenter proxies
        packages.append(ProxyPackage(
            id="oxy_datacenter_shared",
            name="Shared Datacenter",
            type=ProxyType.DATACENTER,
            price_per_gb=Decimal("0.30"),
            min_purchase=Decimal("100"),
            locations=["US", "UK", "DE", "NL", "FR", "CA", "SG", "JP", "AU"],
            features=["High speed", "99.9% uptime", "Instant delivery"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD],
            rotation_type="rotating",
            pool_size=100000
        ))
        
        # Residential proxies
        packages.append(ProxyPackage(
            id="oxy_residential_premium",
            name="Residential Proxies",
            type=ProxyType.RESIDENTIAL,
            price_per_gb=Decimal("12.00"),
            min_purchase=Decimal("20"),
            locations=["195 countries", "City targeting", "State targeting"],
            features=["100M+ IPs", "Sticky sessions", "Real residential"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD],
            rotation_type="rotating",
            pool_size=100000000
        ))
        
        # Mobile proxies
        packages.append(ProxyPackage(
            id="oxy_mobile_proxies",
            name="Mobile Proxies",
            type=ProxyType.MOBILE,
            price_per_gb=Decimal("20.00"),
            min_purchase=Decimal("10"),
            locations=["US", "UK", "DE", "FR", "IT", "ES"],
            features=["Real mobile IPs", "Carrier targeting", "ASN targeting"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD],
            rotation_type="rotating"
        ))
        
        # ISP proxies
        packages.append(ProxyPackage(
            id="oxy_isp_proxies",
            name="ISP Proxies",
            type=ProxyType.ISP,
            price_per_ip=Decimal("15.00"),
            ip_count=1,
            locations=["US", "UK", "FR", "DE"],
            features=["Static residential", "Unlimited traffic", "Private pools"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD, AuthMethod.IP_WHITELIST],
            rotation_type="static"
        ))
        
        return packages
    
    async def purchase_package(self, package_id: str, **kwargs) -> ProxyCredentials:
        """Purchase Oxylabs package"""
        endpoint_map = {
            "oxy_datacenter_shared": "dc.oxylabs.io",
            "oxy_residential_premium": "pr.oxylabs.io",
            "oxy_mobile_proxies": "mobile.oxylabs.io",
            "oxy_isp_proxies": "isp.oxylabs.io"
        }
        
        return ProxyCredentials(
            provider=self.name,
            username=f"{self.api_key}-session-{int(time.time())}",
            password=self.api_secret,
            endpoint=endpoint_map.get(package_id, "pr.oxylabs.io"),
            port=7777,
            expires_at=datetime.utcnow() + timedelta(days=30),
            metadata={
                "package_id": package_id,
                "country": kwargs.get("country", "us")
            }
        )
    
    async def get_usage_stats(self) -> UsageStats:
        """Get usage statistics"""
        # API implementation
        return UsageStats(
            bandwidth_used_gb=67.3,
            bandwidth_limit_gb=200.0,
            requests_made=2340000,
            unique_ips_used=15600,
            success_rate=0.978,
            avg_response_time_ms=380
        )
    
    async def rotate_credentials(self) -> ProxyCredentials:
        """Rotate credentials"""
        pass
    
    async def add_ip_whitelist(self, ips: List[str]) -> bool:
        """Add IPs to whitelist"""
        return True


class IPRoyalProvider(ProxyProvider):
    """IPRoyal integration"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.iproyal.com/v1"
        self.name = "IPRoyal"
    
    async def get_packages(self) -> List[ProxyPackage]:
        """Get IPRoyal packages"""
        packages = []
        
        # Premium residential
        packages.append(ProxyPackage(
            id="ipr_residential_premium",
            name="Premium Residential",
            type=ProxyType.RESIDENTIAL,
            price_per_gb=Decimal("7.00"),
            min_purchase=Decimal("1"),
            locations=["195 countries", "City level", "State level"],
            features=["Rotating IPs", "Sticky sessions", "SOCKS5 support"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD],
            rotation_type="rotating",
            pool_size=2000000
        ))
        
        # Datacenter proxies
        packages.append(ProxyPackage(
            id="ipr_datacenter_sneaker",
            name="Sneaker Datacenter",
            type=ProxyType.DATACENTER,
            price_per_ip=Decimal("1.80"),
            ip_count=1,
            locations=["US", "UK", "DE", "NL"],
            features=["High speed", "Low latency", "Sneaker sites optimized"],
            auth_methods=[AuthMethod.USERNAME_PASSWORD, AuthMethod.IP_WHITELIST],
            rotation_type="static"
        ))
        
        # Static residential
        packages.append(ProxyPackage(
            id="ipr_static_residential",
            name="Static Residential",
            type=ProxyType.STATIC_RESIDENTIAL,
            price_per_ip=Decimal("2.50"),
            ip_count=1,
            locations=["US", "UK", "CA", "AU"],
            features=["ISP IPs", "Unlimited bandwidth", "30-day minimum"],
            auth_methods=[AuthMethod.IP_WHITELIST],
            rotation_type="static"
        ))
        
        return packages
    
    async def purchase_package(self, package_id: str, **kwargs) -> ProxyCredentials:
        """Purchase IPRoyal package"""
        endpoint_map = {
            "ipr_residential_premium": "geo.iproyal.com",
            "ipr_datacenter_sneaker": "dc.iproyal.com",
            "ipr_static_residential": "static.iproyal.com"
        }
        
        return ProxyCredentials(
            provider=self.name,
            username=f"user_{self.api_key[:8]}",
            password=hashlib.md5(self.api_key.encode()).hexdigest(),
            endpoint=endpoint_map.get(package_id, "geo.iproyal.com"),
            port=12321,
            expires_at=datetime.utcnow() + timedelta(days=30),
            metadata={"package_id": package_id}
        )
    
    async def get_usage_stats(self) -> UsageStats:
        """Get usage statistics"""
        return UsageStats(
            bandwidth_used_gb=12.5,
            requests_made=450000,
            unique_ips_used=3200,
            success_rate=0.945,
            avg_response_time_ms=520
        )
    
    async def rotate_credentials(self) -> ProxyCredentials:
        """Rotate credentials"""
        pass
    
    async def add_ip_whitelist(self, ips: List[str]) -> bool:
        """Add IPs to whitelist"""
        return True


class ProxyProviderManager:
    """Manages multiple proxy providers"""
    
    def __init__(self):
        self.providers: Dict[str, ProxyProvider] = {}
        self.active_subscriptions: Dict[str, ProxyCredentials] = {}
        self.usage_cache: Dict[str, UsageStats] = {}
        self._usage_update_interval = timedelta(minutes=5)
        self._last_usage_update: Dict[str, datetime] = {}
    
    def register_provider(self, name: str, provider: ProxyProvider):
        """Register a proxy provider"""
        self.providers[name.lower()] = provider
        logger.info(f"Registered proxy provider: {name}")
    
    async def get_all_packages(self) -> Dict[str, List[ProxyPackage]]:
        """Get packages from all providers"""
        all_packages = {}
        
        for name, provider in self.providers.items():
            try:
                async with provider:
                    packages = await provider.get_packages()
                    all_packages[name] = packages
            except Exception as e:
                logger.error(f"Error fetching packages from {name}: {e}")
                all_packages[name] = []
        
        return all_packages
    
    async def find_best_package(self,
                              proxy_type: ProxyType,
                              budget: Decimal,
                              location: Optional[str] = None,
                              min_pool_size: Optional[int] = None) -> Optional[Tuple[str, ProxyPackage]]:
        """Find best package matching criteria"""
        best_package = None
        best_provider = None
        best_value = float('inf')
        
        all_packages = await self.get_all_packages()
        
        for provider_name, packages in all_packages.items():
            for package in packages:
                # Check type
                if package.type != proxy_type:
                    continue
                
                # Check budget
                if package.total_price > budget:
                    continue
                
                # Check location
                if location and location not in package.locations and "Global" not in package.locations:
                    continue
                
                # Check pool size
                if min_pool_size and package.pool_size and package.pool_size < min_pool_size:
                    continue
                
                # Calculate value (price per GB or IP)
                if package.price_per_gb:
                    value = float(package.price_per_gb)
                elif package.price_per_ip:
                    value = float(package.price_per_ip)
                else:
                    continue
                
                # Check if better value
                if value < best_value:
                    best_value = value
                    best_package = package
                    best_provider = provider_name
        
        if best_package:
            return (best_provider, best_package)
        
        return None
    
    async def purchase_package(self,
                             provider_name: str,
                             package_id: str,
                             **kwargs) -> ProxyCredentials:
        """Purchase a proxy package"""
        provider = self.providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Provider {provider_name} not registered")
        
        async with provider:
            credentials = await provider.purchase_package(package_id, **kwargs)
            
            # Store active subscription
            subscription_id = f"{provider_name}_{package_id}_{int(time.time())}"
            self.active_subscriptions[subscription_id] = credentials
            
            logger.info(f"Purchased package {package_id} from {provider_name}")
            
            return credentials
    
    async def get_usage_stats(self, provider_name: str, force_refresh: bool = False) -> UsageStats:
        """Get usage statistics with caching"""
        # Check cache
        if not force_refresh and provider_name in self.usage_cache:
            last_update = self._last_usage_update.get(provider_name)
            if last_update and (datetime.utcnow() - last_update) < self._usage_update_interval:
                return self.usage_cache[provider_name]
        
        # Fetch fresh stats
        provider = self.providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Provider {provider_name} not registered")
        
        async with provider:
            stats = await provider.get_usage_stats()
            
            # Update cache
            self.usage_cache[provider_name] = stats
            self._last_usage_update[provider_name] = datetime.utcnow()
            
            return stats
    
    async def check_quota_alerts(self) -> List[Dict[str, Any]]:
        """Check for quota alerts across all providers"""
        alerts = []
        
        for provider_name in self.providers:
            try:
                stats = await self.get_usage_stats(provider_name)
                
                # Check bandwidth quota
                if stats.bandwidth_remaining_gb is not None:
                    usage_percent = (stats.bandwidth_used_gb / stats.bandwidth_limit_gb) * 100
                    
                    if usage_percent >= 90:
                        alerts.append({
                            'provider': provider_name,
                            'type': 'bandwidth',
                            'severity': 'critical' if usage_percent >= 95 else 'warning',
                            'message': f"{provider_name} bandwidth at {usage_percent:.1f}%",
                            'usage': stats.bandwidth_used_gb,
                            'limit': stats.bandwidth_limit_gb
                        })
                
                # Check request quota
                if stats.requests_limit:
                    request_percent = (stats.requests_made / stats.requests_limit) * 100
                    
                    if request_percent >= 90:
                        alerts.append({
                            'provider': provider_name,
                            'type': 'requests',
                            'severity': 'critical' if request_percent >= 95 else 'warning',
                            'message': f"{provider_name} requests at {request_percent:.1f}%",
                            'usage': stats.requests_made,
                            'limit': stats.requests_limit
                        })
                
            except Exception as e:
                logger.error(f"Error checking quota for {provider_name}: {e}")
        
        return alerts
    
    def get_active_subscriptions(self) -> Dict[str, ProxyCredentials]:
        """Get all active subscriptions"""
        # Filter out expired subscriptions
        active = {}
        now = datetime.utcnow()
        
        for sub_id, creds in self.active_subscriptions.items():
            if not creds.expires_at or creds.expires_at > now:
                active[sub_id] = creds
        
        return active
    
    async def rotate_all_credentials(self) -> Dict[str, ProxyCredentials]:
        """Rotate credentials for all providers"""
        rotated = {}
        
        for provider_name, provider in self.providers.items():
            try:
                async with provider:
                    new_creds = await provider.rotate_credentials()
                    rotated[provider_name] = new_creds
                    logger.info(f"Rotated credentials for {provider_name}")
            except Exception as e:
                logger.error(f"Failed to rotate credentials for {provider_name}: {e}")
        
        return rotated