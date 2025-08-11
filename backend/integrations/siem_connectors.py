#!/usr/bin/env python3
"""
SIEM Integration Module
Supports Splunk, Elastic (ELK), Datadog, and more
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import logging
import uuid

import httpx
from elasticsearch import AsyncElasticsearch
from datadog import initialize as dd_initialize, api as dd_api, statsd

logger = logging.getLogger(__name__)


class EventSeverity(str, Enum):
    """Event severity levels for SIEM"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    DEBUG = "debug"


class EventCategory(str, Enum):
    """Event categories"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    FRAUD = "fraud"


@dataclass
class SIEMEvent:
    """SIEM event structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""
    severity: EventSeverity = EventSeverity.INFO
    category: EventCategory = EventCategory.OPERATIONAL
    
    # Event details
    title: str = ""
    description: str = ""
    source: str = "ProxyAssessmentTool"
    
    # Context data
    proxy_ip: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_type: Optional[str] = None
    
    # Metrics
    metrics: Dict[str, Union[int, float]] = field(default_factory=dict)
    
    # Additional fields
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Correlation
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_cef(self) -> str:
        """Convert to Common Event Format (CEF)"""
        severity_map = {
            EventSeverity.CRITICAL: 10,
            EventSeverity.HIGH: 8,
            EventSeverity.MEDIUM: 5,
            EventSeverity.LOW: 3,
            EventSeverity.INFO: 1,
            EventSeverity.DEBUG: 0
        }
        
        cef = f"CEF:0|ProxyAssessment|ProxyTool|2.0|{self.event_type}|{self.title}|{severity_map[self.severity]}|"
        
        # Add extension fields
        extensions = []
        if self.proxy_ip:
            extensions.append(f"src={self.proxy_ip}")
        if self.proxy_port:
            extensions.append(f"spt={self.proxy_port}")
        if self.description:
            extensions.append(f"msg={self.description.replace('|', '_')}")
        
        for key, value in self.attributes.items():
            extensions.append(f"cs1Label={key} cs1={value}")
        
        cef += " ".join(extensions)
        return cef
    
    def to_leef(self) -> str:
        """Convert to Log Event Extended Format (LEEF)"""
        leef = f"LEEF:2.0|ProxyAssessment|ProxyTool|2.0|{self.event_type}|"
        
        # Add fields
        fields = {
            'devTime': int(self.timestamp.timestamp() * 1000),
            'severity': self.severity.value,
            'category': self.category.value,
            'devEventId': self.id
        }
        
        if self.proxy_ip:
            fields['src'] = self.proxy_ip
        if self.proxy_port:
            fields['srcPort'] = self.proxy_port
        
        fields.update(self.attributes)
        
        field_str = "\t".join([f"{k}={v}" for k, v in fields.items()])
        return leef + field_str


class SIEMConnector(ABC):
    """Base class for SIEM connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = ""
        self.connected = False
        self._event_buffer: List[SIEMEvent] = []
        self._buffer_size = config.get('buffer_size', 1000)
        self._flush_interval = config.get('flush_interval', 60)
        self._last_flush = datetime.utcnow()
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to SIEM"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from SIEM"""
        pass
    
    @abstractmethod
    async def send_event(self, event: SIEMEvent) -> bool:
        """Send single event"""
        pass
    
    @abstractmethod
    async def send_batch(self, events: List[SIEMEvent]) -> bool:
        """Send batch of events"""
        pass
    
    async def buffer_event(self, event: SIEMEvent):
        """Buffer event for batch sending"""
        self._event_buffer.append(event)
        
        # Check if flush needed
        if len(self._event_buffer) >= self._buffer_size:
            await self.flush_buffer()
        elif (datetime.utcnow() - self._last_flush).seconds >= self._flush_interval:
            await self.flush_buffer()
    
    async def flush_buffer(self) -> bool:
        """Flush event buffer"""
        if not self._event_buffer:
            return True
        
        events = self._event_buffer.copy()
        self._event_buffer.clear()
        self._last_flush = datetime.utcnow()
        
        return await self.send_batch(events)
    
    def enrich_event(self, event: SIEMEvent) -> SIEMEvent:
        """Enrich event with common fields"""
        event.attributes['siem_connector'] = self.name
        event.attributes['environment'] = self.config.get('environment', 'production')
        event.attributes['region'] = self.config.get('region', 'us-east-1')
        event.attributes['instance_id'] = self.config.get('instance_id', 'default')
        
        return event


