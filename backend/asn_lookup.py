#!/usr/bin/env python3
"""
ASN Lookup Service - Real BGP Data
Uses multiple data sources for accurate ASN information
"""

import asyncio
import aiohttp
import ipaddress
import json
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import pyasn
import socket
import struct

logger = logging.getLogger(__name__)


@dataclass
class ASNInfo:
    """ASN information for an IP or range"""
    asn: str
    name: str
    country: str
    ip_range: str
    description: str = ""
    abuse_contact: Optional[str] = None
    is_hosting: bool = False
    is_vpn_provider: bool = False
    reputation_score: float = 0.5  # 0-1, higher = more likely to have proxies


class ASNLookupService:
    """Real ASN lookup using multiple data sources"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(hours=24)
        
        # Known hosting/VPN ASNs with high proxy likelihood
        self.known_proxy_asns = {
            # Major cloud providers
            'AS16509': ASNInfo('AS16509', 'Amazon Web Services', 'US', '0.0.0.0/0', 'AWS EC2', is_hosting=True, reputation_score=0.8),
            'AS15169': ASNInfo('AS15169', 'Google Cloud', 'US', '0.0.0.0/0', 'Google Cloud Platform', is_hosting=True, reputation_score=0.7),
            'AS8075': ASNInfo('AS8075', 'Microsoft Azure', 'US', '0.0.0.0/0', 'Microsoft Azure', is_hosting=True, reputation_score=0.7),
            'AS14061': ASNInfo('AS14061', 'DigitalOcean', 'US', '0.0.0.0/0', 'DigitalOcean', is_hosting=True, reputation_score=0.9),
            'AS16276': ASNInfo('AS16276', 'OVH', 'FR', '0.0.0.0/0', 'OVH Hosting', is_hosting=True, reputation_score=0.85),
            'AS24940': ASNInfo('AS24940', 'Hetzner', 'DE', '0.0.0.0/0', 'Hetzner Online', is_hosting=True, reputation_score=0.8),
            'AS63949': ASNInfo('AS63949', 'Linode', 'US', '0.0.0.0/0', 'Linode LLC', is_hosting=True, reputation_score=0.85),
            'AS20473': ASNInfo('AS20473', 'Vultr', 'US', '0.0.0.0/0', 'Choopa LLC', is_hosting=True, reputation_score=0.9),
            
            # Known VPN/Proxy providers
            'AS9009': ASNInfo('AS9009', 'M247', 'GB', '0.0.0.0/0', 'M247 Ltd', is_vpn_provider=True, reputation_score=0.95),
            'AS212238': ASNInfo('AS212238', 'DataCamp', 'GB', '0.0.0.0/0', 'DataCamp Limited', is_vpn_provider=True, reputation_score=0.95),
            'AS51167': ASNInfo('AS51167', 'Contabo', 'DE', '0.0.0.0/0', 'Contabo GmbH', is_hosting=True, reputation_score=0.9),
            'AS197540': ASNInfo('AS197540', 'Neterra', 'BG', '0.0.0.0/0', 'Neterra Ltd', is_hosting=True, reputation_score=0.85),
            
            # Residential ISPs (lower proxy likelihood)
            'AS7922': ASNInfo('AS7922', 'Comcast', 'US', '0.0.0.0/0', 'Comcast Cable', reputation_score=0.2),
            'AS701': ASNInfo('AS701', 'Verizon', 'US', '0.0.0.0/0', 'Verizon Business', reputation_score=0.2),
            'AS209': ASNInfo('AS209', 'CenturyLink', 'US', '0.0.0.0/0', 'CenturyLink', reputation_score=0.2),
        }
        
        # Initialize PyASN database (would need actual data file)
        self.pyasn_db = None
        
    async def lookup_ip(self, ip: str) -> Optional[ASNInfo]:
        """Look up ASN information for an IP address"""
        # Check cache
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.utcnow() - timestamp < self.cache_ttl:
                return cached_data
        
        # Try multiple data sources
        asn_info = None
        
        # 1. Try RIPE RIS API (real-time BGP data)
        asn_info = await self._lookup_ripe_ris(ip)
        
        # 2. Fallback to Team Cymru whois
        if not asn_info:
            asn_info = await self._lookup_team_cymru(ip)
        
        # 3. Fallback to ip-api.com
        if not asn_info:
            asn_info = await self._lookup_ip_api(ip)
        
        # Cache result
        if asn_info:
            self.cache[cache_key] = (asn_info, datetime.utcnow())
        
        return asn_info
    
    async def _lookup_ripe_ris(self, ip: str) -> Optional[ASNInfo]:
        """Query RIPE RIS Looking Glass API"""
        try:
            url = f"https://stat.ripe.net/data/prefix-overview/data.json?resource={ip}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'ok' and data.get('data'):
                            asn_data = data['data']['asns']
                            if asn_data:
                                asn = f"AS{asn_data[0]['asn']}"
                                holder = asn_data[0].get('holder', 'Unknown')
                                
                                # Check if it's a known ASN
                                if asn in self.known_proxy_asns:
                                    return self.known_proxy_asns[asn]
                                
                                # Create new ASN info
                                return ASNInfo(
                                    asn=asn,
                                    name=holder,
                                    country=data['data'].get('country_code', 'XX'),
                                    ip_range=data['data'].get('prefix', f"{ip}/32"),
                                    description=holder,
                                    reputation_score=self._calculate_reputation(holder)
                                )
        except Exception as e:
            logger.debug(f"RIPE RIS lookup failed for {ip}: {e}")
        
        return None
    
    async def _lookup_team_cymru(self, ip: str) -> Optional[ASNInfo]:
        """Query Team Cymru whois service"""
        try:
            # Reverse IP for DNS query
            octets = ip.split('.')
            reversed_ip = '.'.join(reversed(octets))
            query = f"{reversed_ip}.origin.asn.cymru.com"
            
            # DNS TXT query
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, socket.gethostbyname, query)
            
            # Parse result (format: "AS#### | IP/CIDR | CC | Registry | Date")
            if result:
                parts = result.split('|')
                if len(parts) >= 3:
                    asn = parts[0].strip()
                    ip_range = parts[1].strip()
                    country = parts[2].strip()
                    
                    # Check known ASNs
                    if asn in self.known_proxy_asns:
                        return self.known_proxy_asns[asn]
                    
                    return ASNInfo(
                        asn=asn,
                        name=f"AS{asn.replace('AS', '')}",
                        country=country,
                        ip_range=ip_range,
                        reputation_score=0.5
                    )
        except Exception as e:
            logger.debug(f"Team Cymru lookup failed for {ip}: {e}")
        
        return None
    
    async def _lookup_ip_api(self, ip: str) -> Optional[ASNInfo]:
        """Fallback to ip-api.com"""
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,as,org,isp,country,hosting,proxy"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            # Parse AS field (format: "AS#### Organization")
                            as_field = data.get('as', '')
                            asn = as_field.split()[0] if as_field else 'Unknown'
                            
                            # Check known ASNs
                            if asn in self.known_proxy_asns:
                                return self.known_proxy_asns[asn]
                            
                            return ASNInfo(
                                asn=asn,
                                name=data.get('org', 'Unknown'),
                                country=data.get('countryCode', 'XX'),
                                ip_range=f"{ip}/32",
                                description=data.get('isp', ''),
                                is_hosting=data.get('hosting', False),
                                is_vpn_provider=data.get('proxy', False),
                                reputation_score=self._calculate_reputation(
                                    data.get('org', ''),
                                    is_hosting=data.get('hosting', False),
                                    is_proxy=data.get('proxy', False)
                                )
                            )
        except Exception as e:
            logger.debug(f"ip-api lookup failed for {ip}: {e}")
        
        return None
    
    def _calculate_reputation(self, org_name: str, is_hosting: bool = None, is_proxy: bool = None) -> float:
        """Calculate reputation score based on organization name and flags"""
        score = 0.5  # Default neutral score
        
        # Check organization name for hosting keywords
        hosting_keywords = [
            'hosting', 'cloud', 'vps', 'server', 'datacenter', 
            'colocation', 'dedicated', 'virtual', 'compute'
        ]
        
        vpn_keywords = [
            'vpn', 'proxy', 'anonymiz', 'privacy', 'secure',
            'hide', 'tunnel', 'socks'
        ]
        
        residential_keywords = [
            'comcast', 'verizon', 'at&t', 'charter', 'cox',
            'spectrum', 'centurylink', 'frontier', 'broadband',
            'cable', 'dsl', 'fiber', 'telecom', 'residential'
        ]
        
        org_lower = org_name.lower()
        
        # Check for VPN/proxy providers (highest likelihood)
        if is_proxy or any(keyword in org_lower for keyword in vpn_keywords):
            score = 0.9
        # Check for hosting providers (high likelihood)
        elif is_hosting or any(keyword in org_lower for keyword in hosting_keywords):
            score = 0.8
        # Check for residential ISPs (low likelihood)
        elif any(keyword in org_lower for keyword in residential_keywords):
            score = 0.2
        
        return score
    
    async def get_high_value_ranges(self, min_reputation: float = 0.7) -> List[Dict]:
        """Get IP ranges with high proxy likelihood"""
        ranges = []
        
        for asn, info in self.known_proxy_asns.items():
            if info.reputation_score >= min_reputation:
                # Get actual IP ranges for this ASN
                # In production, this would query BGP data
                ranges.append({
                    'asn': asn,
                    'name': info.name,
                    'ranges': self._get_ip_ranges_for_asn(asn),
                    'reputation': info.reputation_score,
                    'type': 'vpn' if info.is_vpn_provider else 'hosting'
                })
        
        return ranges
    
    def _get_ip_ranges_for_asn(self, asn: str) -> List[str]:
        """Get IP ranges for an ASN (would query real BGP data)"""
        # Mock data for testing
        mock_ranges = {
            'AS14061': [  # DigitalOcean
                '104.248.0.0/18',
                '159.65.0.0/16',
                '167.172.0.0/16',
                '178.128.0.0/16'
            ],
            'AS16276': [  # OVH
                '51.15.0.0/16',
                '54.36.0.0/16',
                '91.121.0.0/16',
                '137.74.0.0/16'
            ],
            'AS16509': [  # AWS
                '52.0.0.0/11',
                '54.0.0.0/8',
                '3.0.0.0/9',
                '18.0.0.0/9'
            ]
        }
        
        return mock_ranges.get(asn, [f"0.0.0.0/0"])


# Test function
async def test_asn_lookup():
    """Test ASN lookup functionality"""
    print("=" * 70)
    print("ASN LOOKUP TEST")
    print("=" * 70)
    
    service = ASNLookupService()
    
    # Test IPs from different providers
    test_ips = [
        '104.248.1.1',     # DigitalOcean
        '51.15.1.1',       # OVH
        '8.8.8.8',         # Google DNS
        '1.1.1.1',         # Cloudflare
        '192.168.1.1',     # Private IP
    ]
    
    print("\n📍 Testing ASN lookups...")
    for ip in test_ips:
        print(f"\nLooking up {ip}...")
        info = await service.lookup_ip(ip)
        
        if info:
            print(f"  ASN: {info.asn}")
            print(f"  Name: {info.name}")
            print(f"  Country: {info.country}")
            print(f"  Reputation: {info.reputation_score:.2f}")
            print(f"  Is Hosting: {info.is_hosting}")
            print(f"  Is VPN: {info.is_vpn_provider}")
        else:
            print(f"  ❌ Lookup failed")
    
    # Test high-value ranges
    print("\n🎯 High-value proxy ranges:")
    ranges = await service.get_high_value_ranges()
    
    for range_info in ranges[:5]:
        print(f"\n{range_info['name']} ({range_info['asn']}):")
        print(f"  Type: {range_info['type']}")
        print(f"  Reputation: {range_info['reputation']:.2f}")
        print(f"  Sample ranges:")
        for ip_range in range_info['ranges'][:3]:
            print(f"    {ip_range}")
    
    print("\n✅ ASN lookup test complete!")


if __name__ == "__main__":
    asyncio.run(test_asn_lookup())