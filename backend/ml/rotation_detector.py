#!/usr/bin/env python3
"""
Proxy Rotation Detection System
Identifies rotating proxies and residential proxy pools
"""

import asyncio
import hashlib
import ipaddress
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
import logging
from dataclasses import dataclass, field
import numpy as np
from scipy.stats import entropy
import jellyfish  # For string similarity

logger = logging.getLogger(__name__)


@dataclass
class ProxySession:
    """Represents a proxy session with metadata"""
    ip: str
    port: int
    first_seen: datetime
    last_seen: datetime
    exit_ips: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    tls_fingerprints: Set[str] = field(default_factory=set)
    asn_changes: int = 0
    location_changes: int = 0
    total_requests: int = 0
    
    @property
    def session_duration(self) -> timedelta:
        return self.last_seen - self.first_seen
    
    @property
    def rotation_score(self) -> float:
        """Calculate rotation likelihood score"""
        factors = [
            len(self.exit_ips) / max(1, self.total_requests),
            self.asn_changes / max(1, self.total_requests),
            self.location_changes / max(1, self.total_requests),
            len(self.tls_fingerprints) / max(1, len(self.exit_ips))
        ]
        return np.mean(factors)


@dataclass
class RotationPattern:
    """Detected rotation pattern"""
    pattern_type: str  # 'sequential', 'random', 'sticky', 'geographic'
    rotation_interval: Optional[timedelta]
    pool_size: int
    ip_range: Optional[str]
    confidence: float
    detected_at: datetime = field(default_factory=datetime.utcnow)
    evidence: Dict[str, Any] = field(default_factory=dict)


