#!/usr/bin/env python3
"""
Webhook Notification System
Enterprise-grade webhook delivery with retries and security
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from uuid import uuid4

import httpx
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import backoff

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Webhook event types"""
    # Proxy events
    PROXY_DISCOVERED = "proxy.discovered"
    PROXY_VALIDATED = "proxy.validated"
    PROXY_FAILED = "proxy.failed"
    PROXY_ROTATING = "proxy.rotating"
    PROXY_BLACKLISTED = "proxy.blacklisted"
    
    # Quality events
    QUALITY_DEGRADED = "quality.degraded"
    QUALITY_IMPROVED = "quality.improved"
    QUALITY_THRESHOLD = "quality.threshold"
    
    # Security events
    SECURITY_LEAK_DETECTED = "security.leak_detected"
    SECURITY_SSL_INTERCEPTED = "security.ssl_intercepted"
    SECURITY_FRAUD_HIGH = "security.fraud_high"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_PERFORMANCE = "system.performance"
    SCAN_COMPLETED = "scan.completed"
    
    # ML events
    ML_PREDICTION_ANOMALY = "ml.prediction_anomaly"
    ML_PATTERN_DETECTED = "ml.pattern_detected"


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str = field(default_factory=lambda: str(uuid4()))
    url: str = ""
    name: str = ""
    events: List[WebhookEvent] = field(default_factory=list)
    secret: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    active: bool = True
    max_retries: int = 5
    timeout: int = 30
    
    # Security options
    sign_payload: bool = True
    verify_ssl: bool = True
    
    # Filtering
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    total_sent: int = 0
    total_failed: int = 0
    last_sent: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # Rate limiting
    rate_limit: int = 100  # per minute
    rate_window: timedelta = timedelta(minutes=1)


@dataclass
class WebhookPayload:
    """Webhook payload structure"""
    id: str = field(default_factory=lambda: str(uuid4()))
    event: WebhookEvent = WebhookEvent.SYSTEM_ERROR
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event': self.event.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata
        }


