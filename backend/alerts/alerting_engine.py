#!/usr/bin/env python3
"""
Custom Alerting Engine
Complex rule-based alerting with conditions and actions
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import ast
import operator
import hashlib

try:
    from notifications.webhook_manager import WebhookManager, WebhookEvent
except ImportError:
    # Handle case where module isn't in path yet
    WebhookManager = None
    WebhookEvent = None

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ConditionOperator(str, Enum):
    """Condition operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUALS = "gte"
    LESS_THAN = "lt"
    LESS_EQUALS = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    OUTSIDE = "outside"


@dataclass
class AlertCondition:
    """Single alert condition"""
    field: str
    operator: ConditionOperator
    value: Any
    description: Optional[str] = None
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition against data"""
        field_value = self._get_nested_value(data, self.field)
        
        if field_value is None:
            return False
        
        try:
            if self.operator == ConditionOperator.EQUALS:
                return field_value == self.value
            elif self.operator == ConditionOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == ConditionOperator.GREATER_THAN:
                return float(field_value) > float(self.value)
            elif self.operator == ConditionOperator.GREATER_EQUALS:
                return float(field_value) >= float(self.value)
            elif self.operator == ConditionOperator.LESS_THAN:
                return float(field_value) < float(self.value)
            elif self.operator == ConditionOperator.LESS_EQUALS:
                return float(field_value) <= float(self.value)
            elif self.operator == ConditionOperator.CONTAINS:
                return str(self.value) in str(field_value)
            elif self.operator == ConditionOperator.NOT_CONTAINS:
                return str(self.value) not in str(field_value)
            elif self.operator == ConditionOperator.REGEX:
                return bool(re.search(str(self.value), str(field_value)))
            elif self.operator == ConditionOperator.IN:
                return field_value in self.value
            elif self.operator == ConditionOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == ConditionOperator.BETWEEN:
                return self.value[0] <= field_value <= self.value[1]
            elif self.operator == ConditionOperator.OUTSIDE:
                return field_value < self.value[0] or field_value > self.value[1]
            else:
                return False
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
    
    def _get_nested_value(self, data: Dict, field: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    conditions: List[AlertCondition]
    condition_logic: str = "AND"  # AND, OR, or custom expression
    
    # Time windows
    time_window: Optional[timedelta] = None
    occurrence_threshold: int = 1
    
    # Actions
    actions: List[str] = field(default_factory=list)
    
    # Metadata
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Rate limiting
    cooldown_period: Optional[timedelta] = None
    max_alerts_per_period: Optional[int] = None
    
    # Advanced options
    correlate_with: List[str] = field(default_factory=list)  # Other rule IDs
    suppress_if: Optional[str] = None  # Condition expression
    escalate_after: Optional[timedelta] = None
    auto_resolve_after: Optional[timedelta] = None
    
    def evaluate(self, data: Dict[str, Any], context: Optional[Dict] = None) -> bool:
        """Evaluate rule conditions"""
        if not self.enabled:
            return False
        
        # Check suppression condition
        if self.suppress_if and context:
            if self._evaluate_expression(self.suppress_if, context):
                return False
        
        # Evaluate conditions
        if self.condition_logic == "AND":
            return all(cond.evaluate(data) for cond in self.conditions)
        elif self.condition_logic == "OR":
            return any(cond.evaluate(data) for cond in self.conditions)
        else:
            # Custom logic expression
            return self._evaluate_custom_logic(data)
    
    def _evaluate_custom_logic(self, data: Dict[str, Any]) -> bool:
        """Evaluate custom condition logic"""
        # Replace condition indices with actual results
        expression = self.condition_logic
        
        for i, condition in enumerate(self.conditions):
            result = condition.evaluate(data)
            expression = expression.replace(f"C{i}", str(result))
        
        try:
            # Safely evaluate boolean expression
            return self._safe_eval(expression)
        except Exception as e:
            logger.error(f"Custom logic evaluation error: {e}")
            return False
    
    def _safe_eval(self, expression: str) -> bool:
        """Safely evaluate boolean expression"""
        # Allow only boolean operations
        allowed_names = {
            'True': True,
            'False': False,
            'and': operator.and_,
            'or': operator.or_,
            'not': operator.not_
        }
        
        code = compile(expression, '<string>', 'eval')
        
        for name in code.co_names:
            if name not in allowed_names:
                raise ValueError(f"Unsafe expression: {name}")
        
        return eval(code, {"__builtins__": {}}, allowed_names)
    
    def _evaluate_expression(self, expression: str, context: Dict) -> bool:
        """Evaluate suppression expression"""
        try:
            # Simple expression evaluation
            # Format: "field operator value"
            parts = expression.split()
            if len(parts) == 3:
                field, op, value = parts
                field_value = context.get(field)
                
                if op == '==':
                    return str(field_value) == value
                elif op == '!=':
                    return str(field_value) != value
                elif op == '>':
                    return float(field_value) > float(value)
                elif op == '<':
                    return float(field_value) < float(value)
            
            return False
        except:
            return False


@dataclass
class Alert:
    """Active alert instance"""
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    data: Dict[str, Any]
    
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    status: str = "active"  # active, acknowledged, resolved, suppressed
    
    # Deduplication
    fingerprint: str = ""
    occurrence_count: int = 1
    last_occurrence: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Actions taken
    actions_executed: List[str] = field(default_factory=list)
    
    def resolve(self, resolved_by: Optional[str] = None):
        """Resolve alert"""
        self.status = "resolved"
        self.resolved_at = datetime.utcnow()
        if resolved_by:
            self.context['resolved_by'] = resolved_by
    
    def acknowledge(self, acknowledged_by: str):
        """Acknowledge alert"""
        self.status = "acknowledged"
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = acknowledged_by
    
    def update_occurrence(self):
        """Update occurrence count"""
        self.occurrence_count += 1
        self.last_occurrence = datetime.utcnow()


class AlertAction(ABC):
    """Base class for alert actions"""
    
    @abstractmethod
    async def execute(self, alert: Alert, engine: 'AlertingEngine'):
        """Execute action for alert"""
        pass


class WebhookAction(AlertAction):
    """Send webhook notification"""
    
    def __init__(self, webhook_event: WebhookEvent):
        self.webhook_event = webhook_event
    
    async def execute(self, alert: Alert, engine: 'AlertingEngine'):
        """Send webhook"""
        if engine.webhook_manager:
            await engine.webhook_manager.trigger_event(
                self.webhook_event,
                {
                    'alert_id': alert.id,
                    'rule_name': alert.rule_name,
                    'severity': alert.severity.value,
                    'message': alert.message,
                    'data': alert.data,
                    'triggered_at': alert.triggered_at.isoformat()
                }
            )


class LogAction(AlertAction):
    """Log alert to file or service"""
    
    async def execute(self, alert: Alert, engine: 'AlertingEngine'):
        """Log alert"""
        logger.warning(
            f"ALERT [{alert.severity.value.upper()}] {alert.rule_name}: {alert.message}",
            extra={'alert': alert.__dict__}
        )


class EmailAction(AlertAction):
    """Send email notification"""
    
    def __init__(self, recipients: List[str]):
        self.recipients = recipients
    
    async def execute(self, alert: Alert, engine: 'AlertingEngine'):
        """Send email"""
        # Implementation would integrate with email service
        pass


class AlertingEngine:
    """
    Advanced alerting engine with rule evaluation and actions
    """
    
    def __init__(self, webhook_manager: Optional[WebhookManager] = None):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Actions
        self.actions: Dict[str, AlertAction] = {
            'webhook': WebhookAction(WebhookEvent.SYSTEM_ERROR),
            'log': LogAction(),
        }
        
        # Event tracking for time windows
        self.event_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Rate limiting
        self.rate_limiters: Dict[str, List[datetime]] = defaultdict(list)
        
        # Correlation tracking
        self.correlation_cache: Dict[str, List[Alert]] = defaultdict(list)
        
        # External integrations
        self.webhook_manager = webhook_manager
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start alerting engine"""
        self.running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        logger.info("Alerting engine started")
    
    async def stop(self):
        """Stop alerting engine"""
        self.running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Alerting engine stopped")
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def add_action(self, name: str, action: AlertAction):
        """Add custom action"""
        self.actions[name] = action
    
    async def evaluate_event(self, event_type: str, data: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate event against all rules
        """
        triggered_alerts = []
        
        # Track event for time windows
        self.event_windows[event_type].append({
            'timestamp': datetime.utcnow(),
            'data': data
        })
        
        # Build context for rule evaluation
        context = self._build_context(event_type)
        
        # Evaluate each rule
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this event type
            if rule.tags and event_type not in rule.tags:
                continue
            
            # Check rate limiting
            if not self._check_rate_limit(rule):
                continue
            
            # Check time window conditions
            if rule.time_window:
                if not self._check_time_window(rule, event_type):
                    continue
            
            # Evaluate rule
            if rule.evaluate(data, context):
                alert = await self._create_alert(rule, data, context)
                if alert:
                    triggered_alerts.append(alert)
        
        return triggered_alerts
    
    async def _create_alert(self, 
                          rule: AlertRule, 
                          data: Dict[str, Any],
                          context: Dict[str, Any]) -> Optional[Alert]:
        """Create and process alert"""
        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(rule, data)
        
        # Check for existing alert
        existing_alert = self._find_active_alert(fingerprint)
        
        if existing_alert:
            # Update existing alert
            existing_alert.update_occurrence()
            
            # Check if we should re-trigger actions
            if existing_alert.occurrence_count % 5 == 0:  # Every 5 occurrences
                await self._execute_actions(existing_alert, rule)
            
            return None
        
        # Create new alert
        alert = Alert(
            id=f"{rule.id}_{int(datetime.utcnow().timestamp())}",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            message=self._format_message(rule, data),
            data=data,
            fingerprint=fingerprint,
            context=context,
            tags=rule.tags
        )
        
        # Store alert
        self.alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Check correlations
        if rule.correlate_with:
            self._check_correlations(alert, rule)
        
        # Execute actions
        await self._execute_actions(alert, rule)
        
        # Schedule auto-resolution if configured
        if rule.auto_resolve_after:
            asyncio.create_task(self._auto_resolve(alert, rule.auto_resolve_after))
        
        logger.info(f"Alert triggered: {alert.rule_name} - {alert.message}")
        
        return alert
    
    def _check_time_window(self, rule: AlertRule, event_type: str) -> bool:
        """Check time window conditions"""
        if not rule.time_window:
            return True
        
        cutoff = datetime.utcnow() - rule.time_window
        events = self.event_windows[event_type]
        
        # Count matching events in window
        matching_count = sum(
            1 for event in events
            if event['timestamp'] > cutoff and 
            all(cond.evaluate(event['data']) for cond in rule.conditions)
        )
        
        return matching_count >= rule.occurrence_threshold
    
    def _check_rate_limit(self, rule: AlertRule) -> bool:
        """Check rate limiting for rule"""
        if not rule.cooldown_period:
            return True
        
        now = datetime.utcnow()
        rule_id = rule.id
        
        # Clean old entries
        cutoff = now - rule.cooldown_period
        self.rate_limiters[rule_id] = [
            timestamp for timestamp in self.rate_limiters[rule_id]
            if timestamp > cutoff
        ]
        
        # Check limit
        if rule.max_alerts_per_period:
            if len(self.rate_limiters[rule_id]) >= rule.max_alerts_per_period:
                return False
        
        # Add current alert
        self.rate_limiters[rule_id].append(now)
        return True
    
    async def _execute_actions(self, alert: Alert, rule: AlertRule):
        """Execute actions for alert"""
        for action_name in rule.actions:
            if action_name in self.actions:
                try:
                    await self.actions[action_name].execute(alert, self)
                    alert.actions_executed.append(action_name)
                except Exception as e:
                    logger.error(f"Action execution error: {action_name} - {e}")
    
    def _generate_fingerprint(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """Generate alert fingerprint for deduplication"""
        # Include rule ID and key data fields
        fingerprint_data = {
            'rule_id': rule.id,
            'severity': rule.severity.value
        }
        
        # Add key fields from data
        for condition in rule.conditions:
            field_value = self._get_nested_value(data, condition.field)
            if field_value is not None:
                fingerprint_data[condition.field] = str(field_value)
        
        # Generate hash
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
    
    def _find_active_alert(self, fingerprint: str) -> Optional[Alert]:
        """Find active alert with same fingerprint"""
        for alert in self.alerts.values():
            if alert.fingerprint == fingerprint and alert.status in ['active', 'acknowledged']:
                return alert
        return None
    
    def _format_message(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """Format alert message with data"""
        message = rule.description
        
        # Replace placeholders with actual values
        for match in re.finditer(r'\{(\w+(?:\.\w+)*)\}', message):
            field = match.group(1)
            value = self._get_nested_value(data, field)
            if value is not None:
                message = message.replace(match.group(0), str(value))
        
        return message
    
    def _get_nested_value(self, data: Dict, field: str) -> Any:
        """Get value from nested dictionary"""
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _build_context(self, event_type: str) -> Dict[str, Any]:
        """Build context for rule evaluation"""
        return {
            'event_type': event_type,
            'timestamp': datetime.utcnow(),
            'active_alerts': len([a for a in self.alerts.values() if a.status == 'active']),
            'recent_alerts': len(self.alert_history)
        }
    
    def _check_correlations(self, alert: Alert, rule: AlertRule):
        """Check for correlated alerts"""
        for correlated_rule_id in rule.correlate_with:
            # Find recent alerts from correlated rule
            correlated_alerts = [
                a for a in self.alert_history
                if a.rule_id == correlated_rule_id and
                (datetime.utcnow() - a.triggered_at) < timedelta(minutes=5)
            ]
            
            if correlated_alerts:
                alert.context['correlated_alerts'] = [a.id for a in correlated_alerts]
                self.correlation_cache[alert.id].extend(correlated_alerts)
    
    async def _auto_resolve(self, alert: Alert, after: timedelta):
        """Auto-resolve alert after specified time"""
        await asyncio.sleep(after.total_seconds())
        
        if alert.status == 'active':
            alert.resolve('auto')
            logger.info(f"Alert auto-resolved: {alert.id}")
    
    async def _cleanup_worker(self):
        """Background worker to clean up old data"""
        while self.running:
            try:
                # Clean old events
                cutoff = datetime.utcnow() - timedelta(hours=1)
                
                for event_list in self.event_windows.values():
                    while event_list and event_list[0]['timestamp'] < cutoff:
                        event_list.popleft()
                
                # Clean resolved alerts
                resolved_alerts = [
                    alert_id for alert_id, alert in self.alerts.items()
                    if alert.status == 'resolved' and 
                    (datetime.utcnow() - alert.resolved_at) > timedelta(hours=24)
                ]
                
                for alert_id in resolved_alerts:
                    del self.alerts[alert_id]
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [
            alert for alert in self.alerts.values()
            if alert.status in ['active', 'acknowledged']
        ]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alerting statistics"""
        active_alerts = self.get_active_alerts()
        
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'total_active': len(active_alerts),
            'by_severity': dict(severity_counts),
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules.values() if r.enabled),
            'recent_alerts': len(self.alert_history)
        }