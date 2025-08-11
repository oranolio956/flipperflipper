#!/usr/bin/env python3
"""
SQLAlchemy ORM Models for ProxyAssessmentTool
Production-grade database models with full type hints
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, 
    UniqueConstraint, Index, CheckConstraint, Numeric, Text,
    Enum as SQLEnum, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from geoalchemy2 import Geography

Base = declarative_base()


class ProxyProtocol(enum.Enum):
    """Proxy protocol types"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyAnonymity(enum.Enum):
    """Proxy anonymity levels"""
    TRANSPARENT = "transparent"
    ANONYMOUS = "anonymous"
    ELITE = "elite"


class TestStatus(enum.Enum):
    """Test execution status"""
    PENDING = "pending"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class ASNInfo(Base):
    """Autonomous System Number information"""
    __tablename__ = 'asn_info'
    
    asn = Column(String(20), primary_key=True)
    name = Column(String(255), nullable=False)
    organization = Column(String(255))
    country_code = Column(String(2))
    is_hosting = Column(Boolean, default=False)
    is_vpn_provider = Column(Boolean, default=False)
    reputation_score = Column(Numeric(3, 2), CheckConstraint('reputation_score >= 0 AND reputation_score <= 1'))
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    proxies = relationship("Proxy", back_populates="asn_info")
    
    # Indexes
    __table_args__ = (
        Index('idx_asn_reputation', 'reputation_score'),
        Index('idx_asn_type', 'is_hosting', 'is_vpn_provider'),
    )


class ProxySource(Base):
    """Proxy providers/sources"""
    __tablename__ = 'proxy_sources'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    url = Column(String(500))
    is_active = Column(Boolean, default=True)
    success_rate = Column(Numeric(5, 2), default=0.00)
    last_fetch_at = Column(DateTime(timezone=True))
    last_success_at = Column(DateTime(timezone=True))
    total_fetches = Column(Integer, default=0)
    successful_fetches = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    
    # Relationships
    proxies = relationship("Proxy", back_populates="source")
    
    # Indexes
    __table_args__ = (
        Index('idx_source_active', 'is_active', 'last_fetch_at'),
    )
    
    def update_fetch_stats(self, success: bool):
        """Update fetch statistics"""
        self.total_fetches += 1
        self.last_fetch_at = datetime.utcnow()
        if success:
            self.successful_fetches += 1
            self.last_success_at = datetime.utcnow()
        self.success_rate = (self.successful_fetches / self.total_fetches) * 100


class Proxy(Base):
    """Main proxy records"""
    __tablename__ = 'proxies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ip = Column(INET, nullable=False)
    port = Column(Integer, nullable=False, CheckConstraint('port > 0 AND port <= 65535'))
    protocol = Column(SQLEnum(ProxyProtocol), nullable=False)
    anonymity_level = Column(SQLEnum(ProxyAnonymity))
    asn = Column(String(20), ForeignKey('asn_info.asn'))
    source_id = Column(UUID(as_uuid=True), ForeignKey('proxy_sources.id'))
    
    # Geolocation
    country_code = Column(String(2))
    city = Column(String(100))
    region = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    location = Column(Geography(geometry_type='POINT', srid=4326))
    
    # Network info
    isp = Column(String(255))
    organization = Column(String(255))
    is_mobile = Column(Boolean, default=False)
    is_hosting = Column(Boolean, default=False)
    is_residential = Column(Boolean, default=False)
    
    # Metadata
    first_seen_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    last_tested_at = Column(DateTime(timezone=True))
    times_seen = Column(Integer, default=1)
    times_tested = Column(Integer, default=0)
    times_working = Column(Integer, default=0)
    
    # Relationships
    asn_info = relationship("ASNInfo", back_populates="proxies")
    source = relationship("ProxySource", back_populates="proxies")
    tests = relationship("ProxyTest", back_populates="proxy", cascade="all, delete-orphan")
    blacklist_entries = relationship("ProxyBlacklist", back_populates="proxy")
    user_list_items = relationship("UserProxyListItem", back_populates="proxy")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('ip', 'port', 'protocol', name='unique_proxy'),
        Index('idx_proxy_working', 'times_working', 'times_tested'),
        Index('idx_proxy_last_tested', 'last_tested_at'),
        Index('idx_proxy_country', 'country_code'),
        Index('idx_proxy_protocol', 'protocol'),
        Index('idx_proxy_composite', 'protocol', 'country_code', 'is_mobile'),
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.times_tested == 0:
            return 0.0
        return (self.times_working / self.times_tested) * 100
    
    @validates('ip')
    def validate_ip(self, key, ip):
        """Validate IP address format"""
        # PostgreSQL INET type handles validation
        return ip
    
    def __repr__(self):
        return f"<Proxy {self.protocol.value}://{self.ip}:{self.port}>"