@dataclass
class WebhookDelivery:
    """Track webhook delivery attempts"""
    id: str = field(default_factory=lambda: str(uuid4()))
    endpoint_id: str = ""
    payload: WebhookPayload = field(default_factory=WebhookPayload)
    attempt: int = 0
    status: str = "pending"  # pending, success, failed
    response_code: Optional[int] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class WebhookManager:
    """
    Advanced webhook manager with enterprise features
    """
    
    def __init__(self, 
                 signing_key: Optional[str] = None,
                 encryption_key: Optional[bytes] = None):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.event_handlers: Dict[WebhookEvent, List[Callable]] = {}
        
        # Security
        self.signing_key = signing_key or self._generate_signing_key()
        self.encryption_key = encryption_key
        
        # Delivery queue
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        
        # Rate limiting
        self.rate_limiters: Dict[str, List[datetime]] = {}
        
        # Background tasks
        self.workers: List[asyncio.Task] = []
        self.running = False
    
    async def start(self, num_workers: int = 5):
        """Start webhook delivery workers"""
        self.running = True
        
        # Start delivery workers
        for i in range(num_workers):
            worker = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start retry worker
        retry_worker = asyncio.create_task(self._retry_worker())
        self.workers.append(retry_worker)
        
        logger.info(f"Started {num_workers} webhook delivery workers")
    
    async def stop(self):
        """Stop webhook delivery"""
        self.running = False
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("Stopped webhook delivery workers")
    
    def register_endpoint(self, endpoint: WebhookEndpoint) -> str:
        """Register a webhook endpoint"""
        if not endpoint.id:
            endpoint.id = str(uuid4())
        
        self.endpoints[endpoint.id] = endpoint
        logger.info(f"Registered webhook endpoint: {endpoint.name} ({endpoint.id})")
        
        return endpoint.id
    
    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister a webhook endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered webhook endpoint: {endpoint_id}")
            return True
        return False
    
    async def trigger_event(self, 
                          event: WebhookEvent,
                          data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Trigger webhook event for all subscribed endpoints
        """
        payload = WebhookPayload(
            event=event,
            data=data,
            metadata=metadata or {}
        )
        
        # Add system metadata
        payload.metadata.update({
            'source': 'ProxyAssessmentTool',
            'version': '2.0',
            'environment': 'production'
        })
        
        delivery_ids = []
        
        # Find matching endpoints
        for endpoint in self.endpoints.values():
            if not endpoint.active:
                continue
            
            if event in endpoint.events:
                # Apply filters
                if self._apply_filters(endpoint, payload):
                    # Check rate limit
                    if self._check_rate_limit(endpoint.id):
                        # Create delivery
                        delivery = WebhookDelivery(
                            endpoint_id=endpoint.id,
                            payload=payload
                        )
                        
                        self.deliveries[delivery.id] = delivery
                        await self.delivery_queue.put(delivery)
                        delivery_ids.append(delivery.id)
        
        # Trigger event handlers
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    await handler(payload)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
        
        return delivery_ids
    
    def on_event(self, event: WebhookEvent, handler: Callable):
        """Register event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    async def _delivery_worker(self, worker_id: str):
        """Worker to process webhook deliveries"""
        async with httpx.AsyncClient() as client:
            while self.running:
                try:
                    # Get delivery from queue
                    delivery = await asyncio.wait_for(
                        self.delivery_queue.get(),
                        timeout=1.0
                    )
                    
                    # Deliver webhook
                    await self._deliver_webhook(client, delivery)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Delivery worker {worker_id} error: {e}")
    
    async def _retry_worker(self):
        """Worker to handle retries"""
        while self.running:
            try:
                # Process retry queue
                retry_items = []
                
                while not self.retry_queue.empty():
                    item = await self.retry_queue.get()
                    retry_items.append(item)
                
                # Wait before retrying
                if retry_items:
                    await asyncio.sleep(30)  # Wait 30 seconds
                    
                    for delivery, next_attempt_time in retry_items:
                        if datetime.utcnow() >= next_attempt_time:
                            await self.delivery_queue.put(delivery)
                        else:
                            await self.retry_queue.put((delivery, next_attempt_time))
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Retry worker error: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        httpx.RequestError,
        max_tries=3,
        max_time=60
    )
    async def _deliver_webhook(self, client: httpx.AsyncClient, delivery: WebhookDelivery):
        """Deliver webhook with retries"""
        endpoint = self.endpoints.get(delivery.endpoint_id)
        if not endpoint:
            delivery.status = "failed"
            delivery.error = "Endpoint not found"
            return
        
        delivery.attempt += 1
        start_time = time.time()
        
        try:
            # Prepare payload
            payload_dict = delivery.payload.to_dict()
            payload_json = json.dumps(payload_dict)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ProxyAssessmentTool/2.0',
                'X-Webhook-ID': delivery.id,
                'X-Webhook-Event': delivery.payload.event.value,
                'X-Webhook-Timestamp': str(int(delivery.payload.timestamp.timestamp())),
                **endpoint.headers
            }
            
            # Sign payload if required
            if endpoint.sign_payload and endpoint.secret:
                signature = self._sign_payload(payload_json, endpoint.secret)
                headers['X-Webhook-Signature'] = signature
            
            # Send request
            response = await client.post(
                endpoint.url,
                content=payload_json,
                headers=headers,
                timeout=endpoint.timeout,
                follow_redirects=True
            )
            
            delivery.response_code = response.status_code
            delivery.response_time = time.time() - start_time
            
            if response.is_success:
                delivery.status = "success"
                delivery.delivered_at = datetime.utcnow()
                endpoint.total_sent += 1
                endpoint.last_sent = datetime.utcnow()
                
                logger.info(f"Webhook delivered: {endpoint.name} - {delivery.payload.event.value}")
            else:
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response
                )
            
        except Exception as e:
            delivery.error = str(e)
            endpoint.total_failed += 1
            endpoint.last_error = str(e)
            
            logger.error(f"Webhook delivery failed: {endpoint.name} - {e}")
            
            # Retry if attempts remaining
            if delivery.attempt < endpoint.max_retries:
                # Exponential backoff
                delay = min(300, 2 ** delivery.attempt * 10)  # Max 5 minutes
                retry_time = datetime.utcnow() + timedelta(seconds=delay)
                await self.retry_queue.put((delivery, retry_time))
            else:
                delivery.status = "failed"
    
    def _sign_payload(self, payload: str, secret: str) -> str:
        """
        Sign webhook payload using HMAC-SHA256
        """
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _generate_signing_key(self) -> str:
        """Generate random signing key"""
        return hashlib.sha256(str(uuid4()).encode()).hexdigest()
    
    def _apply_filters(self, endpoint: WebhookEndpoint, payload: WebhookPayload) -> bool:
        """
        Apply endpoint filters to payload
        """
        if not endpoint.filters:
            return True
        
        # Country filter
        if 'countries' in endpoint.filters:
            country = payload.data.get('country_code')
            if country and country not in endpoint.filters['countries']:
                return False
        
        # Protocol filter
        if 'protocols' in endpoint.filters:
            protocol = payload.data.get('protocol')
            if protocol and protocol not in endpoint.filters['protocols']:
                return False
        
        # Fraud score filter
        if 'min_fraud_score' in endpoint.filters:
            fraud_score = payload.data.get('fraud_score', 0)
            if fraud_score < endpoint.filters['min_fraud_score']:
                return False
        
        # Quality score filter
        if 'min_quality_score' in endpoint.filters:
            quality_score = payload.data.get('quality_score', 0)
            if quality_score < endpoint.filters['min_quality_score']:
                return False
        
        return True
    
    def _check_rate_limit(self, endpoint_id: str) -> bool:
        """Check if endpoint is within rate limit"""
        now = datetime.utcnow()
        
        if endpoint_id not in self.rate_limiters:
            self.rate_limiters[endpoint_id] = []
        
        # Remove old entries
        endpoint = self.endpoints[endpoint_id]
        cutoff = now - endpoint.rate_window
        self.rate_limiters[endpoint_id] = [
            timestamp for timestamp in self.rate_limiters[endpoint_id]
            if timestamp > cutoff
        ]
        
        # Check limit
        if len(self.rate_limiters[endpoint_id]) >= endpoint.rate_limit:
            logger.warning(f"Rate limit exceeded for endpoint: {endpoint_id}")
            return False
        
        # Add current request
        self.rate_limiters[endpoint_id].append(now)
        return True
    
    async def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status"""
        delivery = self.deliveries.get(delivery_id)
        if not delivery:
            return None
        
        return {
            'id': delivery.id,
            'endpoint_id': delivery.endpoint_id,
            'event': delivery.payload.event.value,
            'status': delivery.status,
            'attempt': delivery.attempt,
            'response_code': delivery.response_code,
            'response_time': delivery.response_time,
            'error': delivery.error,
            'created_at': delivery.created_at.isoformat(),
            'delivered_at': delivery.delivered_at.isoformat() if delivery.delivered_at else None
        }
    
    def get_endpoint_stats(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get endpoint statistics"""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return None
        
        success_rate = 0
        if endpoint.total_sent > 0:
            success_rate = (endpoint.total_sent - endpoint.total_failed) / endpoint.total_sent
        
        return {
            'id': endpoint.id,
            'name': endpoint.name,
            'url': endpoint.url,
            'active': endpoint.active,
            'total_sent': endpoint.total_sent,
            'total_failed': endpoint.total_failed,
            'success_rate': success_rate,
            'last_sent': endpoint.last_sent.isoformat() if endpoint.last_sent else None,
            'last_error': endpoint.last_error,
            'events': [e.value for e in endpoint.events]
        }