class ProxyRotationDetector:
    """
    Advanced detector for proxy rotation patterns
    Uses statistical analysis and ML techniques
    """
    
    def __init__(self):
        # Session tracking
        self.sessions: Dict[str, ProxySession] = {}
        self.ip_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Pattern detection
        self.rotation_patterns: Dict[str, List[RotationPattern]] = defaultdict(list)
        self.subnet_pools: Dict[str, Set[str]] = defaultdict(set)
        
        # Time windows for analysis
        self.time_windows = [
            timedelta(minutes=1),
            timedelta(minutes=5),
            timedelta(minutes=15),
            timedelta(hours=1)
        ]
        
        # Detection thresholds
        self.rotation_threshold = 0.7
        self.pool_min_size = 5
        self.sticky_session_duration = timedelta(minutes=30)
    
    async def analyze_request(self, 
                            proxy_ip: str,
                            proxy_port: int,
                            exit_ip: str,
                            headers: Dict[str, str],
                            tls_fingerprint: Optional[str] = None,
                            asn: Optional[str] = None,
                            location: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a single proxy request for rotation patterns
        """
        session_key = f"{proxy_ip}:{proxy_port}"
        current_time = datetime.utcnow()
        
        # Update or create session
        if session_key not in self.sessions:
            self.sessions[session_key] = ProxySession(
                ip=proxy_ip,
                port=proxy_port,
                first_seen=current_time,
                last_seen=current_time
            )
        
        session = self.sessions[session_key]
        
        # Track changes
        prev_exit_count = len(session.exit_ips)
        session.exit_ips.add(exit_ip)
        session.last_seen = current_time
        session.total_requests += 1
        
        if headers.get('User-Agent'):
            session.user_agents.add(headers['User-Agent'])
        
        if tls_fingerprint:
            session.tls_fingerprints.add(tls_fingerprint)
        
        # Track IP history with timestamp
        self.ip_history[session_key].append({
            'exit_ip': exit_ip,
            'timestamp': current_time,
            'asn': asn,
            'location': location
        })
        
        # Detect rotation
        rotation_detected = len(session.exit_ips) > prev_exit_count
        
        # Analyze patterns
        analysis = {
            'proxy': f"{proxy_ip}:{proxy_port}",
            'exit_ip': exit_ip,
            'rotation_detected': rotation_detected,
            'total_exit_ips': len(session.exit_ips),
            'rotation_score': session.rotation_score,
            'session_duration': str(session.session_duration),
            'patterns': []
        }
        
        # Detect patterns if enough data
        if session.total_requests >= 10:
            patterns = await self._detect_patterns(session_key)
            analysis['patterns'] = [
                {
                    'type': p.pattern_type,
                    'confidence': p.confidence,
                    'pool_size': p.pool_size,
                    'rotation_interval': str(p.rotation_interval) if p.rotation_interval else None
                }
                for p in patterns
            ]
        
        # Check for subnet pools
        subnet_info = self._analyze_subnet_pool(session)
        if subnet_info:
            analysis['subnet_pool'] = subnet_info
        
        return analysis
    
    async def _detect_patterns(self, session_key: str) -> List[RotationPattern]:
        """
        Detect rotation patterns from session history
        """
        patterns = []
        history = list(self.ip_history[session_key])
        
        if len(history) < 5:
            return patterns
        
        # Sequential pattern detection
        sequential = self._detect_sequential_pattern(history)
        if sequential:
            patterns.append(sequential)
        
        # Random pattern detection
        random_pattern = self._detect_random_pattern(history)
        if random_pattern:
            patterns.append(random_pattern)
        
        # Sticky session detection
        sticky = self._detect_sticky_pattern(history)
        if sticky:
            patterns.append(sticky)
        
        # Geographic rotation detection
        geo_pattern = self._detect_geographic_pattern(history)
        if geo_pattern:
            patterns.append(geo_pattern)
        
        # Time-based rotation
        time_pattern = self._detect_time_based_pattern(history)
        if time_pattern:
            patterns.append(time_pattern)
        
        return patterns
    
    def _detect_sequential_pattern(self, history: List[Dict]) -> Optional[RotationPattern]:
        """
        Detect sequential IP rotation (e.g., 1.2.3.1, 1.2.3.2, 1.2.3.3)
        """
        ips = [h['exit_ip'] for h in history[-20:]]  # Last 20 IPs
        
        if len(set(ips)) < 3:
            return None
        
        # Convert IPs to integers for sequence detection
        try:
            ip_ints = [int(ipaddress.ip_address(ip)) for ip in ips]
            
            # Check for arithmetic sequence
            differences = np.diff(ip_ints)
            unique_diffs = set(differences)
            
            # Sequential if consistent difference
            if len(unique_diffs) <= 2:  # Allow for some variation
                avg_interval = self._calculate_rotation_interval(history)
                
                return RotationPattern(
                    pattern_type='sequential',
                    rotation_interval=avg_interval,
                    pool_size=len(set(ips)),
                    ip_range=self._get_ip_range(ips),
                    confidence=0.85,
                    evidence={
                        'ip_differences': list(unique_diffs),
                        'sample_ips': ips[:5]
                    }
                )
        except:
            pass
        
        return None
    
    def _detect_random_pattern(self, history: List[Dict]) -> Optional[RotationPattern]:
        """
        Detect random rotation pattern using entropy
        """
        ips = [h['exit_ip'] for h in history[-50:]]
        
        if len(set(ips)) < self.pool_min_size:
            return None
        
        # Calculate entropy
        ip_counts = defaultdict(int)
        for ip in ips:
            ip_counts[ip] += 1
        
        probabilities = np.array(list(ip_counts.values())) / len(ips)
        ip_entropy = entropy(probabilities)
        
        # High entropy indicates randomness
        if ip_entropy > np.log(len(ip_counts)) * 0.8:
            return RotationPattern(
                pattern_type='random',
                rotation_interval=self._calculate_rotation_interval(history),
                pool_size=len(ip_counts),
                ip_range=self._get_ip_range(list(ip_counts.keys())),
                confidence=min(0.95, ip_entropy / np.log(len(ip_counts))),
                evidence={
                    'entropy': float(ip_entropy),
                    'unique_ips': len(ip_counts),
                    'distribution': dict(ip_counts)
                }
            )
        
        return None
    
    def _detect_sticky_pattern(self, history: List[Dict]) -> Optional[RotationPattern]:
        """
        Detect sticky session pattern (same IP for extended period)
        """
        if not history:
            return None
        
        # Group consecutive same IPs
        sticky_sessions = []
        current_ip = None
        session_start = None
        
        for entry in history:
            if entry['exit_ip'] != current_ip:
                if current_ip and session_start:
                    duration = entry['timestamp'] - session_start
                    if duration > self.sticky_session_duration:
                        sticky_sessions.append({
                            'ip': current_ip,
                            'duration': duration,
                            'start': session_start
                        })
                
                current_ip = entry['exit_ip']
                session_start = entry['timestamp']
        
        if len(sticky_sessions) >= 2:
            avg_duration = np.mean([s['duration'].total_seconds() for s in sticky_sessions])
            
            return RotationPattern(
                pattern_type='sticky',
                rotation_interval=timedelta(seconds=avg_duration),
                pool_size=len(set(s['ip'] for s in sticky_sessions)),
                ip_range=None,
                confidence=0.9,
                evidence={
                    'sticky_sessions': len(sticky_sessions),
                    'avg_session_duration': avg_duration,
                    'examples': sticky_sessions[:3]
                }
            )
        
        return None
    
    def _detect_geographic_pattern(self, history: List[Dict]) -> Optional[RotationPattern]:
        """
        Detect geographic-based rotation
        """
        locations = [(h.get('location', {}).get('country'), 
                     h.get('location', {}).get('city')) 
                    for h in history if h.get('location')]
        
        if len(locations) < 10:
            return None
        
        # Count location changes
        location_changes = 0
        prev_location = None
        
        for location in locations:
            if prev_location and location != prev_location:
                location_changes += 1
            prev_location = location
        
        # High location change rate indicates geographic rotation
        change_rate = location_changes / len(locations)
        
        if change_rate > 0.3:
            unique_countries = len(set(l[0] for l in locations if l[0]))
            unique_cities = len(set(l[1] for l in locations if l[1]))
            
            return RotationPattern(
                pattern_type='geographic',
                rotation_interval=self._calculate_rotation_interval(history),
                pool_size=unique_cities,
                ip_range=None,
                confidence=min(0.95, change_rate * 2),
                evidence={
                    'countries': unique_countries,
                    'cities': unique_cities,
                    'change_rate': change_rate,
                    'sample_locations': locations[:10]
                }
            )
        
        return None
    
    def _detect_time_based_pattern(self, history: List[Dict]) -> Optional[RotationPattern]:
        """
        Detect time-based rotation patterns
        """
        if len(history) < 20:
            return None
        
        # Calculate time between rotations
        rotation_times = []
        prev_ip = None
        prev_time = None
        
        for entry in history:
            if prev_ip and entry['exit_ip'] != prev_ip:
                rotation_times.append((entry['timestamp'] - prev_time).total_seconds())
            
            prev_ip = entry['exit_ip']
            prev_time = entry['timestamp']
        
        if len(rotation_times) < 5:
            return None
        
        # Check for regular intervals
        rotation_times = np.array(rotation_times)
        mean_interval = np.mean(rotation_times)
        std_interval = np.std(rotation_times)
        cv = std_interval / mean_interval if mean_interval > 0 else float('inf')
        
        # Low coefficient of variation indicates regular pattern
        if cv < 0.3:
            return RotationPattern(
                pattern_type='time_based',
                rotation_interval=timedelta(seconds=mean_interval),
                pool_size=len(set(h['exit_ip'] for h in history)),
                ip_range=None,
                confidence=max(0.7, 1 - cv),
                evidence={
                    'mean_interval': mean_interval,
                    'std_interval': std_interval,
                    'coefficient_variation': cv,
                    'samples': len(rotation_times)
                }
            )
        
        return None
    
    def _analyze_subnet_pool(self, session: ProxySession) -> Optional[Dict[str, Any]]:
        """
        Analyze if exit IPs belong to same subnet pool
        """
        if len(session.exit_ips) < 3:
            return None
        
        # Group IPs by /24 subnet
        subnets = defaultdict(list)
        
        for ip in session.exit_ips:
            try:
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                subnets[str(network)].append(ip)
            except:
                continue
        
        # Find dominant subnet
        if subnets:
            largest_subnet = max(subnets.items(), key=lambda x: len(x[1]))
            subnet, ips = largest_subnet
            
            if len(ips) >= self.pool_min_size:
                return {
                    'subnet': subnet,
                    'pool_size': len(ips),
                    'coverage': len(ips) / len(session.exit_ips),
                    'ips': sorted(ips)[:10]  # Sample
                }
        
        return None
    
    def _calculate_rotation_interval(self, history: List[Dict]) -> Optional[timedelta]:
        """
        Calculate average rotation interval
        """
        if len(history) < 2:
            return None
        
        intervals = []
        prev_entry = history[0]
        
        for entry in history[1:]:
            if entry['exit_ip'] != prev_entry['exit_ip']:
                interval = (entry['timestamp'] - prev_entry['timestamp']).total_seconds()
                intervals.append(interval)
            prev_entry = entry
        
        if intervals:
            return timedelta(seconds=np.median(intervals))
        
        return None
    
    def _get_ip_range(self, ips: List[str]) -> Optional[str]:
        """
        Get IP range from list of IPs
        """
        try:
            ip_objs = [ipaddress.ip_address(ip) for ip in ips]
            min_ip = min(ip_objs)
            max_ip = max(ip_objs)
            return f"{min_ip} - {max_ip}"
        except:
            return None
    
    async def get_rotation_summary(self, proxy_ip: str, proxy_port: int) -> Dict[str, Any]:
        """
        Get comprehensive rotation analysis for a proxy
        """
        session_key = f"{proxy_ip}:{proxy_port}"
        
        if session_key not in self.sessions:
            return {
                'status': 'no_data',
                'message': 'No session data available'
            }
        
        session = self.sessions[session_key]
        patterns = await self._detect_patterns(session_key)
        
        # Classify proxy type
        proxy_type = self._classify_proxy_type(session, patterns)
        
        return {
            'proxy': session_key,
            'type': proxy_type,
            'rotation_score': session.rotation_score,
            'total_ips': len(session.exit_ips),
            'session_duration': str(session.session_duration),
            'patterns': [
                {
                    'type': p.pattern_type,
                    'confidence': p.confidence,
                    'details': p.evidence
                }
                for p in patterns
            ],
            'recommendation': self._get_recommendation(proxy_type, patterns)
        }
    
    def _classify_proxy_type(self, session: ProxySession, patterns: List[RotationPattern]) -> str:
        """
        Classify proxy type based on behavior
        """
        if not patterns:
            return 'static'
        
        pattern_types = [p.pattern_type for p in patterns]
        
        if 'sticky' in pattern_types:
            return 'sticky_residential'
        elif 'sequential' in pattern_types:
            return 'datacenter_pool'
        elif 'random' in pattern_types and 'geographic' in pattern_types:
            return 'residential_pool'
        elif 'time_based' in pattern_types:
            return 'rotating_gateway'
        else:
            return 'unknown_rotation'
    
    def _get_recommendation(self, proxy_type: str, patterns: List[RotationPattern]) -> str:
        """
        Get usage recommendation based on proxy type
        """
        recommendations = {
            'static': "Good for long sessions, APIs requiring consistent IP",
            'sticky_residential': "Ideal for web scraping with session persistence",
            'datacenter_pool': "Fast but easily detected, use for non-sensitive tasks",
            'residential_pool': "Premium choice for avoiding detection",
            'rotating_gateway': "Good for high-volume requests, may break sessions",
            'unknown_rotation': "Monitor further before production use"
        }
        
        return recommendations.get(proxy_type, "Requires further analysis")