class ProxyTest(Base):
    """Proxy test results"""
    __tablename__ = 'proxy_tests'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    proxy_id = Column(UUID(as_uuid=True), ForeignKey('proxies.id', ondelete='CASCADE'), nullable=False)
    test_id = Column(UUID(as_uuid=True), nullable=False)  # Groups tests in same batch
    status = Column(SQLEnum(TestStatus), nullable=False, default=TestStatus.PENDING)
    
    # Basic test results
    is_working = Column(Boolean, default=False)
    response_time_ms = Column(Integer)
    exit_ip = Column(INET)
    detected_protocol = Column(SQLEnum(ProxyProtocol))
    anonymity_level = Column(SQLEnum(ProxyAnonymity))
    
    # Speed test results
    download_speed_mbps = Column(Numeric(10, 2))
    upload_speed_mbps = Column(Numeric(10, 2))
    
    # Stability metrics
    avg_latency_ms = Column(Numeric(10, 2))
    min_latency_ms = Column(Numeric(10, 2))
    max_latency_ms = Column(Numeric(10, 2))
    jitter_ms = Column(Numeric(10, 2))
    packet_loss_percent = Column(Numeric(5, 2))
    stability_score = Column(Numeric(3, 2))
    
    # Security tests
    dns_leak_detected = Column(Boolean, default=False)
    ip_leak_detected = Column(Boolean, default=False)
    ssl_intercepted = Column(Boolean, default=False)
    webrtc_leak_detected = Column(Boolean, default=False)
    
    # Advanced results
    ja3_fingerprint = Column(String(32))
    ja3s_fingerprint = Column(String(32))
    tls_version = Column(String(10))
    cipher_suite = Column(String(100))
    
    # Fraud/risk assessment
    fraud_score = Column(Numeric(3, 2), CheckConstraint('fraud_score >= 0 AND fraud_score <= 1'))
    risk_level = Column(String(20))
    risk_factors = Column(JSONB)
    
    # Test metadata
    error_message = Column(Text)
    test_duration_ms = Column(Integer)
    tested_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    
    # Additional data
    raw_results = Column(JSONB)
    
    # Relationships
    proxy = relationship("Proxy", back_populates="tests")
    
    # Indexes
    __table_args__ = (
        Index('idx_test_proxy', 'proxy_id', 'tested_at'),
        Index('idx_test_batch', 'test_id'),
        Index('idx_test_working', 'is_working', 'tested_at'),
        Index('idx_test_timestamp', 'tested_at'),
    )
    
    @property
    def has_security_issues(self) -> bool:
        """Check if any security issues detected"""
        return any([
            self.dns_leak_detected,
            self.ip_leak_detected,
            self.ssl_intercepted,
            self.webrtc_leak_detected
        ])


class ProxyBlacklist(Base):
    """Blacklisted proxies"""
    __tablename__ = 'proxy_blacklist'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ip = Column(INET, nullable=False)
    port = Column(Integer)
    reason = Column(String(255), nullable=False)
    source = Column(String(100))
    severity = Column(String(20), default='medium')
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    created_by = Column(String(100))
    
    # Relationships
    proxy = relationship("Proxy", back_populates="blacklist_entries")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('ip', 'port', name='unique_blacklist'),
        Index('idx_blacklist_ip', 'ip'),
        Index('idx_blacklist_expires', 'expires_at', postgresql_where='expires_at IS NOT NULL'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if blacklist entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class UserProxyList(Base):
    """User-created proxy lists"""
    __tablename__ = 'user_proxy_lists'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    items = relationship("UserProxyListItem", back_populates="list", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='unique_user_list'),
    )


class UserProxyListItem(Base):
    """Items in user proxy lists"""
    __tablename__ = 'user_proxy_list_items'
    
    list_id = Column(UUID(as_uuid=True), ForeignKey('user_proxy_lists.id', ondelete='CASCADE'), primary_key=True)
    proxy_id = Column(UUID(as_uuid=True), ForeignKey('proxies.id', ondelete='CASCADE'), primary_key=True)
    notes = Column(Text)
    tags = Column(ARRAY(Text))
    added_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    
    # Relationships
    list = relationship("UserProxyList", back_populates="items")
    proxy = relationship("Proxy", back_populates="user_list_items")


class APIUsage(Base):
    """API usage tracking"""
    __tablename__ = 'api_usage'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    api_key = Column(String(255), nullable=False)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_body = Column(JSONB)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key', 'api_key', 'created_at'),
        Index('idx_api_endpoint', 'endpoint', 'created_at'),
        Index('idx_api_timestamp', 'created_at'),
    )


class ScanHistory(Base):
    """Scanning history and statistics"""
    __tablename__ = 'scan_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_type = Column(String(50), nullable=False)
    targets_scanned = Column(Integer, default=0)
    proxies_found = Column(Integer, default=0)
    duration_seconds = Column(Integer)
    configuration = Column(JSONB)
    started_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_by = Column(String(100))
    
    # Indexes
    __table_args__ = (
        Index('idx_scan_type', 'scan_type', 'started_at'),
    )


class PerformanceMetric(Base):
    """Performance metrics for monitoring"""
    __tablename__ = 'performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(20, 4), nullable=False)
    metric_unit = Column(String(20))
    tags = Column(JSONB)
    recorded_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_name', 'metric_name', 'recorded_at'),
        Index('idx_metrics_time', 'recorded_at'),
    )


# Helper functions for database operations
def create_database_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)


def drop_database_tables(engine):
    """Drop all database tables"""
    Base.metadata.drop_all(engine)