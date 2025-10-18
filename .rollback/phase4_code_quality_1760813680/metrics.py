#!/usr/bin/env python3
"""
Metrics collection and reporting for Stitch Web Interface
Prometheus-compatible metrics endpoint
"""
import time
import psutil
from datetime import datetime
from collections import defaultdict
from threading import Lock
from config import Config

class MetricsCollector:
    """Collect and report application metrics"""
    
    def __init__(self):
        self.lock = Lock()
        self.start_time = time.time()
        
        # Counters
        self.total_commands = 0
        self.command_errors = 0
        self.total_logins = 0
        self.failed_logins = 0
        self.api_requests = 0
        self.websocket_messages = 0
        
        # Gauges
        self.active_connections = 0
        self.active_sessions = 0
        self.rate_limit_hits = defaultdict(int)
        
        # Histograms
        self.command_durations = []
        self.response_times = []
        
        # Rate limit tracking
        self.rate_limit_windows = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
    
    def increment_counter(self, metric_name, value=1):
        """Increment a counter metric"""
        with self.lock:
            if metric_name == 'total_commands':
                self.total_commands += value
            elif metric_name == 'command_errors':
                self.command_errors += value
            elif metric_name == 'total_logins':
                self.total_logins += value
            elif metric_name == 'failed_logins':
                self.failed_logins += value
            elif metric_name == 'api_requests':
                self.api_requests += value
            elif metric_name == 'websocket_messages':
                self.websocket_messages += value
    
    def set_gauge(self, metric_name, value):
        """Set a gauge metric"""
        with self.lock:
            if metric_name == 'active_connections':
                self.active_connections = value
            elif metric_name == 'active_sessions':
                self.active_sessions = value
    
    def record_duration(self, metric_name, duration):
        """Record a duration for histogram"""
        with self.lock:
            if metric_name == 'command_duration':
                self.command_durations.append(duration)
                # Keep only last 1000 entries
                if len(self.command_durations) > 1000:
                    self.command_durations = self.command_durations[-1000:]
            elif metric_name == 'response_time':
                self.response_times.append(duration)
                if len(self.response_times) > 1000:
                    self.response_times = self.response_times[-1000:]
    
    def track_rate_limit(self, endpoint):
        """Track rate limit hits"""
        with self.lock:
            self.rate_limit_hits[endpoint] += 1
    
    def get_uptime(self):
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_system_metrics(self):
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_bytes': memory.used,
                'memory_available_bytes': memory.available,
                'disk_percent': disk.percent,
                'disk_used_bytes': disk.used,
                'disk_free_bytes': disk.free
            }
        except Exception:
            return {}
    
    def calculate_percentiles(self, data, percentiles=[50, 95, 99]):
        """Calculate percentiles for a dataset"""
        if not data:
            return {p: 0 for p in percentiles}
        
        sorted_data = sorted(data)
        result = {}
        
        for p in percentiles:
            index = int(len(sorted_data) * p / 100)
            if index >= len(sorted_data):
                index = len(sorted_data) - 1
            result[p] = sorted_data[index]
        
        return result
    
    def generate_prometheus_metrics(self):
        """Generate metrics in Prometheus format"""
        with self.lock:
            metrics = []
            
            # Info metrics
            metrics.append(f'# HELP stitch_info Application information')
            metrics.append(f'# TYPE stitch_info gauge')
            metrics.append(f'stitch_info{{version="{Config.APP_VERSION}",name="{Config.APP_NAME}"}} 1')
            
            # Uptime
            uptime = self.get_uptime()
            metrics.append(f'# HELP stitch_uptime_seconds Application uptime in seconds')
            metrics.append(f'# TYPE stitch_uptime_seconds gauge')
            metrics.append(f'stitch_uptime_seconds {uptime:.2f}')
            
            # Counters
            metrics.append(f'# HELP stitch_commands_total Total number of commands executed')
            metrics.append(f'# TYPE stitch_commands_total counter')
            metrics.append(f'stitch_commands_total {self.total_commands}')
            
            metrics.append(f'# HELP stitch_command_errors_total Total number of command errors')
            metrics.append(f'# TYPE stitch_command_errors_total counter')
            metrics.append(f'stitch_command_errors_total {self.command_errors}')
            
            metrics.append(f'# HELP stitch_logins_total Total number of login attempts')
            metrics.append(f'# TYPE stitch_logins_total counter')
            metrics.append(f'stitch_logins_total {{status="success"}} {self.total_logins - self.failed_logins}')
            metrics.append(f'stitch_logins_total {{status="failed"}} {self.failed_logins}')
            
            metrics.append(f'# HELP stitch_api_requests_total Total number of API requests')
            metrics.append(f'# TYPE stitch_api_requests_total counter')
            metrics.append(f'stitch_api_requests_total {self.api_requests}')
            
            metrics.append(f'# HELP stitch_websocket_messages_total Total number of WebSocket messages')
            metrics.append(f'# TYPE stitch_websocket_messages_total counter')
            metrics.append(f'stitch_websocket_messages_total {self.websocket_messages}')
            
            # Gauges
            metrics.append(f'# HELP stitch_active_connections Number of active target connections')
            metrics.append(f'# TYPE stitch_active_connections gauge')
            metrics.append(f'stitch_active_connections {self.active_connections}')
            
            metrics.append(f'# HELP stitch_active_sessions Number of active user sessions')
            metrics.append(f'# TYPE stitch_active_sessions gauge')
            metrics.append(f'stitch_active_sessions {self.active_sessions}')
            
            # Rate limit hits
            if self.rate_limit_hits:
                metrics.append(f'# HELP stitch_rate_limit_hits_total Number of rate limit hits')
                metrics.append(f'# TYPE stitch_rate_limit_hits_total counter')
                for endpoint, count in self.rate_limit_hits.items():
                    metrics.append(f'stitch_rate_limit_hits_total{{endpoint="{endpoint}"}} {count}')
            
            # Command duration histogram
            if self.command_durations:
                percentiles = self.calculate_percentiles(self.command_durations)
                metrics.append(f'# HELP stitch_command_duration_seconds Command execution duration')
                metrics.append(f'# TYPE stitch_command_duration_seconds summary')
                for p, value in percentiles.items():
                    metrics.append(f'stitch_command_duration_seconds{{quantile="0.{p}"}} {value:.4f}')
                metrics.append(f'stitch_command_duration_seconds_sum {sum(self.command_durations):.4f}')
                metrics.append(f'stitch_command_duration_seconds_count {len(self.command_durations)}')
            
            # Response time histogram
            if self.response_times:
                percentiles = self.calculate_percentiles(self.response_times)
                metrics.append(f'# HELP stitch_http_response_time_seconds HTTP response time')
                metrics.append(f'# TYPE stitch_http_response_time_seconds summary')
                for p, value in percentiles.items():
                    metrics.append(f'stitch_http_response_time_seconds{{quantile="0.{p}"}} {value:.4f}')
                metrics.append(f'stitch_http_response_time_seconds_sum {sum(self.response_times):.4f}')
                metrics.append(f'stitch_http_response_time_seconds_count {len(self.response_times)}')
            
            # System metrics
            system_metrics = self.get_system_metrics()
            if system_metrics:
                metrics.append(f'# HELP stitch_system_cpu_percent System CPU usage percentage')
                metrics.append(f'# TYPE stitch_system_cpu_percent gauge')
                metrics.append(f'stitch_system_cpu_percent {system_metrics.get("cpu_percent", 0):.2f}')
                
                metrics.append(f'# HELP stitch_system_memory_percent System memory usage percentage')
                metrics.append(f'# TYPE stitch_system_memory_percent gauge')
                metrics.append(f'stitch_system_memory_percent {system_metrics.get("memory_percent", 0):.2f}')
                
                metrics.append(f'# HELP stitch_system_memory_bytes System memory usage in bytes')
                metrics.append(f'# TYPE stitch_system_memory_bytes gauge')
                metrics.append(f'stitch_system_memory_bytes{{state="used"}} {system_metrics.get("memory_used_bytes", 0)}')
                metrics.append(f'stitch_system_memory_bytes{{state="available"}} {system_metrics.get("memory_available_bytes", 0)}')
                
                metrics.append(f'# HELP stitch_system_disk_percent System disk usage percentage')
                metrics.append(f'# TYPE stitch_system_disk_percent gauge')
                metrics.append(f'stitch_system_disk_percent {system_metrics.get("disk_percent", 0):.2f}')
                
                metrics.append(f'# HELP stitch_system_disk_bytes System disk usage in bytes')
                metrics.append(f'# TYPE stitch_system_disk_bytes gauge')
                metrics.append(f'stitch_system_disk_bytes{{state="used"}} {system_metrics.get("disk_used_bytes", 0)}')
                metrics.append(f'stitch_system_disk_bytes{{state="free"}} {system_metrics.get("disk_free_bytes", 0)}')
            
            return '\n'.join(metrics)
    
    def get_json_metrics(self):
        """Get metrics in JSON format"""
        with self.lock:
            system_metrics = self.get_system_metrics()
            
            return {
                'app': {
                    'name': Config.APP_NAME,
                    'version': Config.APP_VERSION,
                    'uptime_seconds': self.get_uptime()
                },
                'counters': {
                    'total_commands': self.total_commands,
                    'command_errors': self.command_errors,
                    'successful_logins': self.total_logins - self.failed_logins,
                    'failed_logins': self.failed_logins,
                    'api_requests': self.api_requests,
                    'websocket_messages': self.websocket_messages
                },
                'gauges': {
                    'active_connections': self.active_connections,
                    'active_sessions': self.active_sessions
                },
                'rate_limits': dict(self.rate_limit_hits),
                'performance': {
                    'command_duration': {
                        'count': len(self.command_durations),
                        'percentiles': self.calculate_percentiles(self.command_durations) if self.command_durations else {}
                    },
                    'response_time': {
                        'count': len(self.response_times),
                        'percentiles': self.calculate_percentiles(self.response_times) if self.response_times else {}
                    }
                },
                'system': system_metrics
            }

# Global metrics collector instance
metrics_collector = MetricsCollector()