#!/usr/bin/env python3
"""
Database Service Layer for ProxyAssessmentTool
Handles database connections, transactions, and queries
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select, update, delete, and_, or_, func, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, selectinload, joinedload
from sqlalchemy.pool import NullPool, QueuePool
import asyncpg

from .models import (
    Base, Proxy, ProxyTest, ProxySource, ASNInfo, 
    ProxyBlacklist, ProxyProtocol, ProxyAnonymity,
    TestStatus, ScanHistory, PerformanceMetric
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Production-grade database service with async support"""
    
    def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 10):
        """
        Initialize database service
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
        """
        # Convert to async URL
        if database_url.startswith('postgresql://'):
            self.async_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
        else:
            self.async_url = database_url
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            self.async_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False           # Set to True for SQL debugging
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = {}
    
    async def initialize(self):
        """Initialize database (create tables if needed)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def session(self):
        """Provide a transactional session scope"""
        async with self.async_session() as session:
            async with session.begin():
                yield session
    
    # Proxy management methods
    
    async def upsert_proxy(self, 
                          ip: str, 
                          port: int, 
                          protocol: ProxyProtocol,
                          source_name: Optional[str] = None,
                          **kwargs) -> Proxy:
        """
        Insert or update a proxy record
        
        Args:
            ip: Proxy IP address
            port: Proxy port
            protocol: Proxy protocol
            source_name: Source name for the proxy
            **kwargs: Additional proxy attributes
        
        Returns:
            Proxy instance
        """
        async with self.session() as session:
            # Check if proxy exists
            stmt = select(Proxy).where(
                and_(
                    Proxy.ip == ip,
                    Proxy.port == port,
                    Proxy.protocol == protocol
                )
            )
            result = await session.execute(stmt)
            proxy = result.scalar_one_or_none()
            
            if proxy:
                # Update existing proxy
                proxy.last_seen_at = datetime.utcnow()
                proxy.times_seen += 1
                
                # Update other fields if provided
                for key, value in kwargs.items():
                    if hasattr(proxy, key) and value is not None:
                        setattr(proxy, key, value)
            else:
                # Create new proxy
                proxy = Proxy(
                    ip=ip,
                    port=port,
                    protocol=protocol,
                    **kwargs
                )
                
                # Link to source if provided
                if source_name:
                    source = await self._get_or_create_source(session, source_name)
                    proxy.source_id = source.id
                
                session.add(proxy)
            
            await session.commit()
            return proxy
    
    async def get_proxy(self, proxy_id: UUID) -> Optional[Proxy]:
        """Get proxy by ID"""
        async with self.session() as session:
            stmt = select(Proxy).where(Proxy.id == proxy_id).options(
                selectinload(Proxy.tests),
                selectinload(Proxy.asn_info)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_proxies(self,
                          protocol: Optional[ProxyProtocol] = None,
                          country_code: Optional[str] = None,
                          is_working: Optional[bool] = None,
                          is_mobile: Optional[bool] = None,
                          min_success_rate: Optional[float] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[Proxy]:
        """
        Find proxies with filters
        
        Args:
            protocol: Filter by protocol
            country_code: Filter by country
            is_working: Filter by working status
            is_mobile: Filter by mobile status
            min_success_rate: Minimum success rate
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List of proxies
        """
        async with self.session() as session:
            stmt = select(Proxy)
            
            # Apply filters
            conditions = []
            
            if protocol:
                conditions.append(Proxy.protocol == protocol)
            
            if country_code:
                conditions.append(Proxy.country_code == country_code)
            
            if is_mobile is not None:
                conditions.append(Proxy.is_mobile == is_mobile)
            
            if is_working is not None:
                if is_working:
                    conditions.append(Proxy.times_working > 0)
                else:
                    conditions.append(Proxy.times_working == 0)
            
            if min_success_rate is not None:
                # Calculate success rate in query
                conditions.append(
                    (Proxy.times_working.cast(Float) / Proxy.times_tested) >= min_success_rate / 100
                )
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Order by success rate descending
            stmt = stmt.order_by(
                (Proxy.times_working.cast(Float) / func.nullif(Proxy.times_tested, 0)).desc().nullslast()
            ).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def save_test_result(self, 
                              proxy_id: UUID,
                              test_batch_id: UUID,
                              test_result: Dict[str, Any]) -> ProxyTest:
        """
        Save proxy test result
        
        Args:
            proxy_id: Proxy ID
            test_batch_id: Test batch ID
            test_result: Test result data
            
        Returns:
            ProxyTest instance
        """
        async with self.session() as session:
            # Create test record
            test = ProxyTest(
                proxy_id=proxy_id,
                test_id=test_batch_id,
                status=TestStatus.COMPLETED,
                is_working=test_result.get('working', False),
                response_time_ms=test_result.get('response_time'),
                exit_ip=test_result.get('exit_ip'),
                detected_protocol=test_result.get('protocol'),
                anonymity_level=test_result.get('anonymity'),
                download_speed_mbps=test_result.get('download_speed_mbps'),
                upload_speed_mbps=test_result.get('upload_speed_mbps'),
                avg_latency_ms=test_result.get('avg_latency_ms'),
                jitter_ms=test_result.get('jitter_ms'),
                packet_loss_percent=test_result.get('packet_loss'),
                stability_score=test_result.get('stability_score'),
                dns_leak_detected=test_result.get('dns_leak'),
                ip_leak_detected=test_result.get('ip_leak'),
                ssl_intercepted=test_result.get('ssl_intercepted'),
                fraud_score=test_result.get('fraud_score'),
                raw_results=test_result
            )
            
            session.add(test)
            
            # Update proxy statistics
            proxy = await session.get(Proxy, proxy_id)
            if proxy:
                proxy.times_tested += 1
                proxy.last_tested_at = datetime.utcnow()
                if test.is_working:
                    proxy.times_working += 1
            
            await session.commit()
            return test
    
    async def get_proxy_stats(self, proxy_id: UUID, days: int = 7) -> Dict[str, Any]:
        """
        Get proxy statistics for the last N days
        
        Args:
            proxy_id: Proxy ID
            days: Number of days to look back
            
        Returns:
            Statistics dictionary
        """
        async with self.session() as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get test statistics
            stmt = select(
                func.count(ProxyTest.id).label('total_tests'),
                func.count(ProxyTest.id).filter(ProxyTest.is_working == True).label('successful_tests'),
                func.avg(ProxyTest.response_time_ms).label('avg_response_time'),
                func.avg(ProxyTest.download_speed_mbps).label('avg_download_speed'),
                func.avg(ProxyTest.stability_score).label('avg_stability')
            ).where(
                and_(
                    ProxyTest.proxy_id == proxy_id,
                    ProxyTest.tested_at >= since
                )
            )
            
            result = await session.execute(stmt)
            stats = result.one()
            
            return {
                'total_tests': stats.total_tests or 0,
                'successful_tests': stats.successful_tests or 0,
                'success_rate': (stats.successful_tests / stats.total_tests * 100) if stats.total_tests > 0 else 0,
                'avg_response_time': float(stats.avg_response_time) if stats.avg_response_time else 0,
                'avg_download_speed': float(stats.avg_download_speed) if stats.avg_download_speed else 0,
                'avg_stability': float(stats.avg_stability) if stats.avg_stability else 0
            }
    
    async def blacklist_proxy(self,
                             ip: str,
                             port: Optional[int] = None,
                             reason: str = "Manual blacklist",
                             severity: str = "medium",
                             expires_in_days: Optional[int] = None,
                             created_by: Optional[str] = None) -> ProxyBlacklist:
        """
        Add proxy to blacklist
        
        Args:
            ip: IP address to blacklist
            port: Optional port (blacklist all ports if None)
            reason: Blacklist reason
            severity: Severity level
            expires_in_days: Days until expiry (permanent if None)
            created_by: User who created the entry
            
        Returns:
            ProxyBlacklist instance
        """
        async with self.session() as session:
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            blacklist = ProxyBlacklist(
                ip=ip,
                port=port,
                reason=reason,
                severity=severity,
                expires_at=expires_at,
                created_by=created_by
            )
            
            session.add(blacklist)
            await session.commit()
            
            # Clear cache
            self._clear_cache('blacklist')
            
            return blacklist
    
    async def is_blacklisted(self, ip: str, port: Optional[int] = None) -> bool:
        """Check if IP/port is blacklisted"""
        # Check cache first
        cache_key = f"blacklist:{ip}:{port}"
        if cache_key in self._cache:
            if datetime.utcnow() < self._cache_ttl.get(cache_key, datetime.min):
                return self._cache[cache_key]
        
        async with self.session() as session:
            conditions = [ProxyBlacklist.ip == ip]
            
            if port:
                # Check specific port or all ports (port = None in blacklist)
                conditions.append(
                    or_(
                        ProxyBlacklist.port == port,
                        ProxyBlacklist.port.is_(None)
                    )
                )
            
            # Exclude expired entries
            conditions.append(
                or_(
                    ProxyBlacklist.expires_at.is_(None),
                    ProxyBlacklist.expires_at > datetime.utcnow()
                )
            )
            
            stmt = select(ProxyBlacklist).where(and_(*conditions)).limit(1)
            result = await session.execute(stmt)
            is_blacklisted = result.scalar_one_or_none() is not None
            
            # Cache result
            self._cache[cache_key] = is_blacklisted
            self._cache_ttl[cache_key] = datetime.utcnow() + timedelta(minutes=5)
            
            return is_blacklisted
    
    async def record_scan(self,
                         scan_type: str,
                         targets_scanned: int,
                         proxies_found: int,
                         duration_seconds: int,
                         configuration: Dict[str, Any],
                         error: Optional[str] = None,
                         created_by: Optional[str] = None) -> ScanHistory:
        """Record scan history"""
        async with self.session() as session:
            scan = ScanHistory(
                scan_type=scan_type,
                targets_scanned=targets_scanned,
                proxies_found=proxies_found,
                duration_seconds=duration_seconds,
                configuration=configuration,
                completed_at=datetime.utcnow() if not error else None,
                error_message=error,
                created_by=created_by
            )
            
            session.add(scan)
            await session.commit()
            return scan
    
    async def record_metric(self,
                           name: str,
                           value: float,
                           unit: Optional[str] = None,
                           tags: Optional[Dict[str, Any]] = None):
        """Record performance metric"""
        async with self.session() as session:
            metric = PerformanceMetric(
                metric_name=name,
                metric_value=value,
                metric_unit=unit,
                tags=tags or {}
            )
            
            session.add(metric)
            await session.commit()
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old test data and metrics"""
        async with self.session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old test results
            stmt = delete(ProxyTest).where(ProxyTest.tested_at < cutoff_date)
            await session.execute(stmt)
            
            # Delete old metrics
            stmt = delete(PerformanceMetric).where(PerformanceMetric.recorded_at < cutoff_date)
            await session.execute(stmt)
            
            # Delete expired blacklist entries
            stmt = delete(ProxyBlacklist).where(
                and_(
                    ProxyBlacklist.expires_at.isnot(None),
                    ProxyBlacklist.expires_at < datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            await session.commit()
            logger.info(f"Cleaned up data older than {days} days")
    
    # Private helper methods
    
    async def _get_or_create_source(self, session: AsyncSession, name: str) -> ProxySource:
        """Get or create proxy source"""
        stmt = select(ProxySource).where(ProxySource.name == name)
        result = await session.execute(stmt)
        source = result.scalar_one_or_none()
        
        if not source:
            source = ProxySource(name=name)
            session.add(source)
            await session.flush()
        
        return source
    
    def _clear_cache(self, prefix: Optional[str] = None):
        """Clear cache entries"""
        if prefix:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]
                self._cache_ttl.pop(key, None)
        else:
            self._cache.clear()
            self._cache_ttl.clear()


# Singleton instance
_db_service: Optional[DatabaseService] = None


def get_database_service(database_url: str) -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(database_url)
    return _db_service