class SplunkConnector(SIEMConnector):
    """Splunk HTTP Event Collector (HEC) integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "Splunk"
        self.hec_url = config['hec_url']
        self.hec_token = config['hec_token']
        self.index = config.get('index', 'main')
        self.source_type = config.get('source_type', 'proxy_assessment')
        self._client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> bool:
        """Connect to Splunk HEC"""
        try:
            self._client = httpx.AsyncClient(
                headers={
                    'Authorization': f'Splunk {self.hec_token}',
                    'Content-Type': 'application/json'
                },
                timeout=30.0
            )
            
            # Test connection
            response = await self._client.get(f"{self.hec_url}/services/collector/health")
            self.connected = response.status_code == 200
            
            if self.connected:
                logger.info("Connected to Splunk HEC")
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to Splunk: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Splunk"""
        if self._client:
            await self._client.aclose()
        self.connected = False
    
    async def send_event(self, event: SIEMEvent) -> bool:
        """Send event to Splunk"""
        if not self.connected or not self._client:
            return False
        
        # Enrich event
        event = self.enrich_event(event)
        
        # Format for Splunk HEC
        splunk_event = {
            'time': event.timestamp.timestamp(),
            'host': event.source,
            'source': self.source_type,
            'sourcetype': self.source_type,
            'index': self.index,
            'event': {
                'event_id': event.id,
                'event_type': event.event_type,
                'severity': event.severity.value,
                'category': event.category.value,
                'title': event.title,
                'description': event.description,
                'proxy_ip': event.proxy_ip,
                'proxy_port': event.proxy_port,
                'proxy_type': event.proxy_type,
                'metrics': event.metrics,
                'tags': event.tags,
                **event.attributes
            }
        }
        
        try:
            response = await self._client.post(
                f"{self.hec_url}/services/collector/event",
                json=splunk_event
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send event to Splunk: {e}")
            return False
    
    async def send_batch(self, events: List[SIEMEvent]) -> bool:
        """Send batch of events to Splunk"""
        if not self.connected or not self._client:
            return False
        
        # Format events for batch
        batch_data = []
        for event in events:
            event = self.enrich_event(event)
            batch_data.append({
                'time': event.timestamp.timestamp(),
                'host': event.source,
                'source': self.source_type,
                'sourcetype': self.source_type,
                'index': self.index,
                'event': event.to_dict()
            })
        
        # Splunk expects newline-delimited JSON
        payload = '\n'.join([json.dumps(item) for item in batch_data])
        
        try:
            response = await self._client.post(
                f"{self.hec_url}/services/collector/event",
                content=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send batch to Splunk: {e}")
            return False


class ElasticConnector(SIEMConnector):
    """Elasticsearch/ELK Stack integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "Elastic"
        self.hosts = config['hosts']
        self.index_prefix = config.get('index_prefix', 'proxy-assessment')
        self.username = config.get('username')
        self.password = config.get('password')
        self.api_key = config.get('api_key')
        self.use_ssl = config.get('use_ssl', True)
        self.verify_certs = config.get('verify_certs', True)
        self._client: Optional[AsyncElasticsearch] = None
    
    async def connect(self) -> bool:
        """Connect to Elasticsearch"""
        try:
            # Build auth config
            auth_config = {}
            if self.api_key:
                auth_config['api_key'] = self.api_key
            elif self.username and self.password:
                auth_config['basic_auth'] = (self.username, self.password)
            
            # Create client
            self._client = AsyncElasticsearch(
                self.hosts,
                use_ssl=self.use_ssl,
                verify_certs=self.verify_certs,
                **auth_config
            )
            
            # Test connection
            info = await self._client.info()
            self.connected = True
            logger.info(f"Connected to Elasticsearch {info['version']['number']}")
            
            # Create index template
            await self._create_index_template()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Elasticsearch"""
        if self._client:
            await self._client.close()
        self.connected = False
    
    async def _create_index_template(self):
        """Create index template for proxy events"""
        template_name = f"{self.index_prefix}-template"
        
        template_body = {
            "index_patterns": [f"{self.index_prefix}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": "proxy-assessment-policy"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "event_id": {"type": "keyword"},
                        "event_type": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "proxy_ip": {"type": "ip"},
                        "proxy_port": {"type": "integer"},
                        "proxy_type": {"type": "keyword"},
                        "metrics": {"type": "object"},
                        "tags": {"type": "keyword"},
                        "correlation_id": {"type": "keyword"},
                        "trace_id": {"type": "keyword"},
                        "geo": {
                            "properties": {
                                "location": {"type": "geo_point"},
                                "country": {"type": "keyword"},
                                "city": {"type": "keyword"}
                            }
                        }
                    }
                }
            }
        }
        
        try:
            await self._client.indices.put_index_template(
                name=template_name,
                body=template_body
            )
            logger.info(f"Created Elasticsearch index template: {template_name}")
        except Exception as e:
            logger.error(f"Failed to create index template: {e}")
    
    async def send_event(self, event: SIEMEvent) -> bool:
        """Send event to Elasticsearch"""
        if not self.connected or not self._client:
            return False
        
        # Enrich event
        event = self.enrich_event(event)
        
        # Get index name (daily rotation)
        index_name = f"{self.index_prefix}-{datetime.utcnow().strftime('%Y.%m.%d')}"
        
        # Format document
        doc = {
            '@timestamp': event.timestamp,
            **event.to_dict()
        }
        
        try:
            response = await self._client.index(
                index=index_name,
                id=event.id,
                document=doc
            )
            
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Failed to send event to Elasticsearch: {e}")
            return False
    
    async def send_batch(self, events: List[SIEMEvent]) -> bool:
        """Send batch of events to Elasticsearch"""
        if not self.connected or not self._client:
            return False
        
        # Prepare bulk operations
        operations = []
        index_name = f"{self.index_prefix}-{datetime.utcnow().strftime('%Y.%m.%d')}"
        
        for event in events:
            event = self.enrich_event(event)
            
            # Index operation
            operations.append({
                "index": {
                    "_index": index_name,
                    "_id": event.id
                }
            })
            
            # Document
            operations.append({
                '@timestamp': event.timestamp,
                **event.to_dict()
            })
        
        try:
            response = await self._client.bulk(operations=operations)
            
            # Check for errors
            if response['errors']:
                error_count = sum(1 for item in response['items'] if 'error' in item.get('index', {}))
                logger.error(f"Bulk operation had {error_count} errors")
                return error_count == 0
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send batch to Elasticsearch: {e}")
            return False


class DatadogConnector(SIEMConnector):
    """Datadog integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "Datadog"
        self.api_key = config['api_key']
        self.app_key = config.get('app_key')
        self.site = config.get('site', 'datadoghq.com')
        self.tags = config.get('tags', [])
        self._statsd = None
    
    async def connect(self) -> bool:
        """Connect to Datadog"""
        try:
            # Initialize Datadog
            dd_initialize(
                api_key=self.api_key,
                app_key=self.app_key,
                host_name='proxy-assessment-tool',
                api_host=f"https://api.{self.site}"
            )
            
            # Initialize StatsD client
            self._statsd = statsd
            self._statsd.host = 'localhost'
            self._statsd.port = 8125
            
            # Test connection
            dd_api.Metric.send(
                metric='proxy.assessment.connection.test',
                points=1,
                tags=self.tags
            )
            
            self.connected = True
            logger.info("Connected to Datadog")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Datadog: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Datadog"""
        self.connected = False
    
    async def send_event(self, event: SIEMEvent) -> bool:
        """Send event to Datadog"""
        if not self.connected:
            return False
        
        # Enrich event
        event = self.enrich_event(event)
        
        # Create Datadog event
        dd_event = {
            'title': event.title,
            'text': event.description,
            'tags': self.tags + event.tags + [
                f"severity:{event.severity.value}",
                f"category:{event.category.value}",
                f"event_type:{event.event_type}"
            ],
            'alert_type': self._map_severity(event.severity),
            'source_type_name': 'proxy_assessment',
            'aggregation_key': event.correlation_id
        }
        
        # Add proxy info to tags
        if event.proxy_ip:
            dd_event['tags'].append(f"proxy_ip:{event.proxy_ip}")
        if event.proxy_type:
            dd_event['tags'].append(f"proxy_type:{event.proxy_type}")
        
        try:
            # Send event
            dd_api.Event.create(**dd_event)
            
            # Send metrics
            for metric_name, value in event.metrics.items():
                self._statsd.gauge(
                    f"proxy.assessment.{metric_name}",
                    value,
                    tags=dd_event['tags']
                )
            
            # Increment counter
            self._statsd.increment(
                f"proxy.assessment.events.{event.event_type}",
                tags=dd_event['tags']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event to Datadog: {e}")
            return False
    
    async def send_batch(self, events: List[SIEMEvent]) -> bool:
        """Send batch of events to Datadog"""
        # Datadog doesn't have native batch API for events
        # Send individually with metrics batched
        
        success_count = 0
        
        # Collect metrics for batch sending
        metrics_batch = []
        
        for event in events:
            # Send event
            if await self.send_event(event):
                success_count += 1
            
            # Collect metrics
            for metric_name, value in event.metrics.items():
                metrics_batch.append({
                    'metric': f"proxy.assessment.{metric_name}",
                    'points': [(event.timestamp.timestamp(), value)],
                    'tags': self.tags + event.tags
                })
        
        # Send batched metrics
        if metrics_batch:
            try:
                dd_api.Metric.send(metrics_batch)
            except Exception as e:
                logger.error(f"Failed to send metrics batch to Datadog: {e}")
        
        return success_count == len(events)
    
    def _map_severity(self, severity: EventSeverity) -> str:
        """Map severity to Datadog alert type"""
        mapping = {
            EventSeverity.CRITICAL: "error",
            EventSeverity.HIGH: "error",
            EventSeverity.MEDIUM: "warning",
            EventSeverity.LOW: "warning",
            EventSeverity.INFO: "info",
            EventSeverity.DEBUG: "info"
        }
        return mapping.get(severity, "info")


class SIEMManager:
    """Manages multiple SIEM connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, SIEMConnector] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    def add_connector(self, name: str, connector: SIEMConnector):
        """Add SIEM connector"""
        self.connectors[name] = connector
        logger.info(f"Added SIEM connector: {name}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect all SIEM connectors"""
        results = {}
        
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.connect()
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        
        return results
    
    async def disconnect_all(self):
        """Disconnect all SIEM connectors"""
        for name, connector in self.connectors.items():
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect {name}: {e}")
    
    async def start(self):
        """Start event processing"""
        self._running = True
        self._worker_task = asyncio.create_task(self._event_worker())
        logger.info("SIEM manager started")
    
    async def stop(self):
        """Stop event processing"""
        self._running = False
        
        # Flush remaining events
        await self._flush_queue()
        
        # Cancel worker
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all
        await self.disconnect_all()
        
        logger.info("SIEM manager stopped")
    
    async def send_event(self, event: SIEMEvent):
        """Queue event for sending"""
        await self._event_queue.put(event)
    
    async def _event_worker(self):
        """Background worker to process events"""
        while self._running:
            try:
                # Get event with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                # Send to all connected SIEMs
                tasks = []
                for name, connector in self.connectors.items():
                    if connector.connected:
                        tasks.append(connector.buffer_event(event))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
            except asyncio.TimeoutError:
                # Periodic flush
                await self._flush_all_buffers()
                
            except Exception as e:
                logger.error(f"Event worker error: {e}")
    
    async def _flush_queue(self):
        """Flush remaining events in queue"""
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                
                # Send directly
                tasks = []
                for connector in self.connectors.values():
                    if connector.connected:
                        tasks.append(connector.send_event(event))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
            except asyncio.QueueEmpty:
                break
    
    async def _flush_all_buffers(self):
        """Flush buffers in all connectors"""
        tasks = []
        
        for connector in self.connectors.values():
            if connector.connected:
                tasks.append(connector.flush_buffer())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def create_security_event(self,
                            title: str,
                            description: str,
                            severity: EventSeverity,
                            proxy_data: Dict[str, Any]) -> SIEMEvent:
        """Create security-focused SIEM event"""
        return SIEMEvent(
            event_type="security_alert",
            severity=severity,
            category=EventCategory.SECURITY,
            title=title,
            description=description,
            proxy_ip=proxy_data.get('ip'),
            proxy_port=proxy_data.get('port'),
            proxy_type=proxy_data.get('type'),
            metrics={
                'fraud_score': proxy_data.get('fraud_score', 0),
                'risk_level': proxy_data.get('risk_level', 0)
            },
            tags=['security', 'proxy', 'alert'],
            attributes=proxy_data
        )
    
    def create_performance_event(self,
                               title: str,
                               metrics: Dict[str, float],
                               proxy_data: Dict[str, Any]) -> SIEMEvent:
        """Create performance-focused SIEM event"""
        return SIEMEvent(
            event_type="performance_metric",
            severity=EventSeverity.INFO,
            category=EventCategory.PERFORMANCE,
            title=title,
            description=f"Performance metrics for {proxy_data.get('ip', 'unknown')}",
            proxy_ip=proxy_data.get('ip'),
            proxy_port=proxy_data.get('port'),
            proxy_type=proxy_data.get('type'),
            metrics=metrics,
            tags=['performance', 'metrics', 'proxy'],
            attributes=proxy_data